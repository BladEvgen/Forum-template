import os

from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.utils.crypto import get_random_string
from django.core.validators import FileExtensionValidator

from .utils import transliterate


class PasswordResetTokenManager(models.Manager):
    def mark_as_used(self, token):
        token_obj = self.filter(token=token, _used=False).first()
        if token_obj and token_obj.is_valid():
            token_obj._used = True
            token_obj.save(update_fields=["_used"])
            return True
        return False


class PasswordResetToken(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name="Пользователь"
    )
    token = models.CharField(max_length=64, unique=True, verbose_name="Токен")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    _used = models.BooleanField(default=False, verbose_name="Статус использования")

    objects = PasswordResetTokenManager()

    @property
    def used(self):
        return self._used

    def is_valid(self):
        expiration_time = timezone.now() - timezone.timedelta(hours=1)
        return self.created_at > expiration_time and not self._used

    @staticmethod
    def generate_token(user):
        token = get_random_string(64)
        PasswordResetToken.objects.create(user=user, token=token)
        return token

    def save(self, *args, **kwargs):
        if self.pk:
            original = PasswordResetToken.objects.get(pk=self.pk)
            if original.token != self.token:
                self.token = original.token
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Токен для сброса пароля"
        verbose_name_plural = "Токены для сброса паролей"


class PasswordResetRequestLog(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name="Пользователь"
    )
    ip_address = models.GenericIPAddressField(verbose_name="IP-адрес")
    requested_at = models.DateTimeField(auto_now_add=True, verbose_name="Время запроса")

    @staticmethod
    def is_recent_request(user, ip_address):
        five_minutes_ago = timezone.now() - timezone.timedelta(minutes=5)
        return PasswordResetRequestLog.objects.filter(
            user=user, ip_address=ip_address, requested_at__gte=five_minutes_ago
        ).exists()

    @staticmethod
    def get_last_request_time(user, ip_address):
        last_request = (
            PasswordResetRequestLog.objects.filter(user=user, ip_address=ip_address)
            .order_by("-requested_at")
            .first()
        )
        return last_request.requested_at if last_request else None

    @staticmethod
    def log_request(user, ip_address):
        PasswordResetRequestLog.objects.create(user=user, ip_address=ip_address)

    @staticmethod
    def can_request_again(user, ip_address):
        last_request_time = PasswordResetRequestLog.get_last_request_time(
            user, ip_address
        )
        if not last_request_time:
            return True
        return timezone.now() >= last_request_time + timezone.timedelta(minutes=5)

    class Meta:
        verbose_name = "Лог запросов на сброс пароля"
        verbose_name_plural = "Логи запросов на сброс пароля"


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to="avatars/", null=True, blank=True)
    cover_photo = models.ImageField(upload_to="covers/", null=True, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    location = models.CharField(max_length=100, blank=True)
    birth_date = models.DateField(null=True, blank=True)

    social_links = models.JSONField(default=dict, blank=True)
    visited_places = models.JSONField(default=list, blank=True)
    followers = models.ManyToManyField(User, related_name="following", blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s profile"

    def get_followers_count(self):
        return self.followers.count()

    def get_following_count(self):
        return self.user.following.count()


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()


class Note(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    is_visible = models.BooleanField(default=True)

    location = models.CharField(max_length=255, blank=True, null=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    likes = models.ManyToManyField(User, related_name="liked_notes", blank=True)

    def get_absolute_url(self):
        return reverse("note_detail", args=[str(self.id)])

    def __str__(self):
        return self.title

    def get_likes_count(self):
        return self.likes.count()

    def get_comments_count(self):
        return self.comments.filter(is_visible=True).count()

    def get_root_comments(self):
        return self.comments.filter(parent=None, is_visible=True)


def upload_to_note(instance, filename):
    name, ext = os.path.splitext(filename)
    new_name = transliterate(name)
    return f"note_images/{new_name}{ext}"


class NoteImage(models.Model):
    note = models.ForeignKey(Note, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(
        upload_to=upload_to_note,
        validators=[
            FileExtensionValidator(allowed_extensions=["jpeg", "jpg", "png", "webp"])
        ],
    )

    def __str__(self):
        return f"Image for {self.note.title}"


class Comment(models.Model):
    note = models.ForeignKey(Note, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    content = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    is_visible = models.BooleanField(default=True)

    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="replies"
    )
    replied_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="replies_received",
    )

    likes = models.ManyToManyField(User, related_name="liked_comments", blank=True)

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["note", "parent", "is_visible"]),
            models.Index(fields=["parent", "is_visible"]),
        ]

    def __str__(self):
        return f"Comment by {self.author} on {self.note}"

    def get_likes_count(self):
        return self.likes.count()

    def get_replies_count(self):
        """Get the number of replies to this comment"""
        return self.replies.filter(is_visible=True).count()
