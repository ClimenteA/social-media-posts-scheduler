import uuid
import requests
from requests_oauthlib import OAuth2Session
from core.settings import log
from core import settings
from django.contrib import messages
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from .models import IntegrationsModel, Platform


@login_required
async def integrations_form(request):

    linkedin_ok = bool(
        IntegrationsModel.objects.filter(
            account_id=request.user.id, platform=Platform.LINKEDIN.value
        ).first()
    )
    x_ok = bool(
        IntegrationsModel.objects.filter(
            account_id=request.user.id, platform=Platform.X_TWITTER.value
        ).first()
    )
    instagram_ok = bool(
        IntegrationsModel.objects.filter(
            account_id=request.user.id, platform=Platform.INSTAGRAM.value
        ).first()
    )
    facebook_ok = bool(
        IntegrationsModel.objects.filter(
            account_id=request.user.id, platform=Platform.FACEBOOK.value
        ).first()
    )

    return render(
        request,
        "integrations.html",
        context={
            "x_ok": x_ok,
            "linkedin_ok": linkedin_ok,
            "instagram_ok": instagram_ok and facebook_ok,
            "facebook_ok": facebook_ok and instagram_ok,
            "x_redirect_url": settings.X_REDIRECT_URI,
            "x_uninstall_url": settings.X_UNINSTALL_URI,
            "linkedin_redirect_url": settings.LINKEDIN_REDIRECT_URI,
            "linkedin_uninstall_url": settings.LINKEDIN_UNINSTALL_URI,
            "instagram_redirect_url": settings.INSTAGRAM_REDIRECT_URI,
            "instagram_uninstall_url": settings.INSTAGRAM_UNINSTALL_URI,
            "facebook_redirect_url": settings.FACEBOOK_REDIRECT_URI,
            "facebook_uninstall_url": settings.FACEBOOK_UNINSTALL_URI,
        },
    )


@login_required
async def linkedin_login(request):
    linkedin_auth_url = (
        "https://www.linkedin.com/oauth/v2/authorization"
        "?response_type=code"
        f"&client_id={settings.LINKEDIN_CLIENT_ID}"
        f"&redirect_uri={settings.LINKEDIN_REDIRECT_URI}"
        "&scope=w_member_social openid profile email"
    )
    return redirect(linkedin_auth_url)


@login_required
async def linkedin_callback(request):
    code = request.GET.get("code")
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
    access_token = response.json().get("access_token")

    # Get the user ID
    user_info_url = "https://api.linkedin.com/v2/userinfo"
    headers = {
        "Authorization": f"Bearer {access_token}",
    }
    response = requests.get(user_info_url, headers=headers)
    user_info = response.json()
    user_id = user_info.get("sub")

    if access_token is None or user_id is None:
        messages.add_message(
            request,
            messages.ERROR,
            "Linkedin client secret is outdated or incorect!",
            extra_tags="🟥 Error!",
        )
        return redirect("/integrations/")

    IntegrationsModel.objects.update_or_create(
        account_id=request.user.id,
        user_id=user_id,
        platform=Platform.LINKEDIN.value,
        defaults={
            "account_id": request.user.id,
            "user_id": user_id,
            "access_token": access_token,
            "platform": Platform.LINKEDIN.value,
        },
    )

    messages.add_message(
        request,
        messages.SUCCESS,
        "Successfully logged into Linkedin! Now the app can make posts on your behalf.",
        extra_tags="✅ Success!",
    )

    return redirect("/integrations/")


@login_required
async def linkedin_uninstall(request):

    IntegrationsModel.objects.filter(
        account_id=request.user.id, platform=Platform.LINKEDIN.value
    ).delete()

    messages.add_message(
        request,
        messages.SUCCESS,
        "Deleted the access token.",
        extra_tags="✅ Success!",
    )

    return redirect("/integrations/")


