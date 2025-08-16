import os
import uuid
from django.db import models
from django.utils import timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from django.utils.timezone import is_aware
from enum import IntEnum
from integrations.models import IntegrationsModel, Platform
from django.utils.translation import gettext_lazy as _
from django.db.models import Q


class PrivacyLevelOptions(models.TextChoices):
    FOLLOWER_OF_CREATOR = "FOLLOWER_OF_CREATOR", _("Followers of Creator")
    PUBLIC_TO_EVERYONE = "PUBLIC_TO_EVERYONE", _("Public to Everyone")
    MUTUAL_FOLLOW_FRIENDS = "MUTUAL_FOLLOW_FRIENDS", _("Mutual Follow Friends")
    SELF_ONLY = "SELF_ONLY", _("Self Only")


class TextMaxLength(IntEnum):
    X_FREE = 280
    X_BLUE = 4000
    INSTAGRAM = 2200
    FACEBOOK = 63206
    LINKEDIN = 3000


class MediaFileTypes(models.TextChoices):
    VIDEO = "VIDEO", _("video")
    IMAGE = "IMAGE", _("image")


def get_filename(instance, filename):
    ext = os.path.splitext(filename)[1].lower()
    return f"{instance.account_id}/{uuid.uuid4().hex}{ext}"


