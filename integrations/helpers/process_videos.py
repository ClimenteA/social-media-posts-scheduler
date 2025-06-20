import os
import uuid
import requests
from django.db.models import Q
from django.core.files import File
from socialsched.models import PostModel, MediaFileTypes
from core.logger import log, send_notification
from integrations.helpers.video_processor.make_video_postable import make_video_postable



def process_videos():
    try:

        posts: list[PostModel] = PostModel.objects.filter(
            process_video = True,
            video_processed = False,
            media_file_type = MediaFileTypes.VIDEO.value,
        ).filter(
            Q(post_on_x=True)
            | Q(post_on_instagram=True)
            | Q(post_on_facebook=True)
            | Q(post_on_linkedin=True)
            | Q(post_on_tiktok=True)
        ).only("pk", "account_id", "description", "media_file")

        if len(posts) == 0:
            return

        log.debug(f"Got {len(posts)} videos to process")
        
        for post in posts:
            try:

                ext = os.path.splitext(post.media_file.url)[1].lower()
                ext = ext.split("?")[0]
                vid_response = requests.get(post.media_file.url)
                vid_response.raise_for_status()

                video_path = f"/tmp/{uuid.uuid4().hex}{ext}"

                log.debug(f"Processing {video_path}...")
        
                with open(video_path, "wb") as f:
                    f.write(vid_response.content)

                video_path = make_video_postable(video_path, post.description)

                with open(video_path, "rb") as f:
                    post.media_file = File(f)
                    post.video_processed = True
                    post.save(skip_validation=True)

                os.remove(video_path)
                
                log.debug(f"Done processing {video_path}!")
                
            except Exception as err:
                log.exception(err)
                send_notification("ImPosting", f"Got error on processing video {err}")

    except Exception as err:
        log.exception(err)
        send_notification("ImPosting", f"Got error on processing videos {err}")

