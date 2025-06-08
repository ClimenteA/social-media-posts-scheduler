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
        log.debug(f"Tiktok creator info response: {response.json()}")
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

    def make_post(self):
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






# @dataclass
# class TikTokPoster:
#     integration: IntegrationsModel
#     api_version: str = "v2"
#     MIN_CHUNK_SIZE: int = 5 * 1024 * 1024  # 5 MB
#     MAX_CHUNK_SIZE: int = 64 * 1024 * 1024  # 64 MB
#     DEFAULT_CHUNK_SIZE: int = 10 * 1024 * 1024  # 10 MB (safe default)

#     def __post_init__(self):
#         self.access_token = self.integration.access_token_value
#         if not self.access_token:
#             raise ErrorAccessTokenNotProvided("TikTok access token missing.")
#         self.base_url = "https://open.tiktokapis.com"
#         self.headers = {
#             "Authorization": f"Bearer {self.access_token}",
#             "Content-Type": "application/json; charset=UTF-8",
#         }

#     def query_creator_info(self):
#         """Query creator info to get account details and permissions."""
#         creator_info_url = f"{self.base_url}/v2/post/publish/creator_info/query/"

#         try:
#             response = requests.post(creator_info_url, headers=self.headers)
#             log.debug(f"Creator info response: {response.content}")
#             response.raise_for_status()
#             data = response.json()

#             if data.get("error", {}).get("code") != "ok":
#                 error_msg = data.get("error", {}).get("message", "Unknown error")
#                 error_code = data.get("error", {}).get("code", "unknown")

#                 # Handle specific error cases
#                 if error_code == "spam_risk_too_many_posts":
#                     raise ValueError(
#                         "Daily post limit reached. Please try again later."
#                     )
#                 elif error_code == "spam_risk_user_banned_from_posting":
#                     raise ValueError("User is banned from posting.")
#                 elif error_code == "reached_active_user_cap":
#                     raise ValueError("Daily quota for active users reached.")
#                 else:
#                     raise ValueError(f"Creator info error: {error_code} - {error_msg}")

#             return data.get("data", {})

#         except requests.exceptions.RequestException as e:
#             log.error(f"Failed to query creator info: {str(e)}")
#             raise ValueError(f"Failed to fetch creator info: {str(e)}")

#     def _validate_user_inputs(
#         self,
#         creator_info: dict,
#         privacy_level: str,
#         video_duration: int,
#         allow_comment: bool,
#         allow_duet: bool,
#         allow_stitch: bool,
#         branded_content: bool,
#         your_brand: bool,
#     ):
#         """Validate user inputs against creator permissions."""

#         # Validate privacy level
#         available_privacy_options = creator_info.get("privacy_level_options", [])
#         if privacy_level not in available_privacy_options:
#             raise ValueError(
#                 f"Invalid privacy level. Available options: {available_privacy_options}"
#             )

#         # Validate video duration
#         max_duration = creator_info.get("max_video_post_duration_sec", 300)
#         if video_duration > max_duration:
#             raise ValueError(
#                 f"Video duration ({video_duration}s) exceeds maximum allowed ({max_duration}s)"
#             )

#         # Validate interaction settings based on creator permissions
#         if not allow_comment and creator_info.get("comment_disabled", False):
#             log.warning("Comments are disabled in creator settings")

#         if allow_duet and creator_info.get("duet_disabled", False):
#             raise ValueError("Duet is disabled in creator settings")

#         if allow_stitch and creator_info.get("stitch_disabled", False):
#             raise ValueError("Stitch is disabled in creator settings")

#         # Validate branded content privacy restrictions
#         if branded_content and privacy_level == "SELF_ONLY":
#             raise ValueError("Branded content cannot be set to private (SELF_ONLY)")

#     def get_video_duration(self, media_path: str) -> int:
#         """
#         Get video duration in seconds using ffmpeg-python.

