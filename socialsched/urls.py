from django.urls import path
from django.urls import reverse
from django.contrib.sitemaps import Sitemap
from . import views


class LoginSitemap(Sitemap):
    changefreq = "monthly"
    priority = 1

    def items(self):
        return ["login"]

    def location(self, item):
        return reverse(item)


urlpatterns = [
    path("", views.calendar, name="calendar"),
    path("schedule/<str:isodate>/", views.schedule_form, name="schedule_form"),
    path("schedule-save/<str:isodate>/", views.schedule_save, name="schedule_save"),
    path(
        "schedule-delete/<int:post_id>/", views.schedule_delete, name="schedule_delete"
    ),
    path("login/", views.login_user, name="login"),
    path("logout/", views.logout_user, name="logout"),
    path("legal/", views.legal, name="legal"),
]
