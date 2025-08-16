import os
import uuid
import base64
import functools
import requests
from core.logger import log
from pathlib import Path
from integrations.models import IntegrationsModel, Platform
from integrations.platforms.tiktok import TikTokPoster


@functools.cache
def image_url_to_base64(url: str) -> str | None:
    # Adblockers think images hosted on social media platforms are ads
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()

        content_type = response.headers.get("Content-Type", "")
        if not content_type.startswith("image/"):
            return None

        encoded_image = base64.b64encode(response.content).decode("utf-8")
        return f"data:{content_type};base64,{encoded_image}"
    except requests.RequestException:
        return url



def get_filepath_from_cloudflare_url(url: str):

    ext = os.path.splitext(url)[1].lower()
    ext = ext.split("?")[0]
    filepath = f"/tmp/{uuid.uuid4().hex}{ext}"

    response = requests.get(url)
    response.raise_for_status()

    with open(filepath, "wb") as f:
        f.write(response.content)

    return filepath


def get_tiktok_creator_info(account_id: int):

    integration = IntegrationsModel.objects.filter(
        account_id=account_id, platform=Platform.TIKTOK.value
    ).first()

    if not integration:
        return

    poster = TikTokPoster(integration)

    return poster.get_creator_info()


def delete_tmp_media_files():

    for file_path in Path("/tmp").iterdir():
        if file_path.is_file() and file_path.suffix.lower() in {".png", ".jpeg", ".jpg", ".mp4"}:
            try:
                file_path.unlink()
            except Exception as err:
                log.exception(err)



def get_integrations_context(social_uid: int):

    linkedin_integration = IntegrationsModel.objects.filter(
        account_id=social_uid, platform=Platform.LINKEDIN.value
    ).first()
    linkedin_ok = bool(linkedin_integration)

    x_integration = IntegrationsModel.objects.filter(
        account_id=social_uid, platform=Platform.X_TWITTER.value
    ).first()
    x_ok = bool(x_integration)

    tiktok_integration = IntegrationsModel.objects.filter(
        account_id=social_uid, platform=Platform.TIKTOK.value
    ).first()
    tiktok_ok = bool(tiktok_integration)

    facebook_integration = IntegrationsModel.objects.filter(
        account_id=social_uid, platform=Platform.FACEBOOK.value
    ).first()
    facebook_ok = bool(facebook_integration)

    instagram_integration = IntegrationsModel.objects.filter(
        account_id=social_uid, platform=Platform.INSTAGRAM.value
    ).first()
    instagram_ok = bool(instagram_integration)

    x_expire = None
    if x_integration:
        if x_integration.access_expire:
            x_expire = x_integration.access_expire.date()

    tiktok_expire = None
    if tiktok_integration:
        if tiktok_integration.access_expire:
            tiktok_expire = tiktok_integration.access_expire.date()

    linkedin_expire = None
    if linkedin_integration:
        if linkedin_integration.access_expire:
            linkedin_expire = linkedin_integration.access_expire.date()

    facebook_expire = None
    if facebook_integration:
        if facebook_integration.access_expire:
            facebook_expire = facebook_integration.access_expire.date()

    return {
        "linkedin_avatar_url": (
            image_url_to_base64(linkedin_integration.avatar.url)
            if linkedin_integration
            else None
        ),
        "linkedin_username": (
            linkedin_integration.username if linkedin_integration else None
        ),
        "x_avatar_url": (
            image_url_to_base64(x_integration.avatar.url) if x_integration else None
        ),
        "x_username": x_integration.username if x_integration else None,
        "tiktok_avatar_url": (
            image_url_to_base64(tiktok_integration.avatar.url)
            if tiktok_integration
            else None
        ),
        "tiktok_username": (
            tiktok_integration.username if tiktok_integration else None
        ),
        "facebook_avatar_url": (
            image_url_to_base64(facebook_integration.avatar.url)
            if facebook_integration
            else None
        ),
        "facebook_username": (
            facebook_integration.username if facebook_integration else None
        ),
        "instagram_avatar_url": (
            image_url_to_base64(instagram_integration.avatar.url)
            if instagram_integration
            else None
        ),
        "instagram_username": (
            instagram_integration.username if instagram_integration else None
        ),
        "x_ok": x_ok,
        "linkedin_ok": linkedin_ok,
        "instagram_ok": facebook_ok,
        "meta_ok": facebook_ok and instagram_ok,
        "tiktok_ok": tiktok_ok,
        "x_expire": x_expire,
        "linkedin_expire": linkedin_expire,
        "meta_expire": facebook_expire,
        "tiktok_expire": tiktok_expire,
    }