#         Args:
#             media_path: Path to the video file

#         Returns:
#             int: Video duration in seconds

#         Raises:
#             ValueError: If unable to determine video duration
#         """
#         try:
#             import ffmpeg

#             # Probe the video file to get metadata
#             probe = ffmpeg.probe(media_path)

#             # Try to get duration from format first (most reliable)
#             if "format" in probe and "duration" in probe["format"]:
#                 duration = float(probe["format"]["duration"])
#                 return int(duration)

#             # Fallback: get duration from video stream
#             video_streams = [
#                 stream for stream in probe["streams"] if stream["codec_type"] == "video"
#             ]

#             if video_streams:
#                 video_stream = video_streams[0]  # Get first video stream

#                 if "duration" in video_stream:
#                     duration = float(video_stream["duration"])
#                     return int(duration)

#                 # Another fallback: calculate from duration_ts and time_base
#                 if "duration_ts" in video_stream and "time_base" in video_stream:
#                     duration_ts = int(video_stream["duration_ts"])
#                     time_base = video_stream["time_base"]

#                     # Parse time_base fraction (e.g., "1/30000")
#                     if "/" in time_base:
#                         num, den = map(int, time_base.split("/"))
#                         duration = (duration_ts * num) / den
#                         return int(duration)

#             raise ValueError("Could not determine video duration from metadata")

#         except ffmpeg.Error as e:
#             log.error(f"ffmpeg-python error: {e}")
#             raise ValueError(f"Failed to analyze video file with ffmpeg: {e}")
#         except (KeyError, ValueError, TypeError) as e:
#             log.error(f"Failed to parse video metadata: {e}")
#             raise ValueError(f"Invalid video file or corrupted metadata: {e}")
#         except ImportError:
#             log.error("ffmpeg-python not installed")
#             raise ValueError(
#                 "ffmpeg-python package is required. Install with: pip install ffmpeg-python"
#             )

#         # """Calculate proper chunk size and count according to TikTok's rules."""

#         # # If video is less than 5MB, upload as whole
#         # if video_size < self.MIN_CHUNK_SIZE:
#         #     return video_size, 1

#         # # If video is less than or equal to 64MB, upload as whole
#         # if video_size <= self.MAX_CHUNK_SIZE:
#         #     return video_size, 1

#         # # For larger videos, calculate chunks
#         # chunk_size = self.DEFAULT_CHUNK_SIZE
#         # total_chunk_count = math.ceil(video_size / chunk_size)

#         # # Ensure we don't exceed 1000 chunks limit
#         # if total_chunk_count > 1000:
#         #     chunk_size = math.ceil(video_size / 1000)
#         #     # Ensure chunk_size is at least 5MB
#         #     if chunk_size < self.MIN_CHUNK_SIZE:
#         #         chunk_size = self.MIN_CHUNK_SIZE
#         #     total_chunk_count = math.ceil(video_size / chunk_size)

#         # return chunk_size, total_chunk_count

#     def initialize_upload(
#         self,
#         title: str,
#         privacy_level: str,
#         video_size: int,
#         chunk_size: int,
#         total_chunk_count: int,
#         allow_comment: bool,
#         allow_duet: bool,
#         allow_stitch: bool,
#         branded_content: bool,
#         your_brand: bool,
#     ):

#         init_url = f"{self.base_url}/v2/post/publish/video/init/"

#         # Build post_info payload
#         post_info = {
#             "title": title[:2200],  # TikTok has a character limit
#             "privacy_level": privacy_level,
#             "disable_duet": not allow_duet,
#             "disable_comment": not allow_comment,
#             "disable_stitch": not allow_stitch,
#         }

#         # Add commercial content disclosure if applicable
#         if branded_content or your_brand:
#             brand_content_toggle = True
#             if branded_content and your_brand:
#                 brand_organic_toggle = True
#                 brand_content_toggle = True
#             elif your_brand:
#                 brand_organic_toggle = True
#                 brand_content_toggle = False
#             else:  # branded_content only
#                 brand_organic_toggle = False
#                 brand_content_toggle = True

