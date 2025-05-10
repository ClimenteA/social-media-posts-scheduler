import requests
from core.logger import log, send_notification
from dataclasses import dataclass
from django.utils import timezone
from integrations.models import IntegrationsModel
from socialsched.models import PostModel
from asgiref.sync import sync_to_async
from .common import (
    ErrorAccessTokenNotProvided,
    ErrorUserIdNotProvided,
)


def refresh_access_token_for_linkedin(integration: IntegrationsModel):
    if integration.access_expire < timezone.now():
        log.warning(
            f"Access token expired for account {integration.account_id}. User must reauthenticate."
        )

        integration.access_token = None
        integration.access_expire = None
        integration.save()

        send_notification(
            "ImPosting",
            f"LinkedIn access token expired for account {integration.account_id}.",
        )
        return

    log.info(
        f"LinkedIn access token is still valid for account {integration.account_id}. No action needed."
    )


@dataclass
class LinkedinPoster:
    integration: IntegrationsModel
    api_version: str = "v2"

    def __post_init__(self):

        self.user_id = self.integration.user_id
        self.access_token = self.integration.access_token_value

        if not self.user_id:
            raise ErrorUserIdNotProvided

        if not self.access_token:
            raise ErrorAccessTokenNotProvided

        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0",
        }

    def _get_basic_payload(self, post_text: str, share_media_category: str):

        payload = {
            "author": f"urn:li:person:{self.user_id}",
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": post_text},
                    "shareMediaCategory": share_media_category,
                }
            },
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
        }

        return payload

    def _upload_media(self, filepath: str):

        upload_payload = {
            "registerUploadRequest": {
                "recipes": [f"urn:li:digitalmediaRecipe:feedshare-image"],
                "owner": f"urn:li:person:{self.user_id}",
                "serviceRelationships": [
                    {
                        "relationshipType": "OWNER",
                        "identifier": "urn:li:userGeneratedContent",
                    }
                ],
            }
        }

        upload_response = requests.post(
            url=f"https://api.linkedin.com/{self.api_version}/assets?action=registerUpload",
            headers=self.headers,
            json=upload_payload,
        )
        upload_data = upload_response.json()
        upload_url = upload_data["value"]["uploadMechanism"][
            "com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"
        ]["uploadUrl"]
        asset = upload_data["value"]["asset"]

        with open(filepath, "rb") as image_file:
            requests.put(
                upload_url,
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/octet-stream",
                },
                data=image_file,
            )

        return asset

    def make_post(self, text: str, media_path: str = None):
        share_media_category = "IMAGE" if media_path else "NONE"
        payload = self._get_basic_payload(text, share_media_category)

        if share_media_category == "IMAGE":
            asset = self._upload_media(media_path)
            payload["specificContent"]["com.linkedin.ugc.ShareContent"]["media"] = [
                {
                    "status": "READY",
                    "description": {"text": text[:20].lower()},
                    "media": asset,
                    "title": {"text": text[:20]},
                }
            ]

        response = requests.post(
            url=f"https://api.linkedin.com/{self.api_version}/ugcPosts",
            headers=self.headers,
            json=payload,
        )

        return f"https://www.linkedin.com/feed/update/{response.json()['id']}"


@sync_to_async
def update_linkedin_link(post_id: int, post_url: str):
    post = PostModel.objects.get(id=post_id)
    post.link_linkedin = post_url
    post.post_on_linkedin = False
    post.save(skip_validation=True)


async def post_on_linkedin(
    integration: IntegrationsModel,
    post_id: int,
    post_text: str,
    media_path: str = None,
):

    post_url = None

    try:
        poster = LinkedinPoster(integration)
        post_url = poster.make_post(post_text, media_path)
        log.success(f"Linkedin post url: {integration.account_id} {post_url}")
    except Exception as err:
        log.error(f"Linkedin post error: {integration.account_id} {err}")
        log.exception(err)
        send_notification(
            "ImPosting", f"AccountId: {integration.account_id} got error {str(err)}"
        )
        await sync_to_async(integration.delete)()

    await update_linkedin_link(post_id, post_url)
