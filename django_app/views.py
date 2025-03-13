import json
import logging

from django.utils import timezone
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Prefetch, Q
from django.contrib.auth.models import User
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import get_object_or_404, redirect, render

from django_app import utils
from django_app.paginator import paginate_queryset

from .models import (
    Note,
    Comment,
    NoteImage,
    PasswordResetToken,
    PasswordResetRequestLog,
)

logger = logging.getLogger(__name__)


def password_reset_request_view(request):
    if request.method == "POST":
        identifier = request.POST.get("identifier")
        ip_address = utils.get_client_ip(request)
        logger.error(str(ip_address))
        user = (
            User.objects.filter(username=identifier).first()
            or User.objects.filter(email=identifier).first()
        )

        user_timezone = utils.get_user_timezone(request)

        if user:
            last_request_time = PasswordResetRequestLog.get_last_request_time(
                user, ip_address
            )
            if not PasswordResetRequestLog.can_request_again(user, ip_address):
                next_possible_time = timezone.localtime(
                    last_request_time + timezone.timedelta(minutes=5), user_timezone
                )
                last_request_time_local = timezone.localtime(
                    last_request_time, user_timezone
                )
                messages.warning(
                    request,
                    f"Запрос уже был отправлен. Повторный запрос возможен в {next_possible_time.strftime('%H:%M:%S %Z')} ({next_possible_time.tzinfo}). Последний запрос был в {last_request_time_local.strftime('%H:%M:%S %Z')} ({last_request_time_local.tzinfo}).",
                )
            else:
                utils.send_password_reset_email(user, request)
                PasswordResetRequestLog.log_request(user, ip_address)
                current_time_local = timezone.localtime(timezone.now(), user_timezone)
                messages.success(
                    request,
                    f"Если пользователь существует, ссылка для сброса пароля была отправлена на его электронную почту. Последний запрос был в {current_time_local.strftime('%H:%M:%S %Z')} ({current_time_local.tzinfo}).",
                )
        else:
            messages.info(
                request,
                "Если пользователь существует, ссылка для сброса пароля была отправлена на его электронную почту.",
            )

        return redirect("password_reset_request")

    return render(request, "password_reset_request.html")


def password_reset_confirm_view(request, token):
    reset_token = get_object_or_404(PasswordResetToken, token=token)

    if not reset_token.is_valid():
        messages.error(request, "Этот токен для сброса пароля больше не действителен.")
        return redirect("password_reset_request")

    if request.method == "POST":
        new_password = request.POST.get("password")
        user = reset_token.user
        user.set_password(new_password)
        user.save()

        if PasswordResetToken.objects.mark_as_used(token):
            messages.success(
                request,
                "Пароль успешно сброшен. Вы можете войти в систему с новым паролем.",
            )
            return redirect("login")
        else:
            messages.error(request, "Ошибка при обновлении токена. Попробуйте снова.")
            return redirect("password_reset_confirm", token=token)

    return render(request, "password_reset_confirm.html", {"token": token})


def home(request):
    notes = (
        Note.objects.filter(is_visible=True)
        .select_related("author")
        .prefetch_related("images", "likes")
        .order_by("-created_at")
    )

    paginated_notes = paginate_queryset(request, notes, per_page=5)
    return render(request, "home.html", {"notes": paginated_notes})


def note_detail(request, note_id):
    note = get_object_or_404(
        Note.objects.select_related("author", "author__profile").prefetch_related(
            "images",
            Prefetch(
                "comments",
                queryset=Comment.objects.filter(is_visible=True, parent=None)
                .select_related("author", "author__profile")
                .prefetch_related(
                    Prefetch(
                        "replies",
                        queryset=Comment.objects.filter(is_visible=True)
                        .select_related("author", "author__profile", "replied_to")
                        .prefetch_related("likes"),
                    ),
                    "likes",
                ),
            ),
        ),
        id=note_id,
        is_visible=True,
    )

    comments = note.comments.filter(parent=None, is_visible=True).order_by(
        "-created_at"
    )

    user_likes_note = (
        request.user.is_authenticated and note.likes.filter(id=request.user.id).exists()
    )

    related_notes = (
        Note.objects.filter(Q(author=note.author) & ~Q(id=note.id) & Q(is_visible=True))
        .prefetch_related("images")
        .order_by("-created_at")[:4]
    )

    return render(
        request,
        "note_detail.html",
        {
            "note": note,
            "comments": comments,
            "user_likes_note": user_likes_note,
            "related_notes": related_notes,
        },
    )


