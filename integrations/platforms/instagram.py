import requests
from core.logger import log, send_notification
from dataclasses import dataclass
from asgiref.sync import sync_to_async
from integrations.models import IntegrationsModel, Platform
from socialsched.models import PostModel
from .common import (
    get_integration,
    ErrorAccessTokenNotProvided,
    ErrorPageIdNotProvided,
    ErrorThisTypeOfPostIsNotSupported,
)


@dataclass
class InstagramPoster:
    integration: IntegrationsModel
    api_version: str = "v23.0"

    def __post_init__(self):
        self.access_token = self.integration.access_token_value
        self.page_id = self.integration.user_id

        if not self.access_token:
            raise ErrorAccessTokenNotProvided

        if not self.page_id:
            raise ErrorPageIdNotProvided

        self.base_url = f"https://graph.facebook.com/{self.api_version}/{self.page_id}"
        self.media_url = self.base_url + "/media"
        self.media_publish_url = self.base_url + "/media_publish"

    def get_post_url(self, post_id: int):
        url = f"https://graph.facebook.com/{post_id}"
        params = {
            "fields": "permalink",
            "access_token": self.access_token,
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()["permalink"]

    def post_text_with_image(self, text: str, image_url: str):
        params = {
            "image_url": image_url,
            "is_carousel_item": False,
            "alt_text": text,
            "caption": text,
            "access_token": self.access_token,
        }
        container = requests.post(self.media_url, params=params)
        container.raise_for_status()

        publish = requests.post(
            self.media_publish_url,
            headers={"Authorization": f"Bearer {self.access_token}"},
            json={"creation_id": container.json()["id"]},
        )
        publish.raise_for_status()

        return self.get_post_url(publish.json()["id"])

    def post_text_with_video(self, text: str, video_url: str):
        
        params = {
            "media_type": "REELS",
            "video_url": video_url,
            "caption": text,
            "access_token": self.access_token,
            "share_to_feed": True,
        }

        container = requests.post(self.media_url, params=params)
        container.raise_for_status()

        publish = requests.post(
            self.media_publish_url,
            headers={"Authorization": f"Bearer {self.access_token}"},
            json={"creation_id": container.json()["id"]},
        )
        publish.raise_for_status()

        return self.get_post_url(publish.json()["id"])


    def make_post(self, text: str, media_url: str = None):
        if media_url is None:
            log.info("No media for instagram post. Skip posting.")
            return

        if media_url:
            if media_url.endswith((".jpg", ".jpeg", ".png")):
                return self.post_text_with_image(text, media_url)

            if media_url.endswith(".mp4"):
                return self.post_text_with_video(text, media_url)

        raise ErrorThisTypeOfPostIsNotSupported


@sync_to_async
def update_instagram_link(post_id: int, post_url: str, err: str):
    post = PostModel.objects.get(id=post_id)
    post.link_instagram = post_url
    post.post_on_instagram = False
    post.error_instagram = None if err == "None" else err
    post.save(skip_validation=True)


async def post_on_instagram(
    account_id: int,
    post_id: int,
    post_text: str,
    media_url: str = None,
):

    err = None
    post_url = None

    integration = await get_integration(
        account_id, Platform.INSTAGRAM.value
    )
    
    if integration:
        try:
            poster = InstagramPoster(integration)
            post_url = poster.make_post(post_text, media_url)
            log.success(f"Instagram post url: {integration.account_id} {post_url}")
        except Exception as e:
            err = e
            log.error(f"Instagram post error: {integration.account_id} {err}")
            log.exception(err)
            send_notification(
                "ImPosting", f"AccountId: {integration.account_id} got error {err}"
            )
            await sync_to_async(integration.delete)()
    else:
        err = "(Re-)Authorize Instagram on Integrations page"

    await update_instagram_link(post_id, post_url, str(err)[0:50])