@login_required
async def x_login(request):
    x_auth_url = (
        "https://twitter.com/i/oauth2/authorize"
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
async def x_callback(request):
    code = request.GET.get("code")
    if not code:
        messages.add_message(
            request,
            messages.ERROR,
            "Could not get the code from previous call. Please try again...",
            extra_tags="🟥 Error!",
        )
        return redirect("/integrations/")

    oauth = OAuth2Session(
        client_id=settings.X_CLIENT_ID, redirect_uri=settings.X_REDIRECT_URI
    )

    try:
        token = oauth.fetch_token(
            "https://api.twitter.com/2/oauth2/token",
            code=code,
            client_secret=settings.X_CLIENT_SECRET,
            code_verifier="challenge",
            include_client_id=True,
            auth=(
                settings.X_CLIENT_ID,
                settings.X_CLIENT_SECRET,
            ),  # Ensure auth header is included
        )
    except Exception as e:
        log.error(f"Error fetching token: {e}")
        messages.add_message(
            request,
            messages.ERROR,
            "X client secret is outdated or incorrect!",
            extra_tags="🟥 Error!",
        )
        return redirect("/integrations/")

    try:
        user_info = oauth.get("https://api.twitter.com/2/users/me").json()
        user_id = user_info["data"]["id"]
    except Exception as e:
        log.error(f"Could not get user_id: {e}")
        messages.add_message(
            request,
            messages.ERROR,
            "Failed to fetch user information!",
            extra_tags="🟥 Error!",
        )
        return redirect("/integrations/")

    IntegrationsModel.objects.update_or_create(
        account_id=request.user.id,
        user_id=user_id,
        platform=Platform.X_TWITTER.value,
        defaults={
            "account_id": request.user.id,
            "user_id": user_id,
            "access_token": token["access_token"],
            "refresh_token": token["refresh_token"],
            "platform": Platform.X_TWITTER.value,
        },
    )

    messages.add_message(
        request,
        messages.SUCCESS,
        "Successfully logged into X! Now the app can make posts on your behalf.",
        extra_tags="✅ Success!",
    )

    return redirect("/integrations/")


@login_required
async def x_uninstall(request):

    IntegrationsModel.objects.filter(
        account_id=request.user.id, platform=Platform.X_TWITTER.value
    ).delete()

    messages.add_message(
        request,
        messages.SUCCESS,
        "Deleted the access token.",
        extra_tags="✅ Success!",
    )

    return redirect("/integrations/")


@login_required
async def facebook_login(request):
    fb_login_url = (
        "https://www.facebook.com/v22.0/dialog/oauth"
        "?response_type=code"
        f"&client_id={settings.FACEBOOK_CLIENT_ID}"
        f"&redirect_uri={settings.FACEBOOK_REDIRECT_URI}"
        "&scope=email,public_profile,pages_show_list,pages_manage_posts,instagram_basic,instagram_content_publish,business_management"
    )
    return redirect(fb_login_url)


@login_required
async def facebook_callback(request):
    code = request.GET.get("code")
    if not code:
        messages.add_message(
            request,
            messages.ERROR,
            "Could not get the code from the previous call. Please try again...",
            extra_tags="🟥 Error!",
        )
        return redirect("/integrations/")

    # Exchange code for access token
    response = requests.post(
        url="https://graph.facebook.com/v22.0/oauth/access_token",
        data={
            "client_id": settings.FACEBOOK_CLIENT_ID,
            "client_secret": settings.FACEBOOK_CLIENT_SECRET,
            "code": code,
            "redirect_uri": settings.FACEBOOK_REDIRECT_URI,
            "grant_type": "authorization_code",
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    if response.status_code != 200:
        messages.add_message(
            request,
            messages.ERROR,
            "Facebook client secret is outdated or incorrect!",
            extra_tags="🟥 Error!",
        )
        return redirect("/integrations/")

    short_token = response.json().get("access_token")

    # Exchange short-lived token for long-lived token
    response = requests.get(
        url="https://graph.facebook.com/v22.0/oauth/access_token",
        params={
            "grant_type": "fb_exchange_token",
            "client_id": settings.FACEBOOK_CLIENT_ID,
            "client_secret": settings.FACEBOOK_CLIENT_SECRET,
            "fb_exchange_token": short_token,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    if response.status_code != 200:
        messages.add_message(
            request,
            messages.ERROR,
            "Facebook client secret is outdated or incorrect!",
            extra_tags="🟥 Error!",
        )
        return redirect("/integrations/")

    access_token = response.json().get("access_token")

    if not access_token:
        messages.add_message(
            request,
            messages.ERROR,
            "Failed to retrieve long-lived access token from Facebook.",
            extra_tags="🟥 Error!",
        )
        return redirect("/integrations/")

    # Retrieve user ID using the Graph API directly
    user_info_url = "https://graph.facebook.com/v22.0/me"
    user_info_params = {"access_token": access_token, "fields": "id"}
    user_info_response = requests.get(user_info_url, params=user_info_params)
    user_id = None
    if user_info_response.status_code == 200:
        user_data = user_info_response.json()
        user_id = user_data.get("id")
    else:
        messages.add_message(
            request,
            messages.ERROR,
            f"Failed to retrieve user information from Facebook. Status Code: {user_info_response.status_code}, Response: {user_info_response.text}",
            extra_tags="🟥 Error!",
        )
        return redirect("/integrations/")

    # Retrieve pages associated with the user
    response_pages = requests.get(
        url=f"https://graph.facebook.com/v22.0/{user_id}/accounts",
        params={"access_token": access_token},
    )

    if response_pages.status_code != 200 or not response_pages.json().get("data"):
        messages.add_message(
            request,
            messages.ERROR,
            "Could not retrieve Facebook pages associated with the user!",
            extra_tags="🟥 Error!",
        )
        return redirect("/integrations/")

    pages = response_pages.json().get("data")

    if not pages:
        messages.add_message(
            request,
            messages.ERROR,
            "No Facebook pages found for the user!",
            extra_tags="🟥 Error!",
        )
        return redirect("/integrations/")

    page = pages[0]
    page_id = page["id"]
    page_access_token = page["access_token"]

    # Retrieve Instagram accounts linked to the page
    response_instagram = requests.get(
        url=f"https://graph.facebook.com/v22.0/{page_id}/instagram_accounts",
        params={"access_token": page_access_token},
    )

    if response_instagram.status_code != 200 or not response_instagram.json().get(
        "data"
    ):
        messages.add_message(
            request,
            messages.ERROR,
            "Could not retrieve Instagram accounts associated with the page!",
            extra_tags="🟥 Error!",
        )
        return redirect("/integrations/")

    instagram_accounts = response_instagram.json().get("data")

    if not instagram_accounts:
        messages.add_message(
            request,
            messages.ERROR,
            "No Instagram accounts found for the page!",
            extra_tags="🟥 Error!",
        )
        return redirect("/integrations/")

    # Update or create access tokens in the IntegrationsModel
    IntegrationsModel.objects.update_or_create(
        account_id=request.user.id,
        user_id=page_id,
        platform=Platform.FACEBOOK.value,
        defaults={
            "account_id": request.user.id,
            "user_id": page_id,
            "access_token": page_access_token,
            "platform": Platform.FACEBOOK.value,
        },
    )

    account = instagram_accounts[0]
    IntegrationsModel.objects.update_or_create(
        account_id=request.user.id,
        user_id=account["id"],
        platform=Platform.INSTAGRAM.value,
        defaults={
            "account_id": request.user.id,
            "user_id": account["id"],
            "access_token": page_access_token,
            "platform": Platform.INSTAGRAM.value,
        },
    )

    messages.add_message(
        request,
        messages.SUCCESS,
        "Successfully logged into Facebook and Instagram! Now the app can make posts on your behalf.",
        extra_tags="✅ Success!",
    )

    return redirect("/integrations/")


@login_required
async def facebook_uninstall(request):

    IntegrationsModel.objects.filter(
        account_id=request.user.id, platform=Platform.FACEBOOK.value
    ).delete()

    IntegrationsModel.objects.filter(
        account_id=request.user.id, platform=Platform.INSTAGRAM.value
    ).delete()

    messages.add_message(
        request,
        messages.SUCCESS,
        "Deleted the access tokens.",
        extra_tags="✅ Success!",
    )

    return redirect("/integrations/")
