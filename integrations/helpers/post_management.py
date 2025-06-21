import os
import time
import asyncio
from core.logger import log
from core import settings
from django.db.models import Q
from datetime import timedelta
from django.utils import timezone
from socialsched.models import PostModel
from zoneinfo import ZoneInfo

from .utils import get_filepath_from_cloudflare_url, delete_tmp_media_files
from .refresh_tokens import refresh_tokens
from .process_images import process_images
from .process_videos import process_videos

from integrations.platforms.linkedin import post_on_linkedin
from integrations.platforms.xtwitter import post_on_x
from integrations.platforms.facebook import post_on_facebook
from integrations.platforms.instagram import post_on_instagram
from integrations.platforms.tiktok import post_on_tiktok


def post_scheduled_posts(buffer_seconds: int):
    start = time.perf_counter()
    now_utc = timezone.now() - timedelta(seconds=buffer_seconds)
    
    try:

        # Ensure tokens, images, and videos are read to upload
        refresh_tokens()
        process_images()
        process_videos()

        pre_processing_time = (time.perf_counter() - start)
        if int(pre_processing_time) > 0:
            log.info(f"Pre-processing took {pre_processing_time:.2f} seconds")

        # Publish posts
        potential_posts = PostModel.objects.filter(
            Q(post_on_x=True)
            | Q(post_on_instagram=True)
            | Q(post_on_facebook=True)
            | Q(post_on_linkedin=True)
            | Q(post_on_tiktok=True)
        ).only("pk", "scheduled_on", "post_timezone")

        post_ids_to_publish = []
        for post in potential_posts:
            target_tz = ZoneInfo(post.post_timezone)
            scheduled_aware = post.scheduled_on.replace(tzinfo=target_tz)
            now_in_target_tz = now_utc.astimezone(target_tz)
            if now_in_target_tz >= scheduled_aware:
                post_ids_to_publish.append(post.pk)

        posts = PostModel.objects.filter(pk__in=post_ids_to_publish)

        if len(posts) == 0:
            total_time = time.perf_counter() - start
            if int(total_time) > 0:
                log.info(f"Total time is {total_time:.2f} seconds")
            return total_time

        async def run_post_tasks():
            async_tasks = []

            for post in posts:
                text = post.description
                media_type = post.media_file_type
                media_path = None
                if post.media_file:
                    media_path = get_filepath_from_cloudflare_url(post.media_file.url)
                media_url = None
                if post.media_file:
                    media_url = f"{settings.APP_URL}/proxy-media-file/{os.path.basename(media_path)}" 

                # LINKEDIN
                if post.post_on_linkedin:
                    async_tasks.append(post_on_linkedin(post.account_id, post.id, text, media_path))

                # X
                if post.post_on_x:
                    async_tasks.append(post_on_x(post.account_id, post.id, text, media_path))

                # FACEBOOK
                if post.post_on_facebook:
                    async_tasks.append(post_on_facebook(post.account_id, post.id, text, media_type, media_url, media_path))

                # INSTAGRAM
                if post.post_on_instagram:
                    async_tasks.append(post_on_instagram(post.account_id, post.id, text, media_type, media_url, media_path))

                # TIKTOK
                if post.post_on_tiktok:
                    async_tasks.append(post_on_tiktok(post.account_id, post.id, text, media_path))

            log.debug(f"Gathered async tasks {len(async_tasks)} to run.")
            return await asyncio.gather(*async_tasks)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            log.debug(f"Running async posting for {now_utc}")
            loop.run_until_complete(run_post_tasks())
            log.debug(f"Finished async posting for {now_utc}")
        finally:
            delete_tmp_media_files()
            loop.close()

        total_time = time.perf_counter() - start
        if int(total_time) > 0:
            log.info(f"Total time is {total_time:.2f} seconds")
        return total_time
    
    except Exception as err:
        log.exception(err)
        total_time = time.perf_counter() - start
        if int(total_time) > 0:
            log.info(f"Total time is {total_time:.2f} seconds")
        return total_time
    
    