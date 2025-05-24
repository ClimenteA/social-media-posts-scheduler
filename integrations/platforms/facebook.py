import re
import requests
from core.logger import log, send_notification
from asgiref.sync import sync_to_async
from dataclasses import dataclass
from integrations.models import IntegrationsModel, Platform
from socialsched.models import PostModel
from .common import (
    get_integration,
    ErrorAccessTokenNotProvided,
    ErrorPageIdNotProvided,
    ErrorThisTypeOfPostIsNotSupported,
)


@dataclass
class FacebookPoster:
    integration: IntegrationsModel
    api_version: str = "v22.0"

    def __post_init__(self):
        self.access_token = self.integration.access_token_value
        self.page_id = self.integration.user_id

        if not self.access_token:
            raise ErrorAccessTokenNotProvided

        if not self.page_id:
            raise ErrorPageIdNotProvided

        self.base_url = f"https://graph.facebook.com/{self.api_version}/{self.page_id}"
        self.feed_url = self.base_url + "/feed"
        self.photos_url = self.base_url + "/photos"

    def get_post_url(self, post_id: int):
        return f"https://www.facebook.com/{self.page_id}/posts/{post_id}"

    def post_text(self, text: str):
        payload = {
            "message": text,
            "published": True,
            "access_token": self.access_token,
        }
        response = requests.post(self.feed_url, json=payload)
        response.raise_for_status()
        return self.get_post_url(response.json()["id"])

    def post_text_with_link(self, text: str, link: str):
        payload = {
            "message": text,
            "link": link,
            "published": True,
            "access_token": self.access_token,
        }
        response = requests.post(self.feed_url, json=payload)
        response.raise_for_status()
        return self.get_post_url(response.json()["id"])

    def post_text_with_image(self, text: str, image_url: str):
        payload = {
            "message": text,
            "url": image_url,
            "access_token": self.access_token,
        }
        response = requests.post(self.photos_url, json=payload)
        log.debug(response.json())
        response.raise_for_status()

        return self.get_post_url(response.json()["post_id"])

    def make_post(self, text: str, media_url: str = None):
        if media_url is None:
            pattern = r"(https?://[^\s]+)$"
            match = re.search(pattern, text)
            if match:
                link = match.group(1)
                return self.post_text_with_link(text, link)
            return self.post_text(text)

        if media_url.endswith((".jpg", ".jpeg", ".png")):
            return self.post_text_with_image(text, media_url)

        raise ErrorThisTypeOfPostIsNotSupported


@sync_to_async
def update_facebook_link(post_id: int, post_url: str, err: str):
    post = PostModel.objects.get(id=post_id)
    post.link_facebook = post_url
    post.post_on_facebook = False
    post.error_facebook = None if err == "None" else err
    post.save(skip_validation=True)


async def post_on_facebook(
    account_id: int,
    post_id: int,
    post_text: str,
    media_url: str = None,
):
    
    err = None
    post_url = None

    integration = await get_integration(
        account_id, Platform.FACEBOOK.value
    )
    
    if integration:
        try:
            poster = FacebookPoster(integration)
            post_url = poster.make_post(post_text, media_url)
            log.success(f"Facebook post url: {integration.account_id} {post_url}")
        except Exception as e:
            err = e
            log.error(f"Facebook post error: {integration.account_id} {err}")
            log.exception(err)
            send_notification(
                "ImPosting", f"AccountId: {integration.account_id} got error {err}"
            )
            await sync_to_async(integration.delete)()
    else:
        err = "(Re-)Authorize Facebook on Integrations page"

    await update_facebook_link(post_id, post_url, str(err))
