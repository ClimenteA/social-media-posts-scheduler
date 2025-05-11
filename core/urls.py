import time
from django.contrib import admin
from django.urls import path, include
from django.contrib.sitemaps.views import sitemap
from .settings import MEDIA_URL, MEDIA_ROOT
from django.conf.urls.static import static
from socialsched.urls import LoginSitemap
from django.http import StreamingHttpResponse
from django.http import HttpResponse
from social_django.models import UserSocialAuth
from webpush import send_user_notification


# def sse_view(request):

#     social_uid = "anonymous"
#     if request.user:
#         if request.user.is_authenticated:
#             user_social_auth = UserSocialAuth.objects.filter(user=request.user).first()
#             social_uid = user_social_auth.uid

#     def event_stream():
#         while True:

#             payload = {"head": "Welcome!", "body": "Hello World"}

#             send_user_notification(user=request.user, payload=payload, ttl=1000)

#             yield f"data: Your social UID is {social_uid}\n\n"
#             time.sleep(5)  # simulate periodic events

#     response = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
#     response["Cache-Control"] = "no-cache"
#     return response


def robots_txt(request):
    content = "User-agent: *\nDisallow:"
    return HttpResponse(content, content_type="text/plain")


sitemaps = {
    "sitemaps": {
        "login": LoginSitemap(),
    }
}


urlpatterns = [
    path("", include("socialsched.urls")),
    path("", include("integrations.urls")),
    path("robots.txt", robots_txt),
    path(
        "sitemap.xml",
        sitemap,
        sitemaps,
        name="django.contrib.sitemaps.views.sitemap",
    ),
    path("webpush/", include("webpush.urls")),
    path("admin/", admin.site.urls),
    path("", include("social_django.urls", namespace="social")),
    path("__reload__/", include("django_browser_reload.urls")),
]

urlpatterns += static(MEDIA_URL, document_root=MEDIA_ROOT)
