import os
import webbrowser
from core import settings
from django.test import TestCase
from integrations.models import IntegrationsModel, Platform
from integrations.platforms.xtwitter import XPoster
from integrations.platforms.facebook import FacebookPoster
from integrations.platforms.instagram import InstagramPoster
from integrations.platforms.linkedin import LinkedinPoster


class TestPostingOnSocials(TestCase):

    def test_post_on_x(self):
        # uv run python manage.py test integrations.tests.TestPostingOnSocials.test_post_on_x

        integration = IntegrationsModel(
            account_id = 1,
            user_id = os.getenv("x_user_id"),
            access_token = os.getenv("x_access_token"),
            refresh_token = os.getenv("x_refresh_token"),
            platform = Platform.X_TWITTER
        )

        poster = XPoster(integration)

        post_text = "Test"
        media_path = "static/profile_real_cartoon.jpg"

        post_url = poster.make_post(post_text, media_path)

        self.assertIsNotNone(post_url)

        webbrowser.open(post_url)



    def test_post_on_facebook(self):
        # uv run python manage.py test integrations.tests.TestPostingOnSocials.test_post_on_facebook

        integration = IntegrationsModel(
            account_id = 1,
            user_id = os.getenv("facebook_user_id"),
            access_token = os.getenv("facebook_access_token"),
            refresh_token = os.getenv("facebook_refresh_token"),
            platform = Platform.FACEBOOK
        )

        poster = FacebookPoster(integration)

        post_text = "Test"
        media_url = settings.APP_URL + "/static/profile_real_cartoon.jpg"

        post_url = poster.make_post(post_text, media_url)

        self.assertIsNotNone(post_url)

        webbrowser.open(post_url)


    def test_post_on_instagram(self):
        # uv run python manage.py test integrations.tests.TestPostingOnSocials.test_post_on_instagram

        integration = IntegrationsModel(
            account_id = 1,
            user_id = os.getenv("instagram_user_id"),
            access_token = os.getenv("instagram_access_token"),
            refresh_token = os.getenv("instagram_refresh_token"),
            platform = Platform.INSTAGRAM
        )

        poster = InstagramPoster(integration)

        post_text = "Test"
        media_url = settings.APP_URL + "/static/profile_real_cartoon.jpg"

        post_url = poster.make_post(post_text, media_url)

        self.assertIsNotNone(post_url)

        webbrowser.open(post_url)


    def test_post_on_linkedin(self):
        # uv run python manage.py test integrations.tests.TestPostingOnSocials.test_post_on_linkedin

        integration = IntegrationsModel(
            account_id = 1,
            user_id = os.getenv("linkedin_user_id"),
            access_token = os.getenv("linkedin_access_token"),
            refresh_token = os.getenv("linkedin_refresh_token"),
            platform = Platform.LINKEDIN
        )

        poster = LinkedinPoster(integration)

        post_text = "Test"
        media_path = "./static/profile_real_cartoon.jpg"

        post_url = poster.make_post(post_text, media_path)

        self.assertIsNotNone(post_url)

        webbrowser.open(post_url)
