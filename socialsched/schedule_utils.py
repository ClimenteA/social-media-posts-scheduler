from functools import lru_cache
from datetime import date, timedelta

@lru_cache(maxsize=None)
def get_year_dates(year: int) -> list[date]:
    start_date = date(year, 1, 1)
    end_date = date(year, 12, 31)

    dates = []
    current_date = start_date
    while current_date <= end_date:
        dates.append(current_date)
        current_date += timedelta(days=1)

    return dates


def get_initial_month_placeholder(today, d):

    past_month_bg = "slate-650"
    current_month_bg = "jade-600"
    next_month_bg = "blue-750"
    light_text = "blue-50"
    dark_text = "blue-250"

    current_month = today.date().month == d.month and today.year == d.year

    if current_month:
        bg = current_month_bg
        text_color = light_text
    elif d < today.date():
        bg = past_month_bg
        text_color = dark_text
    else:
        bg = next_month_bg
        text_color = light_text

    return {
        "article_background": bg,
        "text_color": text_color,
        "current_month": current_month,
        "days": [],
    }


def get_day_data(posts, d):
    posts_count = 0
    post_on_x = 0
    post_on_instagram = 0
    post_on_facebook = 0
    post_on_linkedin = 0
    post_on_tiktok = 0
    for post in posts:

        if post["scheduled_on"].date() != d:
            continue

        post_on_x += 1 if post["post_on_x"] or post["link_x"] else 0
        post_on_instagram += (
            1 if post["post_on_instagram"] or post["link_instagram"] else 0
        )
        post_on_facebook += (
            1 if post["post_on_facebook"] or post["link_facebook"] else 0
        )
        post_on_linkedin += (
            1 if post["post_on_linkedin"] or post["link_linkedin"] else 0
        )
        post_on_tiktok += (
            1 if post["post_on_tiktok"] or post["link_tiktok"] else 0
        )
        posts_count += (
            1
            if any(
                [
                    post["post_on_x"],
                    post["post_on_instagram"],
                    post["post_on_facebook"],
                    post["post_on_linkedin"],
                    post["link_x"],
                    post["link_instagram"],
                    post["link_facebook"],
                    post["link_linkedin"],
                ]
            )
            else 0
        )

    return {
        "isodate": d.isoformat(),
        "day": f"{d.day:02}",
        "posts_count": posts_count,
        "instagram_count": post_on_instagram,
        "facebook_count": post_on_facebook,
        "linkedin_count": post_on_linkedin,
        "twitter_count": post_on_x,
        "tiktok_count": post_on_tiktok,
    }
