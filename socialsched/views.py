import uuid
from zoneinfo import ZoneInfo
from pathlib import Path
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout
from django.utils import timezone
from django.db.models import Min, Max
from core.logger import log
from social_django.models import UserSocialAuth
from datetime import datetime, timedelta
from integrations.helpers.utils import get_tiktok_creator_info, get_integrations_context
from .models import PostModel
from .forms import PostForm
from .schedule_utils import (
    get_day_data,
    get_initial_month_placeholder,
    get_year_dates,
)


@login_required
def calendar(request):
    user_social_auth = UserSocialAuth.objects.filter(user=request.user).first()
    social_uid = user_social_auth.pk

    today = timezone.now()
    selected_year = today.year
    if request.GET.get("year") is not None:
        selected_year = int(request.GET.get("year"))

    min_date = PostModel.objects.filter(account_id=social_uid).aggregate(
        Min("scheduled_on")
    )["scheduled_on__min"]

    max_date = PostModel.objects.filter(account_id=social_uid).aggregate(
        Max("scheduled_on")
    )["scheduled_on__max"]

    min_year = min_date.year if min_date else today.year
    max_year = max_date.year if max_date else today.year

    select_years = list(set([min_year, max_year, today.year, today.year + 4]))
    select_years = [y for y in range(min(select_years), max(select_years), 1)]

    posts = PostModel.objects.filter(
        account_id=social_uid, scheduled_on__year=selected_year
    ).values(
        "scheduled_on",
        "post_on_instagram",
        "post_on_facebook",
        "post_on_tiktok",
        "post_on_linkedin",
        "post_on_x",
        "link_instagram",
        "link_facebook",
        "link_tiktok",
        "link_linkedin",
        "link_x",
    )

    year_dates = get_year_dates(selected_year)

    calendar_data = {}
    for d in year_dates:
        if d.month == 1:
            if "january" not in calendar_data:
                calendar_data["january"] = get_initial_month_placeholder(today, d)
            day_data = get_day_data(posts, d)
            calendar_data["january"]["days"].append(day_data)

        if d.month == 2:
            if "february" not in calendar_data:
                calendar_data["february"] = get_initial_month_placeholder(today, d)
            day_data = get_day_data(posts, d)
            calendar_data["february"]["days"].append(day_data)

        if d.month == 3:
            if "march" not in calendar_data:
                calendar_data["march"] = get_initial_month_placeholder(today, d)
            day_data = get_day_data(posts, d)
            calendar_data["march"]["days"].append(day_data)

        if d.month == 4:
            if "april" not in calendar_data:
                calendar_data["april"] = get_initial_month_placeholder(today, d)
            day_data = get_day_data(posts, d)
            calendar_data["april"]["days"].append(day_data)

        if d.month == 5:
            if "may" not in calendar_data:
                calendar_data["may"] = get_initial_month_placeholder(today, d)
            day_data = get_day_data(posts, d)
            calendar_data["may"]["days"].append(day_data)

        if d.month == 6:
            if "june" not in calendar_data:
                calendar_data["june"] = get_initial_month_placeholder(today, d)
            day_data = get_day_data(posts, d)
            calendar_data["june"]["days"].append(day_data)

        if d.month == 7:
            if "july" not in calendar_data:
                calendar_data["july"] = get_initial_month_placeholder(today, d)
            day_data = get_day_data(posts, d)
            calendar_data["july"]["days"].append(day_data)

        if d.month == 8:
            if "august" not in calendar_data:
                calendar_data["august"] = get_initial_month_placeholder(today, d)
            day_data = get_day_data(posts, d)
            calendar_data["august"]["days"].append(day_data)

        if d.month == 9:
            if "september" not in calendar_data:
                calendar_data["september"] = get_initial_month_placeholder(today, d)
            day_data = get_day_data(posts, d)
            calendar_data["september"]["days"].append(day_data)

        if d.month == 10:
            if "octomber" not in calendar_data:
                calendar_data["octomber"] = get_initial_month_placeholder(today, d)
            day_data = get_day_data(posts, d)
            calendar_data["octomber"]["days"].append(day_data)

        if d.month == 11:
            if "november" not in calendar_data:
                calendar_data["november"] = get_initial_month_placeholder(today, d)
            day_data = get_day_data(posts, d)
            calendar_data["november"]["days"].append(day_data)

        if d.month == 12:
            if "december" not in calendar_data:
                calendar_data["december"] = get_initial_month_placeholder(today, d)
            day_data = get_day_data(posts, d)
            calendar_data["december"]["days"].append(day_data)

    return render(
        request,
        "calendar.html",
        context={
            "selected_year": selected_year,
            "select_years": select_years,
            "calendar_data": calendar_data,
            "today": today.date().isoformat(),
        },
    )


