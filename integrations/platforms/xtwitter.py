import base64
from datetime import timedelta
from typing import Literal
from core import settings
from core.logger import log, send_notification
from dataclasses import dataclass
from asgiref.sync import sync_to_async
from socialsched.models import PostModel
from requests_oauthlib import OAuth2Session
from integrations.models import IntegrationsModel, Platform
from .common import (
    get_integration,
    ErrorAccessTokenNotProvided,
    ErrorThisTypeOfPostIsNotSupported,
)


@dataclass
class XPoster:
    integration: IntegrationsModel
    api_version: str = "2"
    chunk_size: int = 1024 * 1024  # 1MB

    def __post_init__(self):
        self.access_token = self.integration.access_token_value
        if not self.access_token:
            raise ErrorAccessTokenNotProvided

        self.chunk_size: int = 5 * 1024 * 1024  # 5MB
        self.base_url = f"https://api.x.com/{self.api_version}/tweets"
        self.upload_url = f"https://api.x.com/{self.api_version}/media/upload"
        self.upload_init_url = self.upload_url + "/initialize"
        self.upload_append_url = lambda media_id: f"{self.upload_url}/{media_id}/append"
        self.upload_finalize_url = (
            lambda media_id: f"{self.upload_url}/{media_id}/finalize"
        )

        self.client = OAuth2Session(
            client_id=settings.X_CLIENT_ID,
            token={"access_token": self.access_token, "token_type": "bearer"},
        )

    def _make_authenticated_request(
        self, method: Literal["post", "get"], url: str, **kwargs
    ):
        response = getattr(self.client, method)(url, **kwargs)
        log.debug(response.content)
        response.raise_for_status()
        return response

    def get_post_url(self, id: int):
        return f"https://x.com/user/status/{id}"

    def post_text(self, text: str):
        response = self._make_authenticated_request(
            "post",
            self.base_url,
            headers={"Content-Type": "application/json"},
            json={"text": text},
        )
        return self.get_post_url(response.json()["data"]["id"])

    def post_text_with_image(self, text: str, image_path: str):
        media_type = None
        if image_path.endswith((".jpg", ".jpeg")):
            media_type = "image/jpeg"
        if image_path.endswith(".png"):
            media_type = "image/png"

        with open(image_path, "rb") as f:
            file_content = f.read()
            base64_encoded = base64.b64encode(file_content).decode("utf-8")

            upload_response = self._make_authenticated_request(
                "post",
                self.upload_url,
                headers={
                    "Content-Type": "application/json",
                    "Content-Transfer-Encoding": "base64",
                },
                json={
                    "media_category": "tweet_image",
                    "media_type": media_type,
                    "shared": True,
                    "media": base64_encoded,
                },
            )
            log.debug(upload_response.content)

            media_id = upload_response.json()["data"]["id"]

        response = self._make_authenticated_request(
            "post",
            self.base_url,
            headers={"Content-Type": "application/json"},
            json={"text": text, "media": {"media_ids": [media_id]}},
        )
        return self.get_post_url(response.json()["data"]["id"])

    def make_post(self, text: str, media_path: str = None):

        if not media_path:
            return self.post_text(text)

        if media_path.endswith((".jpg", ".jpeg", ".png")):
            return self.post_text_with_image(text, media_path)

        raise ErrorThisTypeOfPostIsNotSupported


@sync_to_async
def update_x_link(post_id: int, post_url: str, err: str):
    post = PostModel.objects.get(id=post_id)

    if err != "None":
        # Update existing post with error
        post.error_x = err
        post.post_on_x = False
        post.save(skip_validation=True)

        # Clone post for retry
        new_post = PostModel.objects.get(id=post_id)
        new_post.pk = None

        new_post.retries_x += 1
        delay_minutes = 5 * (2 ** (new_post.retries_x - 1))
        new_post.scheduled_on += timedelta(minutes=delay_minutes)
        new_post.error_x = err

        # Only retry current platform
        new_post.post_on_x = True
        new_post.post_on_instagram = False
        new_post.post_on_facebook = False
        new_post.post_on_linkedin = False
        new_post.post_on_tiktok = False

        # Reset links
        new_post.link_x = None
        new_post.link_instagram = None
        new_post.link_facebook = None
        new_post.link_linkedin = None
        new_post.link_tiktok = None

        # Reset errors (keep only current one)
        # new_post.error_x = None
        new_post.error_instagram = None
        new_post.error_facebook = None
        new_post.error_linkedin = None
        new_post.error_tiktok = None

        # Reset retries for other platforms
        # new_post.retries_x = 0
        new_post.retries_instagram = 0
        new_post.retries_facebook = 0
        new_post.retries_linkedin = 0
        new_post.retries_tiktok = 0

        new_post.save(skip_validation=True)

        return new_post.retries_x

    else:
        post.link_x = post_url
        post.post_on_x = False
        post.error_x = None
        post.save(skip_validation=True)

        return post.retries_x


async def post_on_x(
    account_id: int,
    post_id: int,
    post_text: str,
    media_path: str = None,
):

    err = None
    post_url = None

    integration = await get_integration(account_id, Platform.X_TWITTER.value)

    if integration:
        try:
            poster = XPoster(integration)
            post_url = poster.make_post(post_text, media_path)
            log.success(f"X post url: {integration.account_id} {post_url}")
        except Exception as e:
            err = e
            log.error(f"X post error: {integration.account_id} {err}")
            log.exception(err)
            send_notification(
                "ImPosting", f"AccountId: {integration.account_id} got error {err}"
            )
    else:
        err = "(Re-)Authorize X on Integrations page"

    retries_x = await update_x_link(post_id, post_url, str(err)[0:50])
    if retries_x >= 20:
        await sync_to_async(integration.delete)()
