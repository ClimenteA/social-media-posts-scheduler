import os
import requests
import mimetypes
from core.logger import log
from core import settings
from django.db import models
from integrations.helpers.aes import AESCBC
from django.core.files.base import ContentFile
from django.utils.translation import gettext_lazy as _


class Platform(models.TextChoices):
    X_TWITTER = "X", _("X")
    LINKEDIN = "LinkedIn", _("LinkedIn")
    FACEBOOK = "Facebook", _("Facebook")
    INSTAGRAM = "Instagram", _("Instagram")
    TIKTOK = "TikTok", _("TikTok")



def get_filename(instance, filename):
    ext = os.path.splitext(filename)[1].lower()
    return f"{instance.account_id}/avatar/{instance.platform}{ext or '.jpg'}"



class IntegrationsModel(models.Model):
    account_id = models.IntegerField()
    user_id = models.CharField(max_length=5000, null=True, blank=True)
    access_token = models.CharField(max_length=5000, null=True, blank=True)
    refresh_token = models.CharField(max_length=5000, null=True, blank=True)
    access_expire = models.DateTimeField(null=True, blank=True)
    refresh_expire = models.DateTimeField(null=True, blank=True)
    platform = models.CharField(max_length=1000, choices=Platform)
    username = models.CharField(max_length=1000, null=True, blank=True)
    avatar_url = models.CharField(max_length=100000, null=True, blank=True)
    avatar = models.ImageField(
        max_length=100_000,
        upload_to=get_filename,
        null=True,
        blank=True,
    )

    def save(self, *args, **kwargs):
        aes_cbc = AESCBC(settings.SECRET_KEY)

        if self.access_token:
            self.access_token = aes_cbc.encrypt(self.access_token)
        if self.refresh_token:
            self.refresh_token = aes_cbc.encrypt(self.refresh_token)

        if self.avatar_url and not self.avatar:
            try:
                response = requests.get(self.avatar_url)
                response.raise_for_status()

                content_type = response.headers.get("Content-Type", "")
                extension = mimetypes.guess_extension(content_type.split(";")[0].strip())

                for ext in [".png", ".jpg", ".jpeg"]:
                    if ext in self.avatar_url:
                        extension = ext
                        break

                filename = f"avatar{extension}"

                self.avatar.save(filename, ContentFile(response.content), save=False)
            except Exception as err:
                log.exception(err)
                log.error(f"Failed to download avatar from {self.avatar_url}: {err}")

        super().save(*args, **kwargs)

    @property
    def access_token_value(self):
        aes_cbc = AESCBC(settings.SECRET_KEY)
        return aes_cbc.decrypt(self.access_token) if self.access_token else None

    @property
    def refresh_token_value(self):
        aes_cbc = AESCBC(settings.SECRET_KEY)
        return aes_cbc.decrypt(self.refresh_token) if self.refresh_token else None

    class Meta:
        app_label = "integrations"
        verbose_name_plural = "integrations"

    def __str__(self):
        return f"AccountId:{self.account_id} Platform: {self.platform}"
