from django.db import models
from core import settings
from django.utils.translation import gettext_lazy as _
from integrations.aes import AESCBC


class Platform(models.TextChoices):
    X_TWITTER = "X", _("X")
    LINKEDIN = "LinkedIn", _("LinkedIn")
    FACEBOOK = "Facebook", _("Facebook")
    INSTAGRAM = "Instagram", _("Instagram")
    TIKTOK = "TikTok", _("TikTok")


class IntegrationsModel(models.Model):
    account_id = models.IntegerField()
    user_id = models.CharField(max_length=5000, null=True, blank=True)
    access_token = models.CharField(max_length=5000, null=True, blank=True)
    refresh_token = models.CharField(max_length=5000, null=True, blank=True)
    access_expire = models.DateTimeField(null=True, blank=True)
    refresh_expire = models.DateTimeField(null=True, blank=True)
    platform = models.CharField(max_length=1000, choices=Platform)

    def save(self, *args, **kwargs):
        aes_cbc = AESCBC(settings.SECRET_KEY)

        if self.access_token:
            self.access_token = aes_cbc.encrypt(self.access_token)
        if self.refresh_token:
            self.refresh_token = aes_cbc.encrypt(self.refresh_token)

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