def get_schedule_form_context(social_uid: int, isodate: str, form: PostForm = None):

    today = timezone.now()
    scheduled_on = datetime.strptime(isodate, "%Y-%m-%d").date()
    prev_date = scheduled_on - timedelta(days=1)
    next_date = scheduled_on + timedelta(days=1)

    posts = PostModel.objects.filter(
        account_id=social_uid, scheduled_on__date=scheduled_on
    )

    show_form = today.date() <= scheduled_on

    if form is None:
        form = PostForm(initial={"scheduled_on": scheduled_on})

    integrations_info = get_integrations_context(social_uid)

    tiktok_info = None
    if integrations_info["tiktok_ok"]:
        tiktok_info = get_tiktok_creator_info(social_uid)

    return {
        "show_form": show_form,
        "posts": posts,
        "post_form": form,
        "isodate": isodate,
        "year": scheduled_on.year,
        "current_date": scheduled_on,
        "prev_date": prev_date,
        "today": today.date().isoformat(),
        "next_date": next_date,
        "integrations_info": integrations_info,
        "tiktok_info": tiktok_info,
    }


@login_required
def schedule_form(request, isodate):
    user_social_auth = UserSocialAuth.objects.filter(user=request.user).first()
    social_uid = user_social_auth.pk

    context = get_schedule_form_context(social_uid, isodate, form=None)

    if not context["integrations_info"]["has_at_least_one_valid_integration"]:
        messages.add_message(
            request,
            messages.ERROR,
            "Please grant access to at least 1 platform before posting.",
            extra_tags="💡 Action needed!",
        )
        return redirect("/integrations/")

    return render(request, "schedule.html", context=context)


@login_required
def schedule_save(request, isodate):
    now_utc = timezone.now()

    user_social_auth = UserSocialAuth.objects.filter(user=request.user).first()
    social_uid = user_social_auth.pk

    form = PostForm(request.POST, request.FILES)

    if not form.is_valid():
        return render(
            request,
            "schedule.html",
            context=get_schedule_form_context(social_uid, isodate, form),
        )

    try:
        post: PostModel = form.save(commit=False)
        post.account_id = social_uid

        # Delay schedule_on with time it took for uploading the file
        if post.scheduled_on:
            # Just to make sure user completed the second form
            if post.post_on_tiktok:
                post.scheduled_on = post.scheduled_on + timedelta(minutes=30)
            else:
                post.scheduled_on = post.scheduled_on + timedelta(minutes=5)

            target_tz = ZoneInfo(post.post_timezone)
            scheduled_aware = post.scheduled_on.replace(tzinfo=target_tz)
            now_in_target_tz = now_utc.astimezone(target_tz)

            if now_in_target_tz > scheduled_aware:
                delay = now_in_target_tz - scheduled_aware
                post.scheduled_on = post.scheduled_on + delay

        post.save()

    except Exception as err:
        log.exception(err)
        messages.add_message(
            request,
            messages.ERROR,
            err,
            extra_tags="🟥 Error!",
        )
        return redirect(f"/schedule/{isodate}/")


@login_required
def schedule_delete(request, post_id):
    user_social_auth = UserSocialAuth.objects.filter(user=request.user).first()
    social_uid = user_social_auth.pk

    post = get_object_or_404(PostModel, id=post_id, account_id=social_uid)
    isodate = post.scheduled_on.date().isoformat()

    if any(
        [
            post.link_facebook,
            post.link_instagram,
            post.link_linkedin,
            post.link_tiktok,
            post.link_x,
        ]
    ):
        messages.add_message(
            request,
            messages.ERROR,
            "You cannot delete a published post!",
            extra_tags="🟥 Not allowed!",
        )
        return redirect(f"/schedule/{isodate}/")

    post.delete()

    messages.add_message(
        request,
        messages.SUCCESS,
        "Post was deleted!",
        extra_tags="✅ Succes!",
    )
    return redirect(f"/schedule/{isodate}/")