@login_required
@require_POST
def add_reply(request, comment_id):
    parent_comment = get_object_or_404(
        Comment.objects.select_related("note"), id=comment_id, is_visible=True
    )

    content = request.POST.get("content")
    replied_to_id = request.POST.get("replied_to_id")

    if not content:
        return JsonResponse({"error": "Reply content is required."}, status=400)

    try:
        reply = Comment.objects.create(
            note=parent_comment.note,
            content=content,
            author=request.user,
            parent=parent_comment,
        )

        if replied_to_id:
            try:
                replied_to_user = User.objects.get(id=replied_to_id)
                reply.replied_to = replied_to_user
                reply.save()
            except User.DoesNotExist:
                logger.warning(f"User with ID {replied_to_id} does not exist")
        else:
            reply.replied_to = parent_comment.author
            reply.save()

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse(
                {
                    "status": "success",
                    "comment_id": reply.id,
                    "parent_id": parent_comment.id,
                    "author": reply.author.username,
                    "author_id": reply.author.id,
                    "author_avatar": (
                        reply.author.profile.avatar.url
                        if hasattr(reply.author, "profile")
                        and reply.author.profile.avatar
                        else None
                    ),
                    "replied_to": (
                        reply.replied_to.username if reply.replied_to else None
                    ),
                    "content": reply.content,
                    "created_at": reply.created_at.strftime("%d %b %Y, %H:%M"),
                    "likes_count": 0,
                }
            )

        return redirect(parent_comment.note.get_absolute_url())

    except Exception as e:
        logger.error(f"Error adding reply: {str(e)}")
        return JsonResponse({"error": f"Error adding reply: {str(e)}"}, status=500)


@login_required
def create_note(request):
    if request.method == "POST":
        title = request.POST.get("title")
        content = request.POST.get("content")
        location = request.POST.get("location", "")
        latitude = request.POST.get("latitude")
        longitude = request.POST.get("longitude")

        if not title or not content:
            messages.error(request, "Title and content are required.")
            return redirect("create_note")

        try:
            note = Note.objects.create(
                title=title,
                content=content,
                author=request.user,
                location=location,
                latitude=float(latitude) if latitude else None,
                longitude=float(longitude) if longitude else None,
            )

            images = request.FILES.getlist("images")

            logger.debug(f"Number of images received: {len(images)}")

            for i, image in enumerate(images):
                logger.debug(
                    f"Processing image {i + 1}: {image.name}, size: {image.size}"
                )
                try:
                    NoteImage.objects.create(note=note, image=image)
                except Exception as e:
                    logger.error(f"Error saving image {i + 1}: {str(e)}")
                    messages.warning(
                        request, f"Image '{image.name}' couldn't be uploaded: {str(e)}"
                    )

            messages.success(request, "Note created successfully!")
            return redirect(note.get_absolute_url())
        except Exception as e:
            logger.error(f"Error creating note: {str(e)}")
            messages.error(request, f"Error creating note: {str(e)}")
            return redirect("create_note")

    return render(request, "create_note.html")


