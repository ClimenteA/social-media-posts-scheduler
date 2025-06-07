import os
import ffmpeg
import webbrowser
from core import settings
from django.test import TestCase
from integrations.models import IntegrationsModel, Platform
from integrations.platforms.xtwitter import XPoster
from integrations.platforms.facebook import FacebookPoster
from integrations.platforms.instagram import InstagramPoster
from integrations.platforms.linkedin import LinkedinPoster


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

        post_url = poster.make_post(post_text, media_path=media_path)

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