#             post_info.update(
#                 {
#                     "brand_content_toggle": brand_content_toggle,
#                     "brand_organic_toggle": brand_organic_toggle,
#                 }
#             )

#         init_payload = {
#             "post_info": post_info,
#             "source_info": {
#                 "source": "FILE_UPLOAD",
#                 "video_size": video_size,
#                 "chunk_size": chunk_size,
#                 "total_chunk_count": total_chunk_count,
#             },
#         }

#         init_resp = requests.post(init_url, headers=self.headers, json=init_payload)
#         log.debug(init_resp.content)
#         init_resp.raise_for_status()
#         init_data = init_resp.json()

#         if init_data.get("error", {}).get("code") != "ok":
#             raise ValueError(f"TikTok init error: {init_data.get('error')}")

#         publish_id = init_data["data"]["publish_id"]
#         upload_url = init_data["data"]["upload_url"]

#         return publish_id, upload_url

#     def upload_in_chunks(
#         self,
#         upload_url: str,
#         media_path: str,
#         video_size: int,
#         chunk_size: int,
#         total_chunk_count: int,
#     ):

#         with open(media_path, "rb") as video_file:
#             for chunk_index in range(total_chunk_count):
#                 start_byte = chunk_index * chunk_size

#                 # For the last chunk, read all remaining bytes
#                 if chunk_index == total_chunk_count - 1:
#                     end_byte = video_size - 1
#                     video_file.seek(start_byte)
#                     chunk_data = video_file.read()  # Read all remaining bytes
#                 else:
#                     end_byte = min(start_byte + chunk_size - 1, video_size - 1)
#                     video_file.seek(start_byte)
#                     chunk_data = video_file.read(chunk_size)

#                 actual_chunk_size = len(chunk_data)

#                 log.info(
#                     f"Uploading chunk {chunk_index+1}/{total_chunk_count}: bytes {start_byte}-{end_byte} (size: {actual_chunk_size})"
#                 )

#                 upload_headers = {
#                     "Content-Type": "video/mp4",
#                     "Content-Range": f"bytes {start_byte}-{end_byte}/{video_size}",
#                     "Content-Length": str(actual_chunk_size),
#                 }

#                 upload_resp = requests.put(
#                     upload_url, headers=upload_headers, data=chunk_data
#                 )
#                 log.debug(
#                     f"Upload response: {upload_resp.status_code} - {upload_resp.content}"
#                 )
#                 upload_resp.raise_for_status()

#                 # Check for expected response codes
#                 if chunk_index == total_chunk_count - 1:
#                     # Last chunk should return 201 (Created)
#                     if upload_resp.status_code != 201:
#                         log.warning(
#                             f"Expected 201 for final chunk, got {upload_resp.status_code}"
#                         )
#                 else:
#                     # Non-final chunks should return 206 (Partial Content)
#                     if upload_resp.status_code != 206:
#                         log.warning(
#                             f"Expected 206 for chunk {chunk_index+1}, got {upload_resp.status_code}"
#                         )

#     def check_upload_status(self, publish_id: int):
#         """Check upload status and return TikTok URL when successful."""
#         status_url = f"{self.base_url}/v2/post/publish/status/fetch/"
#         status_payload = {"publish_id": publish_id}
#         max_attempts = 60  # ~10 minutes at 10s intervals
#         poll_interval = 10

#         for attempt in range(max_attempts):
#             time.sleep(poll_interval)

#             try:
#                 status_resp = requests.post(
#                     status_url, headers=self.headers, json=status_payload
#                 )
#                 log.debug(status_resp.content)
#                 status_resp.raise_for_status()
#                 status_data = status_resp.json()

#                 if status_data.get("error", {}).get("code") != "ok":
#                     log.warning(f"Status check error: {status_data.get('error')}")
#                     continue

