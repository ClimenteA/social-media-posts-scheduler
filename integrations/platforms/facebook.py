import os
import re
import time
import requests
from datetime import timedelta
from core.logger import log, send_notification
from asgiref.sync import sync_to_async
from dataclasses import dataclass
from integrations.models import IntegrationsModel, Platform
from socialsched.models import PostModel, MediaFileTypes
from .common import (
    get_integration,
    ErrorAccessTokenNotProvided,
    ErrorPageIdNotProvided,
    ErrorThisTypeOfPostIsNotSupported,
)


@dataclass
class FacebookPoster:
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
        self.feed_url = self.base_url + "/feed"
        self.photos_url = self.base_url + "/photos"
        self.reels_url = self.base_url + "/video_reels"

    def get_post_url(self, post_id: int):
        return f"https://www.facebook.com/{self.page_id}/posts/{post_id}"

    def post_text(self, text: str):
        payload = {
            "message": text,
            "published": True,
            "access_token": self.access_token,
        }
        response = requests.post(self.feed_url, json=payload)
        log.debug(response.json())
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
        log.debug(response.json())
        response.raise_for_status()
        return self.get_post_url(response.json()["id"])

    def post_text_with_reel(self, text: str, reel_path: str):

        # Get upload url
        upload_start_response = requests.post(
            url=self.reels_url,
            data={
                "upload_phase": "start",
                "access_token": self.access_token,
            },
        )
        log.debug(upload_start_response.json())
        upload_start_response.raise_for_status()
        upload_start_data = upload_start_response.json()
        video_id = upload_start_data["video_id"]

        file_size_bytes = os.path.getsize(reel_path)
        file_size_mb = file_size_bytes / (1024 * 1024)

        # Upload reel
        with open(reel_path, "rb") as file:
            upload_initiated_response = requests.post(
                url=upload_start_data["upload_url"],
                headers={
                    "Authorization": f"OAuth {self.access_token}",
                    "offset": "0",
                    "file_size": str(file_size_bytes),
                },
                data=file,
            )
            log.debug(upload_initiated_response.json())
            upload_initiated_response.raise_for_status()

        finish_response = requests.post(
            url=f"https://graph.facebook.com/{self.api_version}/{self.page_id}/video_reels",
            params={
                "access_token": self.access_token,
                "video_id": video_id,
                "upload_phase": "finish",
                "description": text,
            },
        )
        log.debug(finish_response.json())
        finish_response.raise_for_status()

        time.sleep(5)
        max_checks = max(30, int(file_size_mb * 2))  # More time for larger files
        for _ in range(max_checks):
            status_res = requests.get(
                url=f"https://graph.facebook.com/{self.api_version}/{video_id}",
                params={"fields": "status", "access_token": self.access_token},
            )
            log.debug(status_res.json())
            status_res.raise_for_status()
            status_data = status_res.json().get("status", {})

            # Check processing/publishing status directly
            processing = status_data.get("processing_phase", {}).get("status")
            publishing = status_data.get("publishing_phase", {}).get("status")

            if processing == "complete" and publishing == "complete":
                break  # Success!
            elif status_data.get("video_status") in [
                "error",
                "expired",
                "upload_failed",
            ]:
                raise Exception(f"Reel processing failed: {video_id}")

            time.sleep(5)
        else:
            raise Exception("Reel processing timed out")

        # Get reel link
        reel_link_response = requests.get(
            url=f"https://graph.facebook.com/{self.api_version}/{video_id}",
            params={
                "fields": "permalink_url",
                "access_token": self.access_token,
            },
        )
        log.debug(reel_link_response.json())
        reel_link_response.raise_for_status()
        reel_info = reel_link_response.json()
        reel_link = reel_info.get("permalink_url")

        return f"https://facebook.com{reel_link}"

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

    def make_post(
        self, text: str, media_type: str, media_url: str = None, media_path: str = None
    ):
        if media_url is None and media_path is None:
            pattern = r"(https?://[^\s]+)$"
            match = re.search(pattern, text)
            if match:
                link = match.group(1)
                return self.post_text_with_link(text, link)
            return self.post_text(text)

        if media_type == MediaFileTypes.IMAGE.value:
            return self.post_text_with_image(text, media_url)

        if media_type == MediaFileTypes.VIDEO.value:
            return self.post_text_with_reel(text, media_path)

        raise ErrorThisTypeOfPostIsNotSupported


@sync_to_async
def update_facebook_link(post_id: int, post_url: str, err: str):
    post = PostModel.objects.get(id=post_id)
    post.link_facebook = post_url
    if err != "None":
        post.error_facebook = err
        post.retries_facebook += 1
        delay_minutes = 5 * (2 ** (post.retries_facebook - 1))
        post.scheduled_on += timedelta(minutes=delay_minutes)
        post.post_on_facebook = True
    else:
        post.post_on_facebook = False
        post.error_facebook = None
    post.save(skip_validation=True)
    return post.retries_facebook


async def post_on_facebook(
    account_id: int,
    post_id: int,
    post_text: str,
    media_type: str,
    media_url: str = None,
    media_path: str = None,
):

    err = None
    post_url = None

    integration = await get_integration(account_id, Platform.FACEBOOK.value)

    if integration:
        try:
            poster = FacebookPoster(integration)
            post_url = poster.make_post(post_text, media_type, media_url, media_path)
            log.success(f"Facebook post url: {integration.account_id} {post_url}")
        except Exception as e:
            err = e
            log.error(f"Facebook post error: {integration.account_id} {err}")
            log.exception(err)
            send_notification(
                "ImPosting", f"AccountId: {integration.account_id} got error {err}"
            )
    else:
        err = "(Re-)Authorize Facebook on Integrations page"

    retries_facebook = await update_facebook_link(post_id, post_url, str(err)[0:50])
    if retries_facebook >= 20:
        await sync_to_async(integration.delete)()
