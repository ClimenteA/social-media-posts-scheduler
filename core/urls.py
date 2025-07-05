from django.contrib import admin
from django.urls import path, include
from django.contrib.sitemaps.views import sitemap
from django.http import HttpResponse
from django.urls import reverse
from django.contrib.sitemaps import Sitemap
from socialsched.views import articles


def robots_txt(request):
    content = "User-agent: *\nDisallow:"
    return HttpResponse(content, content_type="text/plain")


class MainViewSitemap(Sitemap):
    changefreq = "monthly"
    priority = 1

    def items(self):
        return ["login", "blog_articles"]

    def location(self, item):
        return reverse(item)


class BlogSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.9

    def items(self):
        return list(articles.keys())

    def location(self, slug):
        return reverse("blog_article", kwargs={"blog_slug": slug})


sitemaps = {
    "static": MainViewSitemap,
    "blog": BlogSitemap,
}


urlpatterns = [
    path(
        "sitemap.xml",
        sitemap,
        {"sitemaps": sitemaps},
        name="django.contrib.sitemaps.views.sitemap",
    ),
    path("", include("socialsched.urls")),
    path("", include("integrations.urls")),
    path("robots.txt", robots_txt),
    path("admin/", admin.site.urls),
    path("", include("social_django.urls", namespace="social")),
    path("__reload__/", include("django_browser_reload.urls")),
]
