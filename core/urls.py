from django.contrib import admin
from django.urls import path, include
from django.contrib.sitemaps.views import sitemap
from socialsched.urls import LoginSitemap
from django.http import HttpResponse


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
    path("admin/", admin.site.urls),
    path("", include("social_django.urls", namespace="social")),
    path("__reload__/", include("django_browser_reload.urls")),
]
