import os
import uuid
import requests
from core import settings
from core.logger import log
from requests_oauthlib import OAuth2Session
from urllib.parse import urlencode
from django.http import FileResponse, Http404
from django.utils import timezone
from django.contrib import messages
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from social_django.models import UserSocialAuth
from .models import IntegrationsModel, Platform
from .helpers.utils import image_url_to_base64


@login_required
def integrations_form(request):
    user_social_auth = UserSocialAuth.objects.filter(user=request.user).first()
    social_uid = user_social_auth.pk

    linkedin_integration = IntegrationsModel.objects.filter(
        account_id=social_uid, platform=Platform.LINKEDIN.value
    ).first()
    linkedin_ok = bool(linkedin_integration)

    x_integration = IntegrationsModel.objects.filter(
        account_id=social_uid, platform=Platform.X_TWITTER.value
    ).first()
    x_ok = bool(x_integration)

    tiktok_integration = IntegrationsModel.objects.filter(
        account_id=social_uid, platform=Platform.TIKTOK.value
    ).first()
    tiktok_ok = bool(tiktok_integration)

    facebook_integration = IntegrationsModel.objects.filter(
        account_id=social_uid, platform=Platform.FACEBOOK.value
    ).first()
    facebook_ok = bool(facebook_integration)

    instagram_integration = IntegrationsModel.objects.filter(
        account_id=social_uid, platform=Platform.INSTAGRAM.value
    ).first()
    instagram_ok = bool(instagram_integration)

    x_expire = None
    if x_integration:
        if x_integration.access_expire:
            x_expire = x_integration.access_expire.date()

    tiktok_expire = None
    if tiktok_integration:
        if tiktok_integration.access_expire:
            tiktok_expire = tiktok_integration.access_expire.date()

    linkedin_expire = None
    if linkedin_integration:
        if linkedin_integration.access_expire:
            linkedin_expire = linkedin_integration.access_expire.date()

    facebook_expire = None
    if facebook_integration:
        if facebook_integration.access_expire:
            facebook_expire = facebook_integration.access_expire.date()

    return render(
        request,
        "integrations.html",
        context={
            "linkedin_avatar_url": (
                image_url_to_base64(linkedin_integration.avatar.url)
                if linkedin_integration
                else None
            ),
            "linkedin_username": (
                linkedin_integration.username if linkedin_integration else None
            ),
            "x_avatar_url": (
                image_url_to_base64(x_integration.avatar.url) if x_integration else None
            ),
            "x_username": x_integration.username if x_integration else None,
            "tiktok_avatar_url": (
                image_url_to_base64(tiktok_integration.avatar.url)
                if tiktok_integration
                else None
            ),
            "tiktok_username": (
                tiktok_integration.username if tiktok_integration else None
            ),
            "facebook_avatar_url": (
                image_url_to_base64(facebook_integration.avatar.url)
                if facebook_integration
                else None
            ),
            "facebook_username": (
                facebook_integration.username if facebook_integration else None
            ),
            "instagram_avatar_url": (
                image_url_to_base64(instagram_integration.avatar.url)
                if instagram_integration
                else None
            ),
            "instagram_username": (
                instagram_integration.username if instagram_integration else None
            ),
            "x_ok": x_ok,
            "linkedin_ok": linkedin_ok,
            "instagram_ok": facebook_ok,
            "meta_ok": facebook_ok and instagram_ok,
            "tiktok_ok": tiktok_ok,
            "x_expire": x_expire,
            "linkedin_expire": linkedin_expire,
            "meta_expire": facebook_expire,
            "tiktok_expire": tiktok_expire,
        },
    )


@login_required
def linkedin_login(request):
    linkedin_auth_url = (
        "https://www.linkedin.com/oauth/v2/authorization"
        "?response_type=code"
        f"&client_id={settings.LINKEDIN_CLIENT_ID}"
        f"&redirect_uri={settings.LINKEDIN_REDIRECT_URI}"
        "&scope=w_member_social openid profile email"
    )
    return redirect(linkedin_auth_url)


