import os
import time
import math
import ffmpeg
import requests
from datetime import timedelta
from core.logger import log, send_notification
from dataclasses import dataclass
from integrations.models import IntegrationsModel, Platform
from socialsched.models import PostModel, TikTokPostModel
from asgiref.sync import sync_to_async
from .common import (
    get_integration,
    ErrorAccessTokenNotProvided,
)


@sync_to_async
def get_tiktok_settings(post_id: int, account_id: int):
    try:
        tiktok_settings = TikTokPostModel.objects.filter(
            post_id=post_id, account_id=account_id
        ).get()
        return tiktok_settings
    except Exception as err:
        log.exception(err)
        

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
        self.base_url = f"https://open.tiktokapis.com/{self.api_version}"
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json; charset=UTF-8",
        }

    def get_creator_info(self):
        """
        {
            "data": {
                "comment_disabled": False,
                "creator_avatar_url": "https://p16-pu-sign-no.tiktokcdn-eu.com/tos-no1a-avt-0068c001-no/2650bfd5f4c7d5a5e00b6b8286b61e34~tplv-tiktokx-cropcenter:168:168.webp?dr=10397&refresh_token=99543d33&x-expires=1749578400&x-signature=R4kvQrd0h1s0ey85%2Fz%2F0sZ89DTM%3D&t=4d5b0474&ps=13740610&shp=a5d48078&shcp=bbadf38d&idc=no1a",
                "creator_nickname": "developeralin",
                "creator_username": "developeralin",
                "duet_disabled": True,
                "max_video_post_duration_sec": 600,
                "privacy_level_options": [
                    "FOLLOWER_OF_CREATOR",
                    "MUTUAL_FOLLOW_FRIENDS",
                    "SELF_ONLY",
                ],
                "stitch_disabled": True,
            },
            "error": {
                "code": "ok",
                "message": "",
                "log_id": "2025060818142338D3DFB2A613ABF82FCF",
            },
        }
        """

        creator_info_url = f"{self.base_url}/post/publish/creator_info/query/"

        response = requests.post(creator_info_url, headers=self.headers)
        # log.debug(f"Tiktok creator info response: {response.json()}")
        response.raise_for_status()
        data = response.json()

        if data.get("error", {}).get("code") != "ok":
            error_msg = data.get("error", {}).get("message", "Unknown error")
            error_code = data.get("error", {}).get("code", "unknown")

            # Handle specific error cases
            if error_code == "spam_risk_too_many_posts":
                raise ValueError("Daily post limit reached. Please try again later.")
            elif error_code == "spam_risk_user_banned_from_posting":
                raise ValueError("User is banned from posting.")
            elif error_code == "reached_active_user_cap":
                raise ValueError("Daily quota for active users reached.")
            else:
                raise ValueError(f"Creator info error: {error_code} - {error_msg}")

        return data.get("data", {})

    def calculate_chunks(self, video_size: int):

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

    def get_video_duration(self, media_path: str) -> int:
        try:

            # Probe the video file to get metadata
            probe = ffmpeg.probe(media_path)

            # Try to get duration from format first (most reliable)
            if "format" in probe and "duration" in probe["format"]:
                duration = float(probe["format"]["duration"])
                return int(duration)

            # Fallback: get duration from video stream
            video_streams = [
                stream for stream in probe["streams"] if stream["codec_type"] == "video"
            ]

            if video_streams:
                video_stream = video_streams[0]  # Get first video stream

                if "duration" in video_stream:
                    duration = float(video_stream["duration"])
                    return int(duration)

                # Another fallback: calculate from duration_ts and time_base
                if "duration_ts" in video_stream and "time_base" in video_stream:
                    duration_ts = int(video_stream["duration_ts"])
                    time_base = video_stream["time_base"]

                    # Parse time_base fraction (e.g., "1/30000")
                    if "/" in time_base:
                        num, den = map(int, time_base.split("/"))
                        duration = (duration_ts * num) / den
                        return int(duration)

            raise ValueError("Could not determine video duration from metadata")

        except ffmpeg.Error as e:
            log.error(f"ffmpeg-python error: {e}")
            raise ValueError(f"Failed to analyze video file with ffmpeg: {e}")
        except (KeyError, ValueError, TypeError) as e:
            log.error(f"Failed to parse video metadata: {e}")
            raise ValueError(f"Invalid video file or corrupted metadata: {e}")

    async def initialize_upload(
        self, post_text: str, media_path: str, tiktok_settings: TikTokPostModel
    ):

        video_size = os.path.getsize(media_path)
        chunk_size, total_chunk_count = self.calculate_chunks(video_size)

        init_upload_response = requests.post(
            url=f"{self.base_url}/post/publish/video/init/",
            headers=self.headers,
            json={
                "post_info": {
                    "video_cover_timestamp_ms": 1000,
                    "title": post_text[:2200],
                    "privacy_level": tiktok_settings.privacy_level_options,
                    "disable_duet": not tiktok_settings.allow_duet,
                    "disable_comment": not tiktok_settings.allow_comment,
                    "disable_stitch": not tiktok_settings.allow_stitch,
                    "brand_content_toggle": tiktok_settings.branded_content,
                    "brand_organic_toggle": tiktok_settings.your_brand,
                    "is_aigc": tiktok_settings.ai_generated,
                },
                "source_info": {
                    "source": "FILE_UPLOAD",
                    "video_size": video_size,
                    "chunk_size": chunk_size,
                    "total_chunk_count": total_chunk_count,
                },
            },
        )
        # log.debug(init_upload_response.json())
        init_upload_response.raise_for_status()

        init_upload = init_upload_response.json()
        publish_id = init_upload["data"]["publish_id"]
        upload_url = init_upload["data"]["upload_url"]

        return publish_id, upload_url, video_size

    def upload_file(
        self,
        media_path: str,
        video_size: int,
        upload_url: str,
        publish_id: str,
        account_id: int,
    ):

        with open(media_path, "rb") as file:

            upload_response = requests.put(
                url=upload_url,
                headers={
                    "Content-Range": f"bytes 0-{video_size - 1}/{video_size}",
                    "Content-Type": "video/mp4",
                },
                data=file,
            )
            upload_response.raise_for_status()

        # 3600/5=720 - tiktok timeouts video upload after 1 hour
        for _ in range(720):
            time.sleep(5)

            upload_status_response = requests.post(
                url=f"{self.base_url}/post/publish/status/fetch/",
                headers=self.headers,
                json={"publish_id": publish_id},
            )
            log.debug(upload_status_response.json())
            upload_status_response.raise_for_status()
            upload_status = upload_status_response.json()["data"]["status"]

            if upload_status == "FAILED":
                upload_error = upload_status_response.json()["data"]["error"]["message"]
                raise Exception(
                    f"Failed to upload video on tiktok for AccountID: {account_id}. Got {upload_error}"
                )

            if upload_status == "PUBLISH_COMPLETE":
                break

        return upload_status

    async def make_post(self, account_id: int, post_text: str, media_path: str, tiktok_settings: TikTokPostModel):

        creator_info = self.get_creator_info()
        video_duration = self.get_video_duration(media_path)
        if video_duration > creator_info["max_video_post_duration_sec"]:
            raise ValueError(
                f"Maximum video duration allowed for account id: {account_id} is {creator_info['max_video_post_duration_sec']} seconds"
            )

        publish_id, upload_url, video_size = await self.initialize_upload(
            post_text, media_path, tiktok_settings
        )
        self.upload_file(media_path, video_size, upload_url, publish_id, account_id)

        return f"https://www.tiktok.com/@{creator_info['creator_nickname']}"


