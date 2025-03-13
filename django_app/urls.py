from django.urls import path
from django_app import views
from django.conf import settings
from django.conf.urls.static import static

# Main pages
main_patterns = [
    path("", views.home, name="home"),
    path("search/", views.search, name="search"),
    path("search-ajax/", views.search_ajax, name="search_ajax"),
]

# Authentication & user management
auth_patterns = [
    path("register/", views.register, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path(
        "password-reset/",
        views.password_reset_request_view,
        name="password_reset_request",
    ),
    path(
        "password-reset/<str:token>/",
        views.password_reset_confirm_view,
        name="password_reset_confirm",
    ),
]

# Note patterns
note_patterns = [
    path("note/<int:note_id>/", views.note_detail, name="note_detail"),
    path("create_note/", views.create_note, name="create_note"),
    path("edit_note/<int:note_id>/", views.edit_note, name="edit_note"),
    path("delete_note/<int:note_id>/", views.delete_note, name="delete_note"),
    path("note/<int:note_id>/like/", views.toggle_like_note, name="toggle_like_note"),
    path("liked-notes/", views.liked_notes, name="liked_notes"),
]

# Comment patterns
comment_patterns = [
    path("note/<int:note_id>/add_comment/", views.add_comment, name="add_comment"),
    path("comment/<int:comment_id>/edit/", views.edit_comment, name="edit_comment"),
    path(
        "comment/<int:comment_id>/delete/", views.delete_comment, name="delete_comment"
    ),
    path(
        "comment/<int:comment_id>/like/",
        views.toggle_like_comment,
        name="toggle_like_comment",
    ),
    path("comment/<int:comment_id>/reply/", views.add_reply, name="add_reply"),
    path(
        "comment/<int:comment_id>/get_replies/",
        views.get_comment_replies,
        name="get_comment_replies",
    ),
]

# Profile & user data patterns
profile_patterns = [
    path("profile/<str:username>/", views.profile, name="profile"),
    path("edit_profile/", views.edit_profile, name="edit_profile"),
    path("profile/<str:username>/follow/", views.toggle_follow, name="toggle_follow"),
    path("profile/<str:username>/photos/", views.user_photos, name="user_photos"),
    path("profile/<str:username>/map/", views.travel_map, name="travel_map"),
    path("add-travel-location/", views.add_travel_location, name="add_travel_location"),
]

urlpatterns = (
    main_patterns + auth_patterns + note_patterns + comment_patterns + profile_patterns
)

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
