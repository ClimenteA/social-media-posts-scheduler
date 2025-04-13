import os
import shutil
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout
from django.conf import settings
from django.utils import timezone
from django.db.models import Min, Max
from datetime import datetime, timedelta
from .models import PostModel
from .forms import PostForm
from .schedule_utils import (
    get_day_data,
    get_initial_month_placeholder,
    get_year_dates,
)


@login_required
def delete_old_data(request):
    today = timezone.localtime()

    PostModel.objects.filter(scheduled_on__lt=today).delete()

    messages.add_message(
        request,
        messages.SUCCESS,
        "Old data was deleted!",
        extra_tags="✅ Success!",
    )
    return redirect("/account/")


@login_required
def delete_all_data(request):

    PostModel.objects.all().delete()

    shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
    os.makedirs(settings.MEDIA_ROOT, exist_ok=True)

    messages.add_message(
        request,
        messages.SUCCESS,
        "All data was deleted!",
        extra_tags="✅ Success!",
    )
    return redirect("/account/")


@login_required
def calendar(request):
    today = timezone.localtime()
    selected_year = today.year
    if request.GET.get("year") is not None:
        selected_year = int(request.GET.get("year"))

    min_date = PostModel.objects.aggregate(Min("scheduled_on_date"))[
        "scheduled_on_date__min"
    ]
    max_date = PostModel.objects.aggregate(Max("scheduled_on_date"))[
        "scheduled_on_date__max"
    ]
    min_year = min_date.year if min_date else today.year
    max_year = max_date.year if max_date else today.year

    select_years = list(set([min_year, max_year, today.year, today.year + 4]))
    select_years = [y for y in range(min(select_years), max(select_years), 1)]

    posts = PostModel.objects.filter(scheduled_on_date__year=selected_year).values(
        "scheduled_on",
        "post_on_x",
        "post_on_instagram",
        "post_on_facebook",
        "post_on_tiktok",
        "post_on_linkedin",
        "post_on_youtube",
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
            "today": today,
            "isotoday": today.date().isoformat(),
        },
    )


@login_required
def schedule_form(request, isodate):
    today = timezone.localtime()
    scheduled_on_date = datetime.strptime(isodate, "%Y-%m-%d").date()
    prev_date = scheduled_on_date - timedelta(days=1)
    next_date = scheduled_on_date + timedelta(days=1)
    posts = PostModel.objects.filter(scheduled_on_date=scheduled_on_date)

    show_form = today.date() <= scheduled_on_date

    form = PostForm(
        initial={
            "scheduled_on_time": (timezone.localtime() + timedelta(hours=1)).time(),
            "scheduled_on_date": scheduled_on_date,
        }
    )

    return render(
        request,
        "schedule.html",
        context={
            "show_form": show_form,
            "posts": posts,
            "post_form": form,
            "scheduled_on_date": isodate,
            "year": scheduled_on_date.year,
            "current_date": scheduled_on_date,
            "timezone": settings.TIME_ZONE,
            "prev_date": prev_date,
            "next_date": next_date,
        },
    )


@login_required
def schedule_modify(request, post_id):
    post = get_object_or_404(PostModel, id=post_id)
    posts = PostModel.objects.filter(scheduled_on_date=post.scheduled_on_date)
    prev_date = post.scheduled_on_date - timedelta(days=1)
    next_date = post.scheduled_on_date + timedelta(days=1)
    form = PostForm(instance=post)
    return render(
        request,
        "schedule.html",
        context={
            "posts": posts,
            "post_form": form,
            "post": post,
            "year": post.scheduled_on_date.year,
            "scheduled_on_date": post.scheduled_on_date.isoformat(),
            "timezone": settings.TIME_ZONE,
            "modify_post_id": post_id,
            "prev_date": prev_date,
            "next_date": next_date,
        },
    )


@login_required
def schedule_save(request, isodate):
    modify_post_id = None
    if request.GET.get("modify_post_id") is not None:
        modify_post_id = request.GET.get("modify_post_id")

    if modify_post_id:
        post = get_object_or_404(PostModel, id=modify_post_id)
        form = PostForm(request.POST, request.FILES, instance=post)
    else:
        form = PostForm(request.POST, request.FILES)

    if not form.is_valid():
        scheduled_on_date = datetime.strptime(isodate, "%Y-%m-%d").date()
        posts = PostModel.objects.filter(scheduled_on_date=scheduled_on_date)

        return render(
            request,
            "schedule.html",
            context={
                "posts": posts,
                "post_form": form,
                "scheduled_on_date": isodate,
                "timezone": settings.TIME_ZONE,
            },
        )

    try:
        form.save()
        messages.add_message(
            request,
            messages.SUCCESS,
            "Post was saved!",
            extra_tags="✅ Success!",
        )
        return redirect(f"/schedule/{isodate}/")
    except Exception as err:
        messages.add_message(
            request,
            messages.ERROR,
            err,
            extra_tags="🟥 Error!",
        )
        return redirect(f"/schedule/{isodate}/")


@login_required
def schedule_delete(request, post_id):
    post = get_object_or_404(PostModel, id=post_id)
    isodate = post.scheduled_on_date.isoformat()
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


@login_required
def user_account(request):

    return render(request, "user_account.html")
