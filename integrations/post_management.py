import asyncio
from core import settings
from core.logger import log
from django.db.models import Q
from django.utils import timezone
from socialsched.models import PostModel
from zoneinfo import ZoneInfo
from .platforms.linkedin import post_on_linkedin
from .platforms.xtwitter import post_on_x
from .platforms.facebook import post_on_facebook
from .platforms.instagram import post_on_instagram
from .platforms.refresh_tokens import refresh_tokens


def post_scheduled_posts():

    refresh_tokens()

    potential_posts = PostModel.objects.filter(
        Q(post_on_x=True)
        | Q(post_on_instagram=True)
        | Q(post_on_facebook=True)
        | Q(post_on_linkedin=True)
    ).only("pk", "scheduled_on", "post_timezone")

    post_ids_to_publish = []
    now_utc = timezone.now()
    for post in potential_posts:
        target_tz = ZoneInfo(post.post_timezone)
        scheduled_aware = post.scheduled_on.replace(tzinfo=target_tz)
        now_in_target_tz = now_utc.astimezone(target_tz)
        if now_in_target_tz >= scheduled_aware:
            post_ids_to_publish.append(post.pk)

    posts = PostModel.objects.filter(pk__in=post_ids_to_publish)

    if len(posts) == 0:
        return

    async def run_post_tasks():
        async_tasks = []

        for post in posts:
            text = post.description
            media_path = post.media_file.path if post.media_file else None
            media_object = post.media_file if post.media_file else None
            media_url = None
            if media_object:
                media_url = settings.APP_URL + media_object.url

            # LINKEDIN
            if post.post_on_linkedin:
                async_tasks.append(post_on_linkedin(post.account_id, post.id, text, media_path))

            # X
            if post.post_on_x:
                async_tasks.append(post_on_x(post.account_id, post.id, text, media_path))

            # FACEBOOK
            if post.post_on_facebook:
                async_tasks.append(post_on_facebook(post.account_id, post.id, text, media_url, media_path))

            # INSTAGRAM
            if post.post_on_instagram:
                async_tasks.append(post_on_instagram(post.account_id, post.id, text, media_url, media_path))

        log.debug(f"Gathered async tasks {len(async_tasks)} to run.")
        return await asyncio.gather(*async_tasks)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        log.debug(f"Running async posting for {now_utc}")
        loop.run_until_complete(run_post_tasks())
        log.debug(f"Finished async posting for {now_utc}")
    finally:
        loop.close()