@login_required
def edit_note(request, note_id):
    note = get_object_or_404(Note.objects.prefetch_related("images"), id=note_id)

    if note.author != request.user:
        messages.error(request, "You are not allowed to edit this note.")
        return redirect(note.get_absolute_url())

    if request.method == "POST":
        title = request.POST.get("title")
        content = request.POST.get("content")
        location = request.POST.get("location", "")
        latitude = request.POST.get("latitude")
        longitude = request.POST.get("longitude")

        if not title or not content:
            messages.error(request, "Title and content are required.")
            return redirect("edit_note", note_id=note_id)

        try:
            note.title = title
            note.content = content
            note.location = location
            note.latitude = float(latitude) if latitude else None
            note.longitude = float(longitude) if longitude else None
            note.save()

            images = request.FILES.getlist("images")
            for image in images:
                NoteImage.objects.create(note=note, image=image)

            image_ids_to_delete = request.POST.getlist("delete_images")
            if image_ids_to_delete:
                NoteImage.objects.filter(id__in=image_ids_to_delete, note=note).delete()

            messages.success(request, "Note updated successfully!")
            return redirect(note.get_absolute_url())
        except Exception as e:
            logger.error(f"Error updating note: {str(e)}")
            messages.error(request, f"Error updating note: {str(e)}")
            return redirect("edit_note", note_id=note_id)

    return render(request, "edit_note.html", {"note": note})


@login_required
def delete_note(request, note_id):
    note = get_object_or_404(Note, id=note_id)

    if note.author != request.user:
        messages.error(request, "You are not allowed to delete this note.")
        return redirect(note.get_absolute_url())

    if request.method == "POST":
        note.is_visible = False
        note.save()
        messages.success(request, "Note has been hidden.")
        return redirect("home")

    return render(request, "delete_note.html", {"note": note})


@login_required
def add_comment(request, note_id):
    note = get_object_or_404(Note, id=note_id, is_visible=True)

    if request.method == "POST":
        content = request.POST.get("content")
        if not content:
            messages.error(request, "Comment content is required.")
            return redirect(note.get_absolute_url())

        try:
            Comment.objects.create(note=note, content=content, author=request.user)
            messages.success(request, "Comment added successfully!")
        except Exception as e:
            logger.error(f"Error adding comment: {str(e)}")
            messages.error(request, f"Error adding comment: {str(e)}")

        return redirect(note.get_absolute_url())

    return render(request, "add_comment.html", {"note": note})


@login_required
def edit_comment(request, comment_id):
    comment = get_object_or_404(Comment.objects.select_related("note"), id=comment_id)

    if comment.author != request.user:
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse(
                {"error": "You are not allowed to edit this comment."}, status=403
            )

        messages.error(request, "You are not allowed to edit this comment.")
        return redirect(comment.note.get_absolute_url())

    if request.method == "POST":
        content = request.POST.get("content")
        if not content:
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse(
                    {"error": "Comment content is required."}, status=400
                )

            messages.error(request, "Comment content is required.")
            return redirect("edit_comment", comment_id=comment_id)

        try:
            comment.content = content
            comment.save()

            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse(
                    {
                        "status": "success",
                        "message": "Comment updated successfully!",
                        "content": content,
                    }
                )

            messages.success(request, "Comment updated successfully!")
        except Exception as e:
            logger.error(f"Error updating comment: {str(e)}")

            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse(
                    {"error": f"Error updating comment: {str(e)}"}, status=500
                )

            messages.error(request, f"Error updating comment: {str(e)}")

        return redirect(comment.note.get_absolute_url())

    return render(request, "edit_comment.html", {"comment": comment})


@login_required
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment.objects.select_related("note"), id=comment_id)

    if comment.author != request.user:
        messages.error(request, "You are not allowed to delete this comment.")
        return redirect(comment.note.get_absolute_url())

    if request.method == "POST":
        comment.is_visible = False
        comment.save()
        messages.success(request, "Comment has been hidden.")
        return redirect(comment.note.get_absolute_url())

    return render(request, "delete_comment.html", {"comment": comment})


