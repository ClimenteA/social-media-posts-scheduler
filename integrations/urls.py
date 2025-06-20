from django.urls import path
from . import views


urlpatterns = [
    path("integrations/", views.integrations_form, name="integrations"),
    path('linkedin/login/', views.linkedin_login, name='linkedin_login'),
    path('linkedin/callback/', views.linkedin_callback, name='linkedin_callback'),
    path('linkedin/uninstall/', views.linkedin_uninstall, name='linkedin_uninstall'),
    path('X/login/', views.x_login, name='x_login'),
    path('X/callback/', views.x_callback, name='x_callback'),
    path('X/uninstall/', views.x_uninstall, name='x_uninstall'),
    path('facebook/login/', views.facebook_login, name='facebook_login'),
    path('facebook/callback/', views.facebook_callback, name='facebook_callback'),
    path('facebook/uninstall/', views.facebook_uninstall, name='facebook_uninstall'),
    path('tiktok/login/', views.tiktok_login, name='tiktok_login'),
    path('tiktok/callback/', views.tiktok_callback, name='tiktok_callback'),
    path('tiktok/uninstall/', views.tiktok_uninstall, name='tiktok_uninstall'),
    path('proxy-media-file/<str:filename>', views.proxy_media_file, name='proxy_media_file'),
]
