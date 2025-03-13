from django.contrib import admin
from .models import Profile, Note, NoteImage, Comment


class NoteImageInline(admin.TabularInline):
    model = NoteImage
    extra = 1


class CommentInline(admin.TabularInline):
    model = Comment
    extra = 1


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "author",
        "created_at",
        "updated_at",
        "is_visible",
        "get_likes_count",
        "get_comments_count",
    )
    list_filter = ("is_visible", "created_at", "author", "location")
    search_fields = ("title", "content", "location")
    inlines = [NoteImageInline, CommentInline]
    ordering = ("-created_at",)


@admin.register(NoteImage)
class NoteImageAdmin(admin.ModelAdmin):
    list_display = ("note", "image")
    list_filter = ("note",)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("note", "author", "created_at", "is_visible", "get_likes_count")
    list_filter = ("is_visible", "created_at", "author")
    search_fields = ("content",)
    ordering = ("-created_at",)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "location",
        "birth_date",
        "get_followers_count",
        "created_at",
        "updated_at",
    )
    search_fields = ("user__username", "location", "bio")
    readonly_fields = ("created_at", "updated_at")
