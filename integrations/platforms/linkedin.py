import requests
from datetime import timedelta
from core.logger import log, send_notification
from dataclasses import dataclass
from integrations.models import IntegrationsModel, Platform
from socialsched.models import PostModel
from asgiref.sync import sync_to_async
from .common import (
    get_integration,
    ErrorAccessTokenNotProvided,
    ErrorUserIdNotProvided,
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
                "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
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
        log.debug(upload_response.json())
        upload_response.raise_for_status()
        upload_data = upload_response.json()
        upload_url = upload_data["value"]["uploadMechanism"][
            "com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"
        ]["uploadUrl"]
        asset = upload_data["value"]["asset"]

        with open(filepath, "rb") as image_file:
            response = requests.put(
                upload_url,
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/octet-stream",
                },
                data=image_file,
            )
            log.debug(response.content)
            response.raise_for_status()
        
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
        log.debug(response.json())
        response.raise_for_status()

        return f"https://www.linkedin.com/feed/update/{response.json()['id']}"


@sync_to_async
def update_linkedin_link(post_id: int, post_url: str, err: str):
    post = PostModel.objects.get(id=post_id)

    if err != "None":
        # Update existing post with error
        post.error_linkedin = err
        post.post_on_linkedin = False
        post.save(skip_validation=True)

        # Clone post for retry
        new_post = PostModel.objects.get(id=post_id)
        new_post.pk = None

        new_post.retries_linkedin += 1
        delay_minutes = 5 * (2 ** (new_post.retries_linkedin - 1))
        new_post.scheduled_on += timedelta(minutes=delay_minutes)
        new_post.error_linkedin = err

        # Only retry current platform
        new_post.post_on_x = False
        new_post.post_on_instagram = False
        new_post.post_on_facebook = False
        new_post.post_on_linkedin = True
        new_post.post_on_tiktok = False

        # Reset links
        new_post.link_x = None
        new_post.link_instagram = None
        new_post.link_facebook = None
        new_post.link_linkedin = None
        new_post.link_tiktok = None

        # Reset errors (keep only current one)
        new_post.error_x = None
        new_post.error_instagram = None
        new_post.error_facebook = None
        # new_post.error_linkedin = None
        new_post.error_tiktok = None

        # Reset retries for other platforms
        new_post.retries_x = 0
        new_post.retries_instagram = 0
        new_post.retries_facebook = 0
        # new_post.retries_linkedin = 0
        new_post.retries_tiktok = 0

        new_post.save(skip_validation=True)

        return new_post.retries_linkedin

    else:
        post.link_linkedin = post_url
        post.post_on_linkedin = False
        post.error_linkedin = None
        post.save(skip_validation=True)

        return post.retries_linkedin



async def post_on_linkedin(
    account_id: int,
    post_id: int,
    post_text: str,
    media_path: str = None,
):

    err = None
    post_url = None

    integration = await get_integration(
        account_id, Platform.LINKEDIN.value
    )

    if integration:
        try:
            poster = LinkedinPoster(integration)
            post_url = poster.make_post(post_text, media_path)
            log.success(f"Linkedin post url: {integration.account_id} {post_url}")
        except Exception as e:
            err = e
            log.error(f"Linkedin post error: {integration.account_id} {err}")
            log.exception(err)
            send_notification(
                "ImPosting", f"AccountId: {integration.account_id} got error {err}"
            )
    else:
        err = "(Re-)Authorize Linkedin on Integrations page"

    retries_linkedin = await update_linkedin_link(post_id, post_url, str(err)[0:50])
    if retries_linkedin >= 20:
        await sync_to_async(integration.delete)()