class PostModel(models.Model):
    scheduled_on = models.DateTimeField()
    post_timezone = models.CharField(max_length=100)
    created_at = models.DateTimeField(default=timezone.now, null=True, blank=True)

    account_id = models.IntegerField()
    description = models.TextField(max_length=63206)
    media_file = models.FileField(
        max_length=100_000,
        upload_to=get_filename,
        null=True,
        blank=True,
    )
    media_file_type = models.CharField(
        max_length=50, blank=True, null=True, choices=MediaFileTypes
    )

    process_image = models.BooleanField(blank=True, null=True, default=True)
    process_video = models.BooleanField(blank=True, null=True, default=True)
    image_processed = models.BooleanField(blank=True, null=True, default=False)
    video_processed = models.BooleanField(blank=True, null=True, default=False)

    post_on_x = models.BooleanField(blank=True, null=True, default=False)
    post_on_instagram = models.BooleanField(blank=True, null=True, default=False)
    post_on_facebook = models.BooleanField(blank=True, null=True, default=False)
    post_on_linkedin = models.BooleanField(blank=True, null=True, default=False)
    post_on_tiktok = models.BooleanField(blank=True, null=True, default=False)

    link_x = models.CharField(max_length=50000, blank=True, null=True)
    link_instagram = models.CharField(max_length=50000, blank=True, null=True)
    link_facebook = models.CharField(max_length=50000, blank=True, null=True)
    link_linkedin = models.CharField(max_length=50000, blank=True, null=True)
    link_tiktok = models.CharField(max_length=50000, blank=True, null=True)

    error_x = models.CharField(max_length=50000, blank=True, null=True)
    error_instagram = models.CharField(max_length=50000, blank=True, null=True)
    error_facebook = models.CharField(max_length=50000, blank=True, null=True)
    error_linkedin = models.CharField(max_length=50000, blank=True, null=True)
    error_tiktok = models.CharField(max_length=50000, blank=True, null=True)

    retries_x = models.IntegerField(blank=True, null=True, default=0)
    retries_instagram = models.IntegerField(blank=True, null=True, default=0)
    retries_facebook = models.IntegerField(blank=True, null=True, default=0)
    retries_linkedin = models.IntegerField(blank=True, null=True, default=0)
    retries_tiktok = models.IntegerField(blank=True, null=True, default=0)

    # TIKTOK
    tiktok_nickname = models.CharField(max_length=1000, blank=True, default=None)
    tiktok_max_video_post_duration_sec = models.IntegerField(blank=True, default=None)
    tiktok_privacy_level_options = models.CharField(
        max_length=1000, choices=PrivacyLevelOptions, blank=True, default=None
    )
    tiktok_allow_comment = models.BooleanField(blank=True, default=None)
    tiktok_allow_duet = models.BooleanField(blank=True, default=None)
    tiktok_allow_stitch = models.BooleanField(blank=True, default=None)
    tiktok_disclose_video_content = models.BooleanField(blank=True, default=None)
    tiktok_your_brand = models.BooleanField(blank=True, default=None)
    tiktok_branded_content = models.BooleanField(blank=True, default=None)
    tiktok_ai_generated = models.BooleanField(blank=True, default=None)

    @property
    def has_video(self):
        return self.media_file_type == MediaFileTypes.VIDEO.value

    @property
    def has_image(self):
        return self.media_file_type == MediaFileTypes.IMAGE.value

    def raise_error_if_2_posts_limit_reached(self):

        platform_fields = {
            "instagram": ("post_on_instagram", "link_instagram"),
            "facebook": ("post_on_facebook", "link_facebook"),
            "linkedin": ("post_on_linkedin", "link_linkedin"),
            "tiktok": ("post_on_tiktok", "link_tiktok"),
            "x": ("post_on_x", "link_x"),
        }

        scheduled_date = self.scheduled_on.date()

        for platform, (post_flag, link_field) in platform_fields.items():
            if getattr(self, post_flag):  # only check selected platforms
                q_filter = Q(
                    **{
                        post_flag: True,
                        f"{link_field}__isnull": True,
                    }
                )

                qs = PostModel.objects.filter(
                    account_id=self.account_id,
                    scheduled_on__date=scheduled_date,
                ).filter(q_filter)

                if self.pk:
                    qs = qs.exclude(pk=self.pk)

                if qs.count() >= 2:
                    raise Exception(
                        f"Limit of 2 posts per day reached on {platform.capitalize()}!"
                    )

    def save(self, *args, **kwargs):

        skip_validation = kwargs.pop("skip_validation", False)

        if skip_validation:
            super().save(*args, **kwargs)
            return

        if not any(
            [
                self.post_on_x,
                self.post_on_instagram,
                self.post_on_facebook,
                self.post_on_linkedin,
                self.post_on_tiktok,
            ]
        ):
            raise ValueError("At least one platform must be selected for posting.")

        if not is_aware(self.scheduled_on):
            raise ValueError("The scheduled_on field must be timezone-aware.")

        try:
            ZoneInfo(self.post_timezone)
        except ZoneInfoNotFoundError:
            raise ValueError(f"Invalid timezone: {self.post_timezone}")

        self.raise_error_if_2_posts_limit_reached()

        if self.media_file:
            ext = os.path.splitext(self.media_file.name)[1].lower()
            if ext == ".mp4":
                self.media_file_type = MediaFileTypes.VIDEO.value
            elif ext in [".jpeg", ".jpg", ".png"]:
                self.media_file_type = MediaFileTypes.IMAGE.value
            else:
                raise ValueError(
                    "Unsupported file type. Only JPEG, PNG images and MP4 videos are allowed."
                )

        postlen = len(self.description)

        if self.post_on_x:
            x_ok = IntegrationsModel.objects.filter(
                account_id=self.account_id, platform=Platform.X_TWITTER.value
            ).first()
            if not x_ok:
                raise ValueError("Please got to Integrations and authorize X app")
            if postlen > TextMaxLength.X_BLUE:
                raise ValueError(
                    f"Maximum length of a X post is {TextMaxLength.X_BLUE}"
                )
            if self.media_file:
                ext = os.path.splitext(self.media_file.name)[1].lower()
                if ext not in [".jpeg", ".jpg", ".png"]:
                    raise ValueError(
                        "Unsupported file type. Only JPEG, PNG images can be uploaded to X."
                    )

        if self.post_on_instagram:
            ig_ok = IntegrationsModel.objects.filter(
                account_id=self.account_id, platform=Platform.INSTAGRAM.value
            ).first()
            if not ig_ok:
                raise ValueError(
                    "Please got to Integrations and authorize Facebook/Instagram app"
                )
            if postlen > TextMaxLength.INSTAGRAM:
                raise ValueError(
                    f"Maximum length of a Instagram post is {TextMaxLength.INSTAGRAM}"
                )
            if not self.media_file and not self.process_image:
                raise ValueError("An image or a video is required for Instagram.")
            if not self.media_file and self.process_image:
                self.media_file_type = MediaFileTypes.IMAGE.value

        if self.post_on_facebook:
            fb_ok = IntegrationsModel.objects.filter(
                account_id=self.account_id, platform=Platform.FACEBOOK.value
            ).first()
            if not fb_ok:
                raise ValueError(
                    "Please got to Integrations and authorize Facebook/Instagram app"
                )
            if postlen > TextMaxLength.FACEBOOK:
                raise ValueError(
                    f"Maximum length of a Facebook post is {TextMaxLength.FACEBOOK}"
                )

        if self.post_on_linkedin:
            ld_ok = IntegrationsModel.objects.filter(
                account_id=self.account_id, platform=Platform.LINKEDIN.value
            ).first()
            if not ld_ok:
                raise ValueError(
                    "Please got to Integrations and authorize LinkedIn app"
                )
            if postlen > TextMaxLength.LINKEDIN:
                raise ValueError(
                    f"Maximum length of a LinkedIn post is {TextMaxLength.LINKEDIN}"
                )
            if self.media_file:
                ext = os.path.splitext(self.media_file.name)[1].lower()
                if ext not in [".jpeg", ".jpg", ".png"]:
                    raise ValueError(
                        "Unsupported file type. Only JPEG, PNG images can be uploaded to LinkedIn."
                    )

        if self.post_on_tiktok:
            tk_ok = IntegrationsModel.objects.filter(
                account_id=self.account_id, platform=Platform.TIKTOK.value
            ).first()
            if not tk_ok:
                raise ValueError("Please got to Integrations and authorize TikTok app")

            if self.media_file:
                ext = os.path.splitext(self.media_file.name)[1].lower()
                if ext != ".mp4":
                    raise ValueError(
                        "Unsupported file type. Only .mp4 videos can be uploaded to TikTok."
                    )
            else:
                raise ValueError("A .mp4 video in reel format is needed for TikTok.")

        super().save(*args, **kwargs)

    class Meta:
        app_label = "socialsched"
        verbose_name_plural = "scheduled"

    def __str__(self):
        return f"AccountId:{self.account_id} PostId: {self.pk} PostScheduledOn: {self.scheduled_on}"
