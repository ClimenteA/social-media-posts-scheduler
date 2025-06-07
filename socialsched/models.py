import os
import uuid
from django.db import models
from django.utils import timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from django.utils.timezone import is_aware
from enum import IntEnum
from integrations.models import IntegrationsModel, Platform


class TextMaxLength(IntEnum):
    X_FREE = 280
    X_BLUE = 4000
    INSTAGRAM = 2200
    FACEBOOK = 63206
    LINKEDIN = 3000


def get_filename(_, filename: str):
    return uuid.uuid4().hex + filename.lower()


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
    process_image = models.BooleanField(blank=True, null=True, default=False)
    
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


    @property
    def has_video(self):
        return self.media_file and self.media_file.path.lower().endswith('.mp4')
    
    @property
    def has_image(self):
        return self.media_file and self.media_file.path.lower().endswith((".jpeg", ".jpg", ".png"))
    
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

        if self.media_file:
            ext = os.path.splitext(self.media_file.name)[1].lower()
            if ext not in [".jpeg", ".jpg", ".png", ".mp4"]:
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
            
        if self.post_on_tiktok:
            ld_ok = IntegrationsModel.objects.filter(
                account_id=self.account_id, platform=Platform.TIKTOK.value
            ).first()
            if not ld_ok:
                raise ValueError(
                    "Please got to Integrations and authorize TikTok app"
                )
        
        super().save(*args, **kwargs)

    class Meta:
        app_label = "socialsched"
        verbose_name_plural = "scheduled"

    def __str__(self):
        return f"AccountId:{self.account_id} PostScheduledOn: {self.scheduled_on}"