@login_required
def linkedin_callback(request):
    # Refresh tokens are only for approved Marketing Developer Platform (MDP) partners
    # https://learn.microsoft.com/en-us/linkedin/shared/authentication/programmatic-refresh-tokens
    user_social_auth = UserSocialAuth.objects.filter(user=request.user).first()
    social_uid = user_social_auth.pk

    code = request.GET.get("code")
    if not code:
        messages.error(request, "LinkedIn authorization failed: No code returned.")
        return redirect("/integrations/")

    token_url = "https://www.linkedin.com/oauth/v2/accessToken"
    token_data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": settings.LINKEDIN_REDIRECT_URI,
        "client_id": settings.LINKEDIN_CLIENT_ID,
        "client_secret": settings.LINKEDIN_CLIENT_SECRET,
    }
    token_headers = {"Content-Type": "application/x-www-form-urlencoded"}
    response = requests.post(token_url, data=token_data, headers=token_headers)
    response.raise_for_status()
    token_json = response.json()

    access_token = token_json["access_token"]
    access_token_expires_in = token_json["expires_in"]
    access_token_expire = timezone.now() + timezone.timedelta(
        seconds=access_token_expires_in - 900
    )

    # Get LinkedIn user info (sub is the unique user ID)
    user_info_url = "https://api.linkedin.com/v2/userinfo"
    headers = {
        "Authorization": f"Bearer {access_token}",
    }
    response = requests.get(user_info_url, headers=headers)
    response.raise_for_status()
    user_info = response.json()
    user_id = user_info.get("sub")
    username = user_info.get("name")
    avatar_url = user_info.get("picture")

    # Save Linkedin
    IntegrationsModel.objects.filter(
        account_id=social_uid, platform=Platform.LINKEDIN.value
    ).delete()

    IntegrationsModel.objects.create(
        account_id=social_uid,
        user_id=user_id,
        access_token=access_token,
        access_expire=access_token_expire,
        platform=Platform.LINKEDIN.value,
        username=username,
        avatar_url=avatar_url,
    )

    messages.success(
        request,
        "Successfully logged into LinkedIn! Now the app can make posts on your behalf.",
        extra_tags="✅ Success!",
    )

    return redirect("/integrations/")


@login_required
def linkedin_uninstall(request):
    user_social_auth = UserSocialAuth.objects.filter(user=request.user).first()
    social_uid = user_social_auth.pk

    IntegrationsModel.objects.filter(
        account_id=social_uid, platform=Platform.LINKEDIN.value
    ).delete()

    messages.add_message(
        request,
        messages.SUCCESS,
        "Deleted the access token.",
        extra_tags="✅ Success!",
    )

    return redirect("/integrations/")


@login_required
def x_login(request):
    x_auth_url = (
        "https://x.com/i/oauth2/authorize"
        "?response_type=code"
        f"&client_id={settings.X_CLIENT_ID}"
        f"&redirect_uri={settings.X_REDIRECT_URI}"
        "&scope=tweet.read tweet.write users.read media.write offline.access"
        f"&state={uuid.uuid4().hex}"
        "&code_challenge=challenge"
        "&code_challenge_method=plain"
    )
    return redirect(x_auth_url)


@login_required
def x_callback(request):
    user_social_auth = UserSocialAuth.objects.filter(user=request.user).first()
    social_uid = user_social_auth.pk

    code = request.GET.get("code")
    if not code:
        raise Exception("Could not get the code from previous call.")

    oauth = OAuth2Session(
        client_id=settings.X_CLIENT_ID, redirect_uri=settings.X_REDIRECT_URI
    )

    token = oauth.fetch_token(
        "https://api.x.com/2/oauth2/token",
        code=code,
        client_secret=settings.X_CLIENT_SECRET,
        code_verifier="challenge",
        include_client_id=True,
        auth=(
            settings.X_CLIENT_ID,
            settings.X_CLIENT_SECRET,
        ),
    )

    user_info = oauth.get("https://api.x.com/2/users/me").json()
    user_id = user_info["data"]["id"]
    username = user_info["data"]["username"]

    response = requests.get(
        url=f"https://api.twitter.com/2/users/by/username/{username}",
        headers={"Authorization": f"Bearer {token['access_token']}"},
        params={"user.fields": "profile_image_url"},
    )
    response.raise_for_status()

    avatar_url = response.json()["data"]["profile_image_url"]

    access_expire = timezone.now() + timezone.timedelta(
        seconds=token["expires_in"] - 900
    )

    # Save X
    IntegrationsModel.objects.filter(
        account_id=social_uid, platform=Platform.X_TWITTER.value
    ).delete()

    IntegrationsModel.objects.create(
        account_id=social_uid,
        user_id=user_id,
        access_token=token["access_token"],
        refresh_token=token["refresh_token"],
        access_expire=access_expire,
        platform=Platform.X_TWITTER.value,
        username=username,
        avatar_url=avatar_url,
    )

    messages.add_message(
        request,
        messages.SUCCESS,
        "Successfully logged into X! Now the app can make posts on your behalf.",
        extra_tags="✅ Success!",
    )

    return redirect("/integrations/")