@login_required
@require_POST
def toggle_like_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id, is_visible=True)
    user = request.user

    try:
        if comment.likes.filter(id=user.id).exists():
            comment.likes.remove(user)
            liked = False
        else:
            comment.likes.add(user)
            liked = True

        return JsonResponse({"liked": liked, "likes_count": comment.get_likes_count()})
    except Exception as e:
        logger.error(f"Error toggling comment like: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)


@login_required
@require_POST
def get_comment_replies(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id, is_visible=True)

    try:
        replies = (
            Comment.objects.filter(parent=comment, is_visible=True)
            .select_related("author", "author__profile", "replied_to")
            .prefetch_related("likes")
            .order_by("created_at")
        )

        replies_data = []
        for reply in replies:
            user_likes_reply = request.user in reply.likes.all()

            replies_data.append(
                {
                    "id": reply.id,
                    "author": reply.author.username,
                    "author_id": reply.author.id,
                    "author_avatar": (
                        reply.author.profile.avatar.url
                        if hasattr(reply.author, "profile")
                        and reply.author.profile.avatar
                        else None
                    ),
                    "content": reply.content,
                    "created_at": reply.created_at.strftime("%d %b %Y, %H:%M"),
                    "likes_count": reply.get_likes_count(),
                    "user_likes": user_likes_reply,
                    "replies_count": reply.get_replies_count(),
                    "replied_to": (
                        reply.replied_to.username if reply.replied_to else None
                    ),
                    "can_edit": request.user == reply.author,
                    "can_delete": request.user == reply.author,
                }
            )

        return JsonResponse(
            {"status": "success", "parent_id": comment.id, "replies": replies_data}
        )

    except Exception as e:
        logger.error(f"Error getting comment replies: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)


def register(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email", "")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        if password != confirm_password:
            return render(
                request, "register.html", {"error": "Passwords do not match."}
            )

        if User.objects.filter(username=username).exists():
            return render(
                request, "register.html", {"error": "Username already exists."}
            )

        try:
            user = User.objects.create_user(
                username=username, email=email, password=password
            )
            login(request, user)
            messages.success(request, "Account created successfully!")
            return redirect("profile", username=username)
        except Exception as e:
            logger.error(f"Error registering user: {str(e)}")
            return render(
                request, "register.html", {"error": f"Error creating account: {str(e)}"}
            )

    return render(request, "register.html")


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            next_url = request.GET.get("next", "home")
            messages.success(request, f"Welcome back, {username}!")
            return redirect(next_url)
        else:
            messages.error(request, "Invalid credentials.")

    return render(request, "login.html")


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("home")


def profile(request, username):
    user_profile = get_object_or_404(
        User.objects.select_related("profile").prefetch_related("profile__followers"),
        username=username,
    )

    notes_qs = (
        Note.objects.filter(author=user_profile, is_visible=True)
        .select_related("author")
        .prefetch_related("images", "likes", "comments")
        .order_by("-created_at")
    )

    paginated_notes = paginate_queryset(request, notes_qs, per_page=6)
    is_owner = request.user == user_profile

    is_following = False
    if request.user.is_authenticated:
        is_following = user_profile.profile.followers.filter(
            id=request.user.id
        ).exists()

    if request.GET.get("page"):
        return render(request, "partials/notes_feed.html", {"notes": paginated_notes})

    photo_count = NoteImage.objects.filter(
        note__author=user_profile, note__is_visible=True
    ).count()

    travel_locations = []
    if user_profile.profile.visited_places:
        travel_locations = user_profile.profile.visited_places

    user_likes_data = []
    user_likes_count = 0
    if request.user.is_authenticated:
        user_likes_data = (
            Note.objects.filter(likes=user_profile, is_visible=True)
            .select_related("author", "author__profile")
            .prefetch_related("images", "comments", "likes")
            .order_by("-created_at")[:10]
        )
        user_likes_count = Note.objects.filter(
            likes=user_profile, is_visible=True
        ).count()

    received_likes_data = []
    received_likes_count = 0
    if user_profile.note_set.exists():
        notes_with_likes = (
            Note.objects.filter(author=user_profile, is_visible=True)
            .prefetch_related("likes", "likes__profile")
            .order_by("-created_at")
        )

        received_likes_data = [
            (note, list(note.likes.all()))
            for note in notes_with_likes
            if note.likes.exists()
        ][:10]

        received_likes_count = sum(len(likes) for _, likes in received_likes_data)

    return render(
        request,
        "profile.html",
        {
            "user_profile": user_profile,
            "notes": paginated_notes,
            "is_owner": is_owner,
            "is_following": is_following,
            "photo_count": photo_count,
            "travel_locations": travel_locations,
            "followers_count": user_profile.profile.get_followers_count(),
            "following_count": user_profile.profile.get_following_count(),
            "user_likes_data": user_likes_data,
            "user_likes_count": user_likes_count,
            "received_likes_data": received_likes_data,
            "received_likes_count": received_likes_count,
        },
    )


@login_required
def edit_profile(request):
    user = request.user
    profile = user.profile

    if request.method == "POST":
        try:
            user.first_name = request.POST.get("first_name", "")
            user.last_name = request.POST.get("last_name", "")
            user.email = request.POST.get("email", "")
            user.save()

            profile.bio = request.POST.get("bio", "")
            profile.location = request.POST.get("location", "")

            birth_date = request.POST.get("birth_date")
            if birth_date:
                profile.birth_date = parse_date(birth_date)

            if "avatar" in request.FILES:
                profile.avatar = request.FILES["avatar"]

            if request.POST.get("remove_avatar") == "true":
                profile.avatar = None

            if "cover_photo" in request.FILES:
                profile.cover_photo = request.FILES["cover_photo"]

            if request.POST.get("remove_cover_photo") == "true":
                profile.cover_photo = None

            social_links = {}
            for platform in ["twitter", "facebook", "instagram", "linkedin", "github"]:
                url = request.POST.get(f"social_{platform}")
                if url:
                    social_links[platform] = url

            profile.social_links = social_links

            if request.POST.get("visited_places"):
                try:
                    visited_places = json.loads(request.POST.get("visited_places"))
                    profile.visited_places = visited_places
                except json.JSONDecodeError:
                    logger.warning("Invalid JSON for visited_places")

            profile.save()
            messages.success(request, "Profile updated successfully.")
            return redirect("profile", username=user.username)
        except Exception as e:
            logger.error(f"Error updating profile: {str(e)}")
            messages.error(request, f"Error updating profile: {str(e)}")

    social_links = profile.social_links or {}

    return render(
        request,
        "edit_profile.html",
        {
            "user": user,
            "profile": profile,
            "social_links": social_links,
        },
    )


@login_required
@require_POST
def toggle_like_note(request, note_id):
    note = get_object_or_404(Note, id=note_id, is_visible=True)
    user = request.user

    try:
        if note.likes.filter(id=user.id).exists():
            note.likes.remove(user)
            liked = False
        else:
            note.likes.add(user)
            liked = True

        return JsonResponse({"liked": liked, "likes_count": note.get_likes_count()})
    except Exception as e:
        logger.error(f"Error toggling note like: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)


@login_required
@require_POST
def toggle_follow(request, username):
    target_user = get_object_or_404(User, username=username)
    user = request.user

    if target_user == user:
        return JsonResponse({"error": "You cannot follow yourself"}, status=400)

    try:
        if target_user.profile.followers.filter(id=user.id).exists():
            target_user.profile.followers.remove(user)
            is_following = False
        else:
            target_user.profile.followers.add(user)
            is_following = True

        return JsonResponse(
            {
                "is_following": is_following,
                "followers_count": target_user.profile.get_followers_count(),
            }
        )
    except Exception as e:
        logger.error(f"Error toggling follow: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)


@login_required
def user_photos(request, username):
    user_profile = get_object_or_404(User, username=username)

    images = NoteImage.objects.filter(
        note__author=user_profile, note__is_visible=True
    ).select_related("note")

    paginated_images = paginate_queryset(request, images, per_page=12)

    return render(
        request,
        "user_photos.html",
        {
            "user_profile": user_profile,
            "images": paginated_images,
            "is_owner": request.user == user_profile,
        },
    )


@login_required
def liked_notes(request):
    liked_notes = (
        Note.objects.filter(likes=request.user, is_visible=True)
        .select_related("author")
        .prefetch_related("images")
        .order_by("-created_at")
    )

    paginated_notes = paginate_queryset(request, liked_notes, per_page=6)

    return render(request, "liked_notes.html", {"notes": paginated_notes})


@login_required
def travel_map(request, username):
    user_profile = get_object_or_404(
        User.objects.select_related("profile"), username=username
    )
    is_owner = request.user == user_profile

    note_locations = Note.objects.filter(
        author=user_profile,
        is_visible=True,
        latitude__isnull=False,
        longitude__isnull=False,
    ).values("id", "title", "location", "latitude", "longitude")

    travel_data = {
        "profile_places": user_profile.profile.visited_places or [],
        "note_locations": list(note_locations),
    }

    return render(
        request,
        "travel_map.html",
        {
            "user_profile": user_profile,
            "travel_data": travel_data,
            "is_owner": is_owner,
        },
    )


@login_required
def add_travel_location(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            place_name = data.get("place_name")
            latitude = data.get("latitude")
            longitude = data.get("longitude")
            visit_date = data.get("visit_date")

            if not all([place_name, latitude, longitude]):
                return JsonResponse({"error": "Missing required fields"}, status=400)

            profile = request.user.profile
            visited_places = list(profile.visited_places or [])

            new_place = {
                "name": place_name,
                "lat": float(latitude),
                "lng": float(longitude),
                "date": visit_date,
            }

            visited_places.append(new_place)
            profile.visited_places = visited_places
            profile.save()

            return JsonResponse({"success": True, "place": new_place})

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        except Exception as e:
            logger.error(f"Error adding travel location: {str(e)}")
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Method not allowed"}, status=405)


@login_required
def search(request):
    query = request.GET.get("q", "").strip()

    if not query:
        return render(request, "search.html", {"query": query})

    notes = (
        Note.objects.filter(
            Q(title__icontains=query)
            | Q(content__icontains=query)
            | Q(location__icontains=query),
            is_visible=True,
        )
        .select_related("author")
        .prefetch_related("images")
        .order_by("-created_at")
    )

    users = User.objects.filter(
        Q(username__icontains=query)
        | Q(first_name__icontains=query)
        | Q(last_name__icontains=query)
    ).select_related("profile")

    return render(
        request,
        "search.html",
        {
            "query": query,
            "notes": notes[:10],
            "users": users[:10],
            "notes_count": notes.count(),
            "users_count": users.count(),
        },
    )


def search_ajax(request):
    query = request.GET.get("q", "").strip()

    if not query:
        return JsonResponse(
            {"notes": [], "users": [], "notes_count": 0, "users_count": 0}
        )

    notes = (
        Note.objects.filter(
            Q(title__icontains=query)
            | Q(content__icontains=query)
            | Q(location__icontains=query),
            is_visible=True,
        )
        .select_related("author")
        .prefetch_related("images")
        .order_by("-created_at")
    )[:10]

    users = User.objects.filter(
        Q(username__icontains=query)
        | Q(first_name__icontains=query)
        | Q(last_name__icontains=query)
    ).select_related("profile")[:10]

    notes_data = []
    for note in notes:
        note_data = {
            "id": note.id,
            "title": note.title,
            "content": note.content,
            "created_at": note.created_at.isoformat(),
            "location": note.location,
            "author": {
                "id": note.author.id,
                "username": note.author.username,
            },
            "images": [],
        }

        for image in note.images.all():
            note_data["images"].append({"id": image.id, "image": image.image.url})

        notes_data.append(note_data)

    users_data = []
    for user in users:
        user_data = {
            "id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "profile": {
                "avatar": user.profile.avatar.url if user.profile.avatar else None
            },
        }
        users_data.append(user_data)

    return JsonResponse(
        {
            "notes": notes_data,
            "users": users_data,
            "notes_count": notes.count(),
            "users_count": users.count(),
        }
    )
