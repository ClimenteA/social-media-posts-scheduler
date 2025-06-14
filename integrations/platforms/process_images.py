import os
import uuid
import requests
from django.db.models import Q
from django.core.files import File
from core.logger import log, send_notification
from socialsched.models import PostModel, MediaFileTypes
from integrations.image_processor.instagram_image import make_instagram_image




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

        for post in posts:
            try:

                ext = os.path.splitext(post.media_file.url)[1].lower()
                ext = ext.split("?")[0]
                img_response = requests.get(post.media_file.url)
                img_response.raise_for_status()

                image_path = f"/tmp/{uuid.uuid4().hex}{ext}"
                with open(image_path, "wb") as f:
                    f.write(img_response.content)

                image_path = make_instagram_image(image_path, post.description)

                with open(image_path, "rb") as f:
                    post.media_file = File(f)
                    post.image_processed = True
                    post.save(skip_validation=True)

                os.remove(image_path)
                
            except Exception as err:
                log.exception(err)


    except Exception as err:
        log.exception(err)
        send_notification("ImPosting", f"Got error on processing images {err}")