def login_user(request):
    return render(request, "login.html")


@login_required
def logout_user(request):
    logout(request)
    return redirect("login")


def legal(request):
    return render(request, "legal.html")


description = "These ideas are just to get you started - you'll build momentum after posting consistently for a month."

articles = {
    "100-ways-to-never-run-out-of-content-ideas": {
        "title": "100 ways to never run out of content ideas 💡",
        "description": description,
        "ideas_txt_filename": "how_to_never_run_out_of_content_ideas.txt",
    },
    "365-content-ideas-for-business-process-outsourcing-companies-bpo": {
        "title": "365 content ideas for Business Process Outsourcing (BPO) companies 🌏",
        "description": description,
        "ideas_txt_filename": "content_ideas_for_bpo_companies.txt",
    },
    "365-content-ideas-for-dentists": {
        "title": "365 content ideas for dentists 🦷",
        "description": description,
        "ideas_txt_filename": "content_ideas_for_dentists.txt",
    },
    "365-content-ideas-for-veterinary-cabinets": {
        "title": "365 content ideas for veterinary cabinets 🐱",
        "description": description,
        "ideas_txt_filename": "content_ideas_for_veterinary_cabinets.txt",
    },
    "365-content-ideas-for-startup-founders": {
        "title": "365 content ideas for startup founders 🤵",
        "description": description,
        "ideas_txt_filename": "content_ideas_for_startup_founders.txt",
    },
    "365-content-ideas-for-car-repair-shops": {
        "title": "365 content ideas for car repair shops 🧑‍🔧",
        "description": description,
        "ideas_txt_filename": "content_ideas_for_car_repair_shops.txt",
    },
    "365-content-ideas-for-influencers-in-the-beauty-and-fashion-industry": {
        "title": "365 content ideas for influencers in the beauty and fashion industry 💅",
        "description": description,
        "ideas_txt_filename": "content_ideas_for_influencers_in_beauty_and_fashion_industry.txt",
    },
    "365-content-ideas-for-influencers-in-the-health-and-wellness-industry": {
        "title": "365 content ideas for influencers in the health and wellness industry 🧘",
        "description": description,
        "ideas_txt_filename": "content_ideas_for_influencers_in_health_and_wellness_industry.txt",
    },
    "365-content-ideas-for-influencers-in-the-travel-and-hospitality-industry": {
        "title": "365 content ideas for influencers in the travel and hospitality industry ✈️",
        "description": description,
        "ideas_txt_filename": "content_ideas_for_influencers_in_travel_and_hospitality_industry.txt",
    },
    "365-content-ideas-for-real-estate-agents": {
        "title": "365 content ideas for real estate agents 🏡",
        "description": description,
        "ideas_txt_filename": "content_ideas_for_real_estate_agents.txt",
    },
    "365-content-ideas-for-lawyers-and-legal-consultants": {
        "title": "365 content ideas for lawyers & legal consultants ⚖️",
        "description": description,
        "ideas_txt_filename": "content_ideas_for_lawyers_and_legal_consultants.txt",
    },
}


articles_list = []
for slug, details in articles.items():
    data = {"blog_slug": slug, "blog_title": details["title"]}
    articles_list.append(data)


def blog_articles(request):
    return render(request, "blog_articles.html", context={"items": articles_list})


def blog_article(request, blog_slug: str):

    if blog_slug not in articles:
        return redirect("/blog")

    txt_file = (
        Path(__file__).parent
        / f"ideas_lists/{articles[blog_slug]["ideas_txt_filename"]}"
    )
    with open(txt_file, "r") as f:
        ideas = []
        for line in f.readlines():
            line = line.strip()
            if not line:
                continue

            idea = {
                "id": uuid.uuid5(uuid.NAMESPACE_DNS, blog_slug + line),
                "text": line,
            }

            ideas.append(idea)

    return render(
        request,
        "blog_article.html",
        context={
            "title": articles[blog_slug]["title"],
            "description": articles[blog_slug]["description"],
            "ideas": ideas,
        },
    )
