import os
import time
import math
import requests
from core.logger import log, send_notification
from dataclasses import dataclass
from integrations.models import IntegrationsModel, Platform
from socialsched.models import PostModel
from asgiref.sync import sync_to_async
from .common import (
    get_integration,
    ErrorAccessTokenNotProvided,
)


@dataclass
class TikTokPoster:
    integration: IntegrationsModel
    api_version: str = "v2"
    MIN_CHUNK_SIZE: int = 5 * 1024 * 1024  # 5 MB
    MAX_CHUNK_SIZE: int = 64 * 1024 * 1024  # 64 MB
    DEFAULT_CHUNK_SIZE: int = 10 * 1024 * 1024  # 10 MB (safe default)

    def __post_init__(self):
        self.access_token = self.integration.access_token_value
        if not self.access_token:
            raise ErrorAccessTokenNotProvided("TikTok access token missing.")
        self.base_url = "https://open.tiktokapis.com"
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json; charset=UTF-8",
        }

    def _calculate_chunk_params(self, video_size: int):
        """Calculate proper chunk size and count according to TikTok's rules."""

        # If video is less than 5MB, upload as whole
        if video_size < self.MIN_CHUNK_SIZE:
            return video_size, 1

        # If video is less than or equal to 64MB, upload as whole
        if video_size <= self.MAX_CHUNK_SIZE:
            return video_size, 1

        # For larger videos, calculate chunks
        chunk_size = self.DEFAULT_CHUNK_SIZE
        total_chunk_count = math.ceil(video_size / chunk_size)

        # Ensure we don't exceed 1000 chunks limit
        if total_chunk_count > 1000:
            chunk_size = math.ceil(video_size / 1000)
            # Ensure chunk_size is at least 5MB
            if chunk_size < self.MIN_CHUNK_SIZE:
                chunk_size = self.MIN_CHUNK_SIZE
            total_chunk_count = math.ceil(video_size / chunk_size)

        return chunk_size, total_chunk_count

    def make_post(self, text: str, media_path: str):
        if not media_path or not media_path.lower().endswith(".mp4"):
            log.info("Skipping TikTok post: Not a video or path is missing.")
            return None

        video_size = os.path.getsize(media_path)
        chunk_size, total_chunk_count = self._calculate_chunk_params(video_size)

        log.info(
            f"Video size: {video_size} bytes, Chunk size: {chunk_size} bytes, Total chunks: {total_chunk_count}"
        )

        # Initialize TikTok post
        init_url = f"{self.base_url}/v2/post/publish/video/init/"
        init_payload = {
            "post_info": {
                "title": text[:2200],
                "privacy_level": "SELF_ONLY", # PUBLIC_TO_EVERYONE, SELF_ONLY
                "disable_duet": False,
                "disable_comment": False,
                "disable_stitch": False,
            },
            "source_info": {
                "source": "FILE_UPLOAD",
                "video_size": video_size,
                "chunk_size": chunk_size,
                "total_chunk_count": total_chunk_count,
            },
        }

        try:
            init_resp = requests.post(init_url, headers=self.headers, json=init_payload)
            log.debug(init_resp.content)
            init_resp.raise_for_status()
            init_data = init_resp.json()

            if init_data.get("error", {}).get("code") != "ok":
                log.error(f"TikTok init error: {init_data.get('error')}")
                return None

            publish_id = init_data["data"]["publish_id"]
            upload_url = init_data["data"]["upload_url"]
        except Exception as e:
            log.error(f"Initialization failed: {str(e)}")
            return None

        try:
            with open(media_path, "rb") as video_file:
                for chunk_index in range(total_chunk_count):
                    start_byte = chunk_index * chunk_size

                    # For the last chunk, read all remaining bytes
                    if chunk_index == total_chunk_count - 1:
                        end_byte = video_size - 1
                        video_file.seek(start_byte)
                        chunk_data = video_file.read()  # Read all remaining bytes
                    else:
                        end_byte = min(start_byte + chunk_size - 1, video_size - 1)
                        video_file.seek(start_byte)
                        chunk_data = video_file.read(chunk_size)

                    actual_chunk_size = len(chunk_data)

                    log.info(
                        f"Uploading chunk {chunk_index+1}/{total_chunk_count}: bytes {start_byte}-{end_byte} (size: {actual_chunk_size})"
                    )

                    upload_headers = {
                        "Content-Type": "video/mp4",
                        "Content-Range": f"bytes {start_byte}-{end_byte}/{video_size}",
                        "Content-Length": str(actual_chunk_size),
                    }

                    upload_resp = requests.put(
                        upload_url, headers=upload_headers, data=chunk_data
                    )
                    log.debug(
                        f"Upload response: {upload_resp.status_code} - {upload_resp.content}"
                    )
                    upload_resp.raise_for_status()

                    # Check for expected response codes
                    if chunk_index == total_chunk_count - 1:
                        # Last chunk should return 201 (Created)
                        if upload_resp.status_code != 201:
                            log.warning(
                                f"Expected 201 for final chunk, got {upload_resp.status_code}"
                            )
                    else:
                        # Non-final chunks should return 206 (Partial Content)
                        if upload_resp.status_code != 206:
                            log.warning(
                                f"Expected 206 for chunk {chunk_index+1}, got {upload_resp.status_code}"
                            )

        except Exception as e:
            log.error(f"Video upload failed: {str(e)}")
            return None

        # Poll for status
        status_url = f"{self.base_url}/v2/post/publish/status/fetch/"
        status_payload = {"publish_id": publish_id}
        max_attempts = 60  # ~10 minutes at 10s intervals
        poll_interval = 10

        for attempt in range(max_attempts):
            time.sleep(poll_interval)

            try:
                status_resp = requests.post(
                    status_url, headers=self.headers, json=status_payload
                )
                log.debug(status_resp.content)
                status_resp.raise_for_status()
                status_data = status_resp.json()

                if status_data.get("error", {}).get("code") != "ok":
                    log.warning(f"Status check error: {status_data.get('error')}")
                    continue

                status = status_data["data"].get("status")
                log.info(f"Post status: {status} (attempt {attempt+1}/{max_attempts})")

                if status == "SUCCESS":
                    return status_data["data"].get("tiktok_url")
                elif status == "FAILED":
                    error_code = status_data["data"].get("fail_error_code")
                    error_msg = status_data["data"].get("fail_error_message")
                    log.error(f"Post failed: {error_code} - {error_msg}")
                    return None
            except Exception as e:
                log.warning(f"Status check failed: {str(e)}")
                continue

        log.error("Video processing timed out after 10 minutes")
        return None


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

    integration = await get_integration(account_id, Platform.TIKTOK.value)

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