@sync_to_async
def update_tiktok_link(post_id: int, post_url: str, err: str):
    post = PostModel.objects.get(id=post_id)
    post.link_tiktok = post_url
    if err != "None":
        post.error_tiktok = err
        post.scheduled_on += timedelta(days=1)
        post.retries_tiktok += 1
        post.post_on_tiktok = True
    else:
        post.post_on_tiktok = False
        post.error_tiktok = None
    post.save(skip_validation=True)
    return post.retries_tiktok


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

            tiktok_settings = await get_tiktok_settings(post_id, account_id)
            if tiktok_settings is None:
                raise ValueError("Not posted because TikTok form was not completed.")

            poster = TikTokPoster(integration)
            post_url = await poster.make_post(account_id, post_text, media_path, tiktok_settings)
            
            log.success(f"TikTok post url: {integration.account_id} {post_url}")
        except Exception as e:
            err = e
            log.error(f"TikTok post error: {integration.account_id} {err}")
            log.exception(err)
            send_notification(
                "ImPosting", f"AccountId: {integration.account_id} got error {err}"
            )
    else:
        err = "(Re-)Authorize TikTok on Integrations page"

    retries_tiktok = await update_tiktok_link(post_id, post_url, str(err)[0:50])
    if retries_tiktok >= 10:
        await sync_to_async(integration.delete)()
