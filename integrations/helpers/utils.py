import os
import uuid
import requests
from core.logger import log
from pathlib import Path
from django.core.cache import cache
from integrations.models import IntegrationsModel, Platform
from integrations.platforms.tiktok import TikTokPoster



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

    key = f"tiktok_creator_info_{account_id}"

    result = cache.get(key)
    if result:
        return result

    integration = IntegrationsModel.objects.filter(
        account_id=account_id, platform=Platform.TIKTOK.value
    ).first()

    if not integration:
        return

    poster = TikTokPoster(integration)

    result = poster.get_creator_info()

    if result is None:
        cache.delete(key)
        integration.delete()
    
    cache.set(key, value=result)
    return result



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
            linkedin_integration.avatar.url
            if linkedin_integration
            else None
        ),
        "linkedin_username": (
            linkedin_integration.username if linkedin_integration else None
        ),
        "x_avatar_url": (
            x_integration.avatar.url if x_integration else None
        ),
        "x_username": x_integration.username if x_integration else None,
        "tiktok_avatar_url": (
            tiktok_integration.avatar.url
            if tiktok_integration
            else None
        ),
        "tiktok_username": (
            tiktok_integration.username if tiktok_integration else None
        ),
        "facebook_avatar_url": (
            facebook_integration.avatar.url
            if facebook_integration
            else None
        ),
        "facebook_username": (
            facebook_integration.username if facebook_integration else None
        ),
        "instagram_avatar_url": (
            instagram_integration.avatar.url
            if instagram_integration
            else None
        ),
        "instagram_username": (
            instagram_integration.username if instagram_integration else None
        ),
        "x_ok": x_ok,
        "linkedin_ok": linkedin_ok,
        "instagram_ok": instagram_ok,
        "facebook_ok": facebook_ok,
        "meta_ok": facebook_ok and instagram_ok,
        "tiktok_ok": tiktok_ok,
        "x_expire": x_expire,
        "has_at_least_one_valid_integration": any([linkedin_ok, facebook_ok, instagram_ok, tiktok_ok, x_ok]),
        "linkedin_expire": linkedin_expire,
        "meta_expire": facebook_expire,
        "tiktok_expire": tiktok_expire,
    }
