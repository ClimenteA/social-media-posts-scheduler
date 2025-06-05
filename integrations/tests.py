import os
from django.test import TestCase
from integrations.models import IntegrationsModel, Platform
from integrations.platforms.xtwitter import XPoster


class QuestionModelTests(TestCase):

    def test_post_on_x(self):

        integration = IntegrationsModel(
            account_id = 1,
            user_id = os.getenv("x_user_id"),
            access_token = os.getenv("x_access_token"),
            refresh_token = os.getenv("x_refresh_token"),
            platform = Platform.X_TWITTER
        )

        poster = XPoster(integration)

        post_text = "Test"
        media_path = "static/calendar.png"

        self.assertTrue(os.path.exists(media_path))

        post_url = poster.make_post(post_text, media_path)

        self.assertIsNotNone(post_url)