#                 status = status_data["data"].get("status")
#                 log.info(f"Post status: {status} (attempt {attempt+1}/{max_attempts})")

#                 if status == "SUCCESS":
#                     tiktok_url = status_data["data"].get("tiktok_url")
#                     log.info(f"Video successfully uploaded: {tiktok_url}")
#                     return tiktok_url
#                 elif status == "FAILED":
#                     error_code = status_data["data"].get("fail_error_code")
#                     error_msg = status_data["data"].get("fail_error_message")
#                     log.error(f"Post failed: {error_code} - {error_msg}")
#                     raise ValueError(f"Upload failed: {error_code} - {error_msg}")
#             except Exception as e:
#                 log.warning(f"Status check failed: {str(e)}")
#                 continue

#         raise ValueError("Video processing timed out after 10 minutes")

#     def make_post(
#         self,
#         title: str,
#         media_path: str,
#         privacy_level: str,
#         allow_comment: bool = True,
#         allow_duet: bool = True,
#         allow_stitch: bool = True,
#         branded_content: bool = False,
#         your_brand: bool = False,
#     ):
#         """
#         Upload video to TikTok with user-specified metadata.

#         Args:
#             title: Video title/caption (required, user input)
#             media_path: Path to the video file (required)
#             privacy_level: Privacy setting (required, user must select from available options)
#             allow_comment: Whether to allow comments (user input, default True)
#             allow_duet: Whether to allow duets (user input, default True)
#             allow_stitch: Whether to allow stitches (user input, default True)
#             branded_content: Whether this is branded content (user input, default False)
#             your_brand: Whether this promotes your own brand (user input, default False)

#         Returns:
#             str: TikTok video URL if successful, None if failed
#         """

#         if not media_path or not media_path.lower().endswith(".mp4"):
#             log.info("Skipping TikTok post: Not a video or path is missing.")
#             return None

#         # Step 1: Query creator info to get permissions and validate inputs
#         log.info("Fetching creator information...")
#         creator_info = self.query_creator_info()

#         log.info(
#             f"Creator: {creator_info.get('creator_nickname')} (@{creator_info.get('creator_username')})"
#         )
#         log.info(
#             f"Available privacy options: {creator_info.get('privacy_level_options')}"
#         )

#         # Step 2: Get video duration and validate
#         log.info("Analyzing video duration...")
#         video_duration = self.get_video_duration(media_path)

#         # Step 3: Validate all user inputs against creator permissions
#         self._validate_user_inputs(
#             creator_info,
#             privacy_level,
#             video_duration,
#             allow_comment,
#             allow_duet,
#             allow_stitch,
#             branded_content,
#             your_brand,
#         )

#         # Step 4: Prepare video upload
#         video_size = os.path.getsize(media_path)
#         chunk_size, total_chunk_count = self._calculate_chunk_params(video_size)
#         log.info(
#             f"Video size: {video_size} bytes, Chunk size: {chunk_size} bytes, Total chunks: {total_chunk_count}"
#         )

#         # Step 5: Initialize upload with complete metadata
#         publish_id, upload_url = self.initialize_upload(
#             title,
#             privacy_level,
#             video_size,
#             chunk_size,
#             total_chunk_count,
#             allow_comment,
#             allow_duet,
#             allow_stitch,
#             branded_content,
#             your_brand,
#         )

#         # Step 6: Upload video in chunks
#         self.upload_in_chunks(
#             upload_url, media_path, video_size, chunk_size, total_chunk_count
#         )

#         # Step 7: Check status and get TikTok URL
#         tiktok_url = self.check_upload_status(publish_id)

#         return tiktok_url

#     def get_creator_info_for_ui(self):
#         """
#         Helper method to get creator info for UI rendering.
#         Returns creator info needed to build the posting interface.
#         """
#         return self.query_creator_info()