@login_required
def x_uninstall(request):
    user_social_auth = UserSocialAuth.objects.filter(user=request.user).first()
    social_uid = user_social_auth.pk

    IntegrationsModel.objects.filter(
        account_id=social_uid, platform=Platform.X_TWITTER.value
    ).delete()

    messages.add_message(
        request,
        messages.SUCCESS,
        "Deleted the access token.",
        extra_tags="✅ Success!",
    )

    return redirect("/integrations/")


@login_required
def facebook_login(request):
    fb_login_url = (
        "https://www.facebook.com/v23.0/dialog/oauth"
        "?response_type=code"
        f"&client_id={settings.FACEBOOK_CLIENT_ID}"
        f"&redirect_uri={settings.FACEBOOK_REDIRECT_URI}"
        "&scope=email,public_profile,pages_show_list,pages_manage_posts,instagram_basic,instagram_content_publish,business_management"
    )
    return redirect(fb_login_url)


@login_required
def facebook_callback(request):
    user_social_auth = UserSocialAuth.objects.filter(user=request.user).first()
    social_uid = user_social_auth.pk

    code = request.GET.get("code")
    if not code:
        raise Exception("Could not get the code from the previous call")

    # Exchange code for access token
    response = requests.post(
        url="https://graph.facebook.com/v23.0/oauth/access_token",
        data={
            "client_id": settings.FACEBOOK_CLIENT_ID,
            "client_secret": settings.FACEBOOK_CLIENT_SECRET,
            "code": code,
            "redirect_uri": settings.FACEBOOK_REDIRECT_URI,
            "grant_type": "authorization_code",
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    response.raise_for_status()

    short_token = response.json().get("access_token")

    # Exchange short-lived token for long-lived token
    response = requests.get(
        url="https://graph.facebook.com/v23.0/oauth/access_token",
        params={
            "grant_type": "fb_exchange_token",
            "client_id": settings.FACEBOOK_CLIENT_ID,
            "client_secret": settings.FACEBOOK_CLIENT_SECRET,
            "fb_exchange_token": short_token,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    response.raise_for_status()

    token_data = response.json()
    access_token = token_data["access_token"]

    # Retrieve user ID using the Graph API directly
    user_info_url = "https://graph.facebook.com/v23.0/me"
    user_info_params = {"access_token": access_token, "fields": "id"}
    user_info_response = requests.get(user_info_url, params=user_info_params)
    user_info_response.raise_for_status()
    user_data = user_info_response.json()
    user_id = user_data.get("id")

    # Retrieve pages associated with the user
    response_pages = requests.get(
        url=f"https://graph.facebook.com/v23.0/{user_id}/accounts",
        params={"access_token": access_token},
    )
    response_pages.raise_for_status()

    response_data = response_pages.json()
    pages_data = response_data["data"]
    page = pages_data[0]
    page_id = page["id"]
    page_access_token = page["access_token"]
    page_access_token_expire = timezone.now() + timezone.timedelta(days=60)

    # Get Facebook Page details (username and avatar_url)
    fb_page_details_response = requests.get(
        url=f"https://graph.facebook.com/v23.0/{page_id}",
        params={"access_token": page_access_token, "fields": "name,picture{url}"},
    )
    fb_page_details_response.raise_for_status()
    fb_page_data = fb_page_details_response.json()
    fb_username = fb_page_data.get("name")
    fb_avatar_url = fb_page_data.get("picture", {}).get("data", {}).get("url")

    # Retrieve Instagram accounts linked to the page
    response_instagram = requests.get(
        url=f"https://graph.facebook.com/v23.0/{page_id}/instagram_accounts",
        params={"access_token": page_access_token},
    )
    response_instagram.raise_for_status()

    instagram_user_id = response_instagram.json()["data"][0]["id"]

    # Get Instagram Business Account details (username and avatar_url)
    ig_details_response = requests.get(
        url=f"https://graph.facebook.com/v22.0/{instagram_user_id}",
        params={
            "access_token": page_access_token,
            "fields": "username,profile_picture_url",
        },
    )
    ig_details_response.raise_for_status()
    ig_data = ig_details_response.json()
    ig_username = ig_data.get("username")
    ig_avatar_url = ig_data.get("profile_picture_url")

    # Save Facebook
    IntegrationsModel.objects.filter(
        account_id=social_uid, platform=Platform.FACEBOOK.value
    ).delete()

    IntegrationsModel.objects.create(
        account_id=social_uid,
        user_id=page_id,
        access_token=page_access_token,
        access_expire=page_access_token_expire,
        platform=Platform.FACEBOOK.value,
        username=fb_username,
        avatar_url=fb_avatar_url,
    )

    # Save Instagram
    IntegrationsModel.objects.filter(
        account_id=social_uid, platform=Platform.INSTAGRAM.value
    ).delete()

    IntegrationsModel.objects.create(
        account_id=social_uid,
        user_id=instagram_user_id,
        access_token=page_access_token,
        access_expire=page_access_token_expire,
        platform=Platform.INSTAGRAM.value,
        username=ig_username,
        avatar_url=ig_avatar_url,
    )

    messages.add_message(
        request,
        messages.SUCCESS,
        "Successfully logged into Facebook and Instagram! Now the app can make posts on your behalf.",
        extra_tags="✅ Success!",
    )

    return redirect("/integrations/")


@login_required
def facebook_uninstall(request):
    user_social_auth = UserSocialAuth.objects.filter(user=request.user).first()
    social_uid = user_social_auth.pk

    IntegrationsModel.objects.filter(
        account_id=social_uid, platform=Platform.FACEBOOK.value
    ).delete()

    IntegrationsModel.objects.filter(
        account_id=social_uid, platform=Platform.INSTAGRAM.value
    ).delete()

    messages.add_message(
        request,
        messages.SUCCESS,
        "Deleted the access tokens.",
        extra_tags="✅ Success!",
    )

    return redirect("/integrations/")


@login_required
def tiktok_login(request):
    params = {
        "client_key": settings.TIKTOK_CLIENT_ID,
        "response_type": "code",
        "scope": "user.info.basic,video.publish,video.list",
        "redirect_uri": settings.TIKTOK_REDIRECT_URI,
        "state": uuid.uuid4().hex,
    }
    tiktok_login_url = f"https://www.tiktok.com/v2/auth/authorize/?{urlencode(params)}"
    return redirect(tiktok_login_url)


@login_required
def tiktok_callback(request):
    user_social_auth = UserSocialAuth.objects.filter(user=request.user).first()
    social_uid = user_social_auth.pk

    code = request.GET.get("code")
    error = request.GET.get("error")

    if error:
        messages.error(request, "TikTok authorization failed.")
        return redirect("/integrations/")

    # Exchange authorization code for access/refresh tokens
    token_url = "https://open.tiktokapis.com/v2/oauth/token/"
    data = {
        "client_key": settings.TIKTOK_CLIENT_ID,
        "client_secret": settings.TIKTOK_CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": settings.TIKTOK_REDIRECT_URI,
    }

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
    }

    resp = requests.post(token_url, data=data, headers=headers)
    if resp.status_code != 200:
        log.error(resp.content)
        messages.error(request, "Failed to fetch tokens from TikTok.")
        return redirect("/integrations/")

    token_data = resp.json()

    # Fetch TikTok user info (username and avatar)
    user_info_resp = requests.get(
        url="https://open.tiktokapis.com/v2/user/info/",
        headers={
            "Authorization": f"Bearer {token_data['access_token']}",
        },
        params={"fields": "display_name,avatar_url"},
    )
    user_info_resp.raise_for_status()

    user_info = user_info_resp.json().get("data", {}).get("user", {})
    username = user_info.get("display_name")
    avatar_url = user_info.get("avatar_url")

    IntegrationsModel.objects.filter(
        account_id=social_uid, platform=Platform.TIKTOK.value
    ).delete()

    IntegrationsModel.objects.create(
        account_id=social_uid,
        user_id=token_data["open_id"],
        access_token=token_data["access_token"],
        refresh_token=token_data["refresh_token"],
        access_expire=timezone.now()
        + timezone.timedelta(seconds=token_data["expires_in"]),
        refresh_expire=timezone.now()
        + timezone.timedelta(seconds=token_data["refresh_expires_in"]),
        platform=Platform.TIKTOK.value,
        username=username,
        avatar_url=avatar_url,
    )

    messages.success(
        request,
        "Successfully logged into TikTok! Now the app can make posts on your behalf.",
        extra_tags="✅ Success!",
    )

    return redirect("/integrations/")


@login_required
def tiktok_uninstall(request):
    user_social_auth = UserSocialAuth.objects.filter(user=request.user).first()
    social_uid = user_social_auth.pk

    IntegrationsModel.objects.filter(
        account_id=social_uid, platform=Platform.TIKTOK.value
    ).delete()

    messages.add_message(
        request,
        messages.SUCCESS,
        "Deleted the tokens.",
        extra_tags="✅ Success!",
    )

    return redirect("/integrations/")


def proxy_media_file(request, filename: str):
    filepath = f"/tmp/{filename}"

    if not os.path.isfile(filepath):
        raise Http404("File not found.")

    return FileResponse(open(filepath, "rb"), as_attachment=False)
