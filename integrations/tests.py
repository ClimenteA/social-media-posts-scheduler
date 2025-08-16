import os
import webbrowser
from core import settings
from django.test import TestCase
from integrations.models import IntegrationsModel, Platform
from integrations.platforms.xtwitter import XPoster
from integrations.platforms.facebook import FacebookPoster
from integrations.platforms.instagram import InstagramPoster
from integrations.platforms.linkedin import LinkedinPoster
from integrations.platforms.tiktok import TikTokPoster
from integrations.helpers.refresh_tokens import refresh_access_token_for_tiktok
from integrations.helpers.video_processor.make_video_postable import make_video_postable



class TestPostingOnSocials(TestCase):

    def test_post_text_with_image_on_x(self):
        # uv run python manage.py test integrations.tests.TestPostingOnSocials.test_post_text_with_image_on_x

        integration = IntegrationsModel(
            account_id=1,
            user_id=os.getenv("x_user_id"),
            access_token=os.getenv("x_access_token"),
            refresh_token=os.getenv("x_refresh_token"),
            platform=Platform.X_TWITTER,
        )

        poster = XPoster(integration)

        post_text = "Test"
        media_path = "static/profile_real_cartoon.jpg"

        post_url = poster.make_post(post_text, media_path)

        self.assertIsNotNone(post_url)

        webbrowser.open(post_url)

    def test_post_text_with_image_on_facebook(self):
        # uv run python manage.py test integrations.tests.TestPostingOnSocials.test_post_text_with_image_on_facebook

        integration = IntegrationsModel(
            account_id=1,
            user_id=os.getenv("facebook_user_id"),
            access_token=os.getenv("facebook_access_token"),
            refresh_token=os.getenv("facebook_refresh_token"),
            platform=Platform.FACEBOOK,
        )

        poster = FacebookPoster(integration)

        post_text = "Test"
        media_url = settings.APP_URL + "/static/profile_real_cartoon.jpg"

        post_url = poster.make_post(post_text, media_url)

        self.assertIsNotNone(post_url)

        webbrowser.open(post_url)

    def test_post_text_with_image_on_instagram(self):
        # uv run python manage.py test integrations.tests.TestPostingOnSocials.test_post_text_with_image_on_instagram

        integration = IntegrationsModel(
            account_id=1,
            user_id=os.getenv("instagram_user_id"),
            access_token=os.getenv("instagram_access_token"),
            refresh_token=os.getenv("instagram_refresh_token"),
            platform=Platform.INSTAGRAM,
        )

        poster = InstagramPoster(integration)

        post_text = "Test"
        media_url = settings.APP_URL + "/static/profile_real_cartoon.jpg"

        post_url = poster.make_post(post_text, media_url)

        self.assertIsNotNone(post_url)

        webbrowser.open(post_url)

    def test_post_text_with_image_on_linkedin(self):
        # uv run python manage.py test integrations.tests.TestPostingOnSocials.test_post_text_with_image_on_linkedin

        integration = IntegrationsModel(
            account_id=1,
            user_id=os.getenv("linkedin_user_id"),
            access_token=os.getenv("linkedin_access_token"),
            refresh_token=os.getenv("linkedin_refresh_token"),
            platform=Platform.LINKEDIN,
        )

        poster = LinkedinPoster(integration)

        post_text = "Test"
        media_path = "./static/profile_real_cartoon.jpg"

        post_url = poster.make_post(post_text, media_path)

        self.assertIsNotNone(post_url)

        webbrowser.open(post_url)

    def test_post_text_with_reel_on_facebook(self):
        # uv run python manage.py test integrations.tests.TestPostingOnSocials.test_post_text_with_reel_on_facebook

        integration = IntegrationsModel(
            account_id=1,
            user_id=os.getenv("facebook_user_id"),
            access_token=os.getenv("facebook_access_token"),
            refresh_token=os.getenv("facebook_refresh_token"),
            platform=Platform.FACEBOOK,
        )

        poster = FacebookPoster(integration)

        post_text = "Test"
        media_path = "./static/imposting-video-reel.mp4"
        # media_path = "/home/alinclimente/Videos/test-reel.mp4"

        post_url = poster.make_post(post_text, media_type="VIDEO", media_path=media_path)

        self.assertIsNotNone(post_url)

        webbrowser.open(post_url)


    def test_post_text_with_reel_on_instagram(self):
        # uv run python manage.py test integrations.tests.TestPostingOnSocials.test_post_text_with_reel_on_instagram

        integration = IntegrationsModel(
            account_id=1,
            user_id=os.getenv("instagram_user_id"),
            access_token=os.getenv("instagram_access_token"),
            refresh_token=os.getenv("instagram_refresh_token"),
            platform=Platform.INSTAGRAM,
        )

        poster = InstagramPoster(integration)

        post_text = "Test"
        media_path = "./static/imposting-video-reel.mp4"
        media_url = settings.APP_URL + "/static/imposting-video-reel.mp4"

        post_url = poster.make_post(post_text, media_url, media_path)

        self.assertIsNotNone(post_url)

        webbrowser.open(post_url)


    def test_get_tiktok_creator_info(self):
        # uv run python manage.py test integrations.tests.TestPostingOnSocials.test_get_tiktok_creator_info

        integration = IntegrationsModel(
            account_id=1,
            user_id=os.getenv("tiktok_user_id"),
            access_token=os.getenv("tiktok_access_token"),
            refresh_token=os.getenv("tiktok_refresh_token"),
            platform=Platform.TIKTOK,
        )

        poster = TikTokPoster(integration)

        creator_info = poster.get_creator_info()

        self.assertIsNotNone(creator_info)


    def test_post_text_with_reel_on_tiktok(self):
        # uv run python manage.py test integrations.tests.TestPostingOnSocials.test_post_text_with_reel_on_tiktok
        
        tiktok_settings = None

        integration = IntegrationsModel(
            account_id=tiktok_settings.account_id,
            user_id=os.getenv("tiktok_user_id"),
            access_token=os.getenv("tiktok_access_token"),
            refresh_token=os.getenv("tiktok_refresh_token"),
            platform=Platform.TIKTOK,
        )
        

        poster = TikTokPoster(integration)

        post_text = "Test"
        media_path = "./static/imposting-video-reel-tiktok.mp4"


        # video_duration = poster.get_video_duration(media_path)
        # print(video_duration)
        # assert video_duration

        post_url = poster.make_post(tiktok_settings.account_id, tiktok_settings.post_id, post_text, media_path)

        self.assertIsNotNone(post_url)

        webbrowser.open(post_url)


    def test_refresh_token_for_tiktok(self):
        # uv run python manage.py test integrations.tests.TestPostingOnSocials.test_refresh_token_for_tiktok

        integration = IntegrationsModel(
            account_id=1,
            user_id=os.getenv("tiktok_user_id"),
            access_token=os.getenv("tiktok_access_token"),
            refresh_token=os.getenv("tiktok_refresh_token"),
            platform=Platform.TIKTOK,
        )

        refresh_access_token_for_tiktok(integration)


    def test_make_video_postable(self):
        # uv run python manage.py test integrations.tests.TestPostingOnSocials.test_make_video_postable

        video_path = "./static/imposting-video.mp4"
        output_path = "./static/imposting-video-common.mp4"

        make_video_postable(video_path, output_path)

        

    # def test_make_reel_for_tiktok(self):
    #     # uv run python manage.py test integrations.tests.TestPostingOnSocials.test_make_reel_for_tiktok

    #     def calculate_target_resolution(width: int, height: int) -> Tuple[int, int]:
    #         """Calculate resolution that fits TikTok's 360-4096 range while maintaining aspect ratio"""
    #         aspect = width / height
    #         min_dim, max_dim = min(width, height), max(width, height)
            
    #         # Scale up if below minimum
    #         if min_dim < 360:
    #             scale_factor = 360 / min_dim
    #             new_min = 360
    #             new_max = min(round(max_dim * scale_factor), 4096)
    #         # Scale down if above maximum
    #         elif max_dim > 4096:
    #             scale_factor = 4096 / max_dim
    #             new_max = 4096
    #             new_min = max(round(min_dim * scale_factor), 360)
    #         else:
    #             return width, height
            
    #         # Return dimensions in original orientation
    #         return (new_min, new_max) if width < height else (new_max, new_min)

    #     def calculate_max_bitrate(duration: float, max_size_gb: float = 3.8) -> float:
    #         """
    #         Calculate maximum bitrate to stay under file size limit
    #         (with 200MB buffer for audio and metadata)
    #         """
    #         max_size_bytes = max_size_gb * 1024 * 1024 * 1024
    #         max_bitrate_bps = (max_size_bytes * 8) / duration
    #         return max(1000, min(50000, max_bitrate_bps / 1000))  # Between 1000-50000 kbps


    #     def convert_video_for_tiktok(input_path: str, output_path: str) -> None:
    #         # Probe the source video
    #         probe = ffmpeg.probe(input_path)
    #         video_stream = next((s for s in probe['streams'] if s['codec_type'] == 'video'), None)
    #         if not video_stream:
    #             raise ValueError("No video stream found in input file")
            
    #         # Get video properties
    #         width = int(video_stream['width'])
    #         height = int(video_stream['height'])
    #         duration = float(probe['format']['duration'])
    #         frame_rate = eval(video_stream['r_frame_rate'])  # Safe for fractions like 30000/1001
            
    #         # Calculate target resolution (maintain aspect ratio)
    #         target_width, target_height = calculate_target_resolution(width, height)
            
    #         # Calculate target framerate (clamped between 23-60 FPS)
    #         target_framerate = min(max(frame_rate, 23), 60)
            
    #         # Calculate target duration (max 10 minutes)
    #         target_duration = min(duration, 600)
            
    #         # Build FFmpeg command
    #         stream = ffmpeg.input(input_path)
            
    #         # Apply video filters
    #         stream = stream.filter(
    #             'scale', 
    #             width=target_width, 
    #             height=target_height,
    #             force_original_aspect_ratio='decrease'
    #         )
    #         stream = stream.filter('fps', fps=target_framerate, round='up')
            
    #         # Output configuration
    #         output_args = {
    #             'c:v': 'libx264',
    #             'pix_fmt': 'yuv420p',
    #             'preset': 'fast',
    #             'crf': '23',
    #             'c:a': 'aac',
    #             'b:a': '128k',
    #             't': str(target_duration),
    #             'f': 'mp4',
    #             'y': None  # Overwrite output
    #         }
            
    #         # Calculate target bitrate to stay under 4GB
    #         max_bitrate = calculate_max_bitrate(target_duration)
    #         if max_bitrate:
    #             output_args['b:v'] = f'{max_bitrate}k'
    #             output_args['maxrate'] = f'{max_bitrate}k'
    #             output_args['bufsize'] = f'{max_bitrate * 2}k'
            
    #         # Run conversion
    #         stream.output(output_path, **output_args).run(overwrite_output=True)


    #     input_path = "./static/imposting-video.mp4"
    #     output_path = "./static/imposting-video-reel-tiktok.mp4"

    #     convert_video_for_tiktok(input_path, output_path)


    # def test_video_convert_to_reel(self):
    #     # uv run python manage.py test integrations.tests.TestPostingOnSocials.test_video_convert_to_reel

    #     # all should be 60 seconds 1 minute max

    #     def convert_to_reel_format(
    #         input_path: str, output_path: str, duration_limit: int = 60
    #     ):
    #         probe = ffmpeg.probe(input_path)
    #         video_stream = next(
    #             (
    #                 stream
    #                 for stream in probe["streams"]
    #                 if stream["codec_type"] == "video"
    #             ),
    #             None,
    #         )

    #         if not video_stream:
    #             raise ValueError("No video stream found")

    #         # Resize video to 1080x1920 and enforce duration cap
    #         stream = (
    #             ffmpeg.input(input_path, ss=0, t=duration_limit)
    #             .filter("scale", 1080, 1920)
    #             .output(
    #                 output_path,
    #                 vcodec="libx264",
    #                 acodec="aac",
    #                 video_bitrate="5000k",
    #                 audio_bitrate="128k",
    #                 ac=2,
    #                 ar=48000,
    #                 pix_fmt="yuv420p",
    #                 r=30,
    #                 movflags="+faststart",
    #                 g=60,
    #                 preset="medium",
    #                 format="mp4",
    #             )
    #             .overwrite_output()
    #         )

    #         ffmpeg.run(stream)

    #     input_path = "./static/imposting-video.mp4"
    #     output_path = "./static/imposting-video-reel.mp4"

    #     convert_to_reel_format(input_path, output_path, duration_limit=60)
