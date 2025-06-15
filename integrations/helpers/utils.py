import os
import uuid
import base64
import requests
from ..models import IntegrationsModel, Platform
from ..platforms.tiktok import TikTokPoster


# Brave browser thinks external profile url pics are an advert.
def image_url_to_base64(url: str) -> str | None:
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


def get_filepath_from_cloudflare_url(url: str, ):

    ext = os.path.splitext(url)[1].lower()
    ext = ext.split("?")[0]

    response = requests.get(url)
    response.raise_for_status()

    filepath = f"/tmp/{uuid.uuid4().hex}{ext}"
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
