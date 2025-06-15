import os
from django.db.models import Q
from django.core.files import File
from core.logger import log, send_notification
from socialsched.models import PostModel, MediaFileTypes
from integrations.helpers.image_processor.make_image_postable import make_image_postable
from integrations.helpers.utils import get_filepath_from_cloudflare_url



def process_images():
    try:

        posts: list[PostModel] = PostModel.objects.filter(
            process_image = True,
            image_processed = False,
            media_file_type = MediaFileTypes.IMAGE.value,
        ).filter(
            Q(post_on_x=True)
            | Q(post_on_instagram=True)
            | Q(post_on_facebook=True)
            | Q(post_on_linkedin=True)
            | Q(post_on_tiktok=True)
        ).only("pk", "account_id", "description", "media_file")

        if len(posts) == 0:
            return

        log.debug(f"Got {len(posts)} images to process")
        
        for post in posts:
            try:
                image_path = get_filepath_from_cloudflare_url(post.media_file.url)
                image_path = make_image_postable(image_path, post.description)

                log.debug(f"Processing {image_path}...")
        
                with open(image_path, "rb") as f:
                    post.media_file = File(f)
                    post.image_processed = True
                    post.save(skip_validation=True)

                os.remove(image_path)

                log.debug(f"Done processing {image_path}!")
                
            except Exception as err:
                log.exception(err)
                send_notification("ImPosting", f"Got error on processing image {err}")

    except Exception as err:
        log.exception(err)
        send_notification("ImPosting", f"Got error on processing images {err}")
