from social_django.models import UserSocialAuth


class SocialUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            user_social_auth = UserSocialAuth.objects.filter(user=request.user).first()
            request.social_user_id = user_social_auth.pk if user_social_auth else None
        else:
            request.social_user_id = None

        return self.get_response(request)
