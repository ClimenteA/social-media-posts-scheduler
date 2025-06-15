import requests
from datetime import datetime
from datetime import timedelta
from core import settings
from django.utils import timezone
from core.logger import log, send_notification
from integrations.models import IntegrationsModel, Platform
from django.db.models import Q


def refresh_access_token_for_x(integration: IntegrationsModel):
    refresh_token = integration.refresh_token_value
    if not refresh_token:
        integration.delete()
        return

    try:
        token_url = "https://api.x.com/2/oauth2/token"

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
        }

        auth = (settings.X_CLIENT_ID, settings.X_CLIENT_SECRET)

        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        }

        log.info(f"Refreshing access token for account {integration.account_id}")
        response = requests.post(token_url, data=data, headers=headers, auth=auth)
        response.raise_for_status()

        new_token = response.json()

        integration.access_token = new_token["access_token"]

        if new_token.get("refresh_token"):
            integration.refresh_token = new_token["refresh_token"]

        expires_in = new_token.get("expires_in", 7200)
        integration.access_expire = timezone.now() + timedelta(seconds=expires_in - 900)

        integration.save()
        log.success(f"Access token refreshed for account {integration.account_id}")

    except Exception as e:
        log.error(f"Token refresh failed for account {integration.account_id}")
        log.exception(e)
        send_notification(
            "ImPosting",
            f"Token refresh failed for X account {integration.account_id}: {str(e)}",
        )
        integration.delete()


def refresh_access_token_for_linkedin(integration: IntegrationsModel):
    if integration.access_expire < timezone.now():
        log.warning(f"Access token expired for account {integration.account_id}.")

        integration.delete()

        send_notification(
            "ImPosting",
            f"LinkedIn access token expired for account {integration.account_id}.",
        )
        return

    log.info(
        f"LinkedIn access token is still valid for account {integration.account_id}. No action needed."
    )


def refresh_access_token_for_instagram(
    account_id: int, access_token: str, access_expire: datetime
):

    integration = IntegrationsModel.objects.filter(
        account_id=account_id, platform=Platform.INSTAGRAM.value
    ).first()

    integration.access_token = access_token
    integration.access_expire = access_expire
    integration.save()


def refresh_access_token_for_facebook(integration: IntegrationsModel):
    try:
        token_url = "https://graph.facebook.com/v22.0/oauth/access_token"
        params = {
            "grant_type": "fb_exchange_token",
            "client_id": settings.FACEBOOK_CLIENT_ID,
            "client_secret": settings.FACEBOOK_CLIENT_SECRET,
            "fb_exchange_token": integration.access_token_value,
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        log.info(
            f"Refreshing Facebook access token for account {integration.account_id}"
        )
        response = requests.get(token_url, params=params, headers=headers)
        response.raise_for_status()

        new_token_data = response.json()
        new_access_token = new_token_data.get("access_token")

        if not new_access_token:
            raise ValueError("Failed to retrieve new access token.")

        access_expire = timezone.now() + timedelta(days=60)
        integration.access_token = new_access_token
        integration.access_expire = access_expire
        integration.save()

        refresh_access_token_for_instagram(
            integration.account_id, new_access_token, access_expire
        )

        log.success(f"Facebook token refreshed for account {integration.account_id}")

    except Exception as e:
        log.error(f"Token refresh failed for Facebook account {integration.account_id}")
        log.exception(e)

        send_notification(
            "ImPosting",
            f"Facebook token refresh failed for account {integration.account_id}: {str(e)}",
        )

        integration.delete()


def refresh_access_token_for_tiktok(integration: IntegrationsModel):
    refresh_token = integration.refresh_token_value
    if not refresh_token:
        integration.delete()
        return

    try:
        token_url = "https://open.tiktokapis.com/v2/oauth/token/"

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Cache-Control": "no-cache",
        }

        data = {
            "client_key": settings.TIKTOK_CLIENT_ID,
            "client_secret": settings.TIKTOK_CLIENT_SECRET,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        }

        log.info(f"Refreshing access token for TikTok account {integration.account_id}")
        response = requests.post(token_url, data=data, headers=headers)
        response.raise_for_status()

        new_token = response.json()

        # Update the access token
        integration.access_token = new_token["access_token"]

        # Update refresh token if a new one is provided
        if new_token.get("refresh_token"):
            integration.refresh_token = new_token["refresh_token"]

        # Set access token expiration (subtract 15 minutes for safety buffer)
        expires_in = new_token.get("expires_in", 86400)  # Default to 24 hours if not provided
        integration.access_expire = timezone.now() + timedelta(seconds=expires_in - 900)

        # Set refresh token expiration if provided
        if new_token.get("refresh_expires_in"):
            refresh_expires_in = new_token["refresh_expires_in"]
            integration.refresh_expire = timezone.now() + timedelta(seconds=refresh_expires_in - 900)

        integration.save()
        log.success(f"Access token refreshed for TikTok account {integration.account_id}")

    except Exception as e:
        log.error(f"Token refresh failed for TikTok account {integration.account_id}")
        log.exception(e)

        send_notification(
            "ImPosting",
            f"TikTok token refresh failed for account {integration.account_id}: {str(e)}",
        )

        integration.delete()


refresh_methods = {
    Platform.X_TWITTER.value: refresh_access_token_for_x,
    Platform.FACEBOOK.value: refresh_access_token_for_facebook,
    Platform.LINKEDIN.value: refresh_access_token_for_linkedin,
    Platform.TIKTOK.value: refresh_access_token_for_tiktok,
}


def refresh_tokens():
    try:

        time_threshold = timezone.now() + timedelta(minutes=15)

        integrations = IntegrationsModel.objects.filter(
            Q(access_expire__lte=time_threshold) | Q(refresh_expire__lte=time_threshold)
        )

        for integration in integrations:
            refresh_method = refresh_methods.get(integration.platform)
            if refresh_method:
                refresh_method(integration)

    except Exception as err:
        log.exception(err)
        send_notification("ImPosting", f"Could not refresh tokens because {err}")
