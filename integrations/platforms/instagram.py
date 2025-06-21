import os
import time
import requests
from datetime import timedelta
from core.logger import log, send_notification
from dataclasses import dataclass
from asgiref.sync import sync_to_async
from integrations.models import IntegrationsModel, Platform
from socialsched.models import PostModel, MediaFileTypes
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


    def post_text_with_reel(self, text: str, reel_url: str, reel_path: str):
        # Step 1: Get video file size from local path
        file_size_bytes = os.path.getsize(reel_path)
        file_size_mb = file_size_bytes / (1024 * 1024)

        # Step 2: Create media container for Reel
        container_response = requests.post(
            self.media_url,
            params={
                "video_url": reel_url,
                "caption": text,
                "access_token": self.access_token,
                "media_type": "REELS",
            },
        )
        container_response.raise_for_status()
        container_id = container_response.json()["id"]

        # Step 3: Poll container readiness based on video size
        max_checks = max(10, int(file_size_mb * 2))  # Scale wait by video size
        for attempt in range(max_checks):
            status_url = f"https://graph.facebook.com/{self.api_version}/{container_id}"
            status_resp = requests.get(
                status_url,
                params={
                    "fields": "status_code",
                    "access_token": self.access_token,
                },
            )
            status_resp.raise_for_status()
            status = status_resp.json().get("status_code")

            if status == "FINISHED":
                break
            elif status in {"ERROR", "EXPIRED"}:
                raise Exception(f"Media container failed with status: {status}")
            else:
                time.sleep(5)
        else:
            raise TimeoutError("Media container not ready after polling")

        # Step 4: Publish the Reel
        publish_response = requests.post(
            self.media_publish_url,
            headers={"Authorization": f"Bearer {self.access_token}"},
            json={"creation_id": container_id},
        )
        log.debug(publish_response.json())
        publish_response.raise_for_status()

        return self.get_post_url(publish_response.json()["id"])


    def make_post(self, text: str, media_type: str, media_url: str = None, media_path: str = None):
        if media_url is None:
            log.info("No media for instagram post. Skip posting.")
            return

        if media_type == MediaFileTypes.IMAGE.value:
            return self.post_text_with_image(text, media_url)

        if media_type == MediaFileTypes.VIDEO.value:
            return self.post_text_with_reel(text, media_url, media_path)

        raise ErrorThisTypeOfPostIsNotSupported


@sync_to_async
def update_instagram_link(post_id: int, post_url: str, err: str):
    post = PostModel.objects.get(id=post_id)
    post.link_instagram = post_url
    if err != "None":
        post.error_instagram = err
        post.scheduled_on += timedelta(days=1)
        post.retries_instagram += 1
        post.post_on_instagram = True
    else:
        post.post_on_instagram = False
        post.error_instagram = None
    post.save(skip_validation=True)
    return post.retries_instagram


async def post_on_instagram(
    account_id: int,
    post_id: int,
    post_text: str,
    media_type: str,
    media_url: str = None,
    media_path: str = None,
):

    err = None
    post_url = None

    integration = await get_integration(
        account_id, Platform.INSTAGRAM.value
    )
    
    if integration:
        try:
            poster = InstagramPoster(integration)
            post_url = poster.make_post(post_text, media_type, media_url, media_path)
            log.success(f"Instagram post url: {integration.account_id} {post_url}")
        except Exception as e:
            err = e
            log.error(f"Instagram post error: {integration.account_id} {err}")
            log.exception(err)
            send_notification(
                "ImPosting", f"AccountId: {integration.account_id} got error {err}"
            )
    else:
        err = "(Re-)Authorize Instagram on Integrations page"

    retries_instagram = await update_instagram_link(post_id, post_url, str(err)[0:50])

    if retries_instagram >= 10:
        await sync_to_async(integration.delete)()
