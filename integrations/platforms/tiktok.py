import requests
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
class TikTokPoster:
    integration: IntegrationsModel
    api_version: str = "v2"

    def __post_init__(self):
        pass


    def make_post(self, text: str, media_path: str):
        pass





@sync_to_async
def update_tiktok_link(post_id: int, post_url: str, err: str):
    post = PostModel.objects.get(id=post_id)
    post.link_tiktok = post_url
    post.post_on_tiktok = False
    post.error_tiktok = None if err == "None" else err
    post.save(skip_validation=True)


async def post_on_tiktok(
    account_id: int,
    post_id: int,
    post_text: str,
    media_path: str = None,
):

    err = None
    post_url = None

    integration = await get_integration(
        account_id, Platform.TIKTOK.value
    )

    if integration:
        try:
            poster = TikTokPoster(integration)
            post_url = poster.make_post(post_text, media_path)
            log.success(f"TikTok post url: {integration.account_id} {post_url}")
        except Exception as e:
            err = e
            log.error(f"TikTok post error: {integration.account_id} {err}")
            log.exception(err)
            send_notification(
                "ImPosting", f"AccountId: {integration.account_id} got error {err}"
            )
            await sync_to_async(integration.delete)()
    else:
        err = "(Re-)Authorize TikTok on Integrations page"

    await update_tiktok_link(post_id, post_url, str(err)[0:50])
