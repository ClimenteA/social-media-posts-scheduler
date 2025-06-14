from django.db.models import Q
from socialsched.models import PostModel, MediaFileTypes
from core.logger import log, send_notification




def process_videos():
    try:
        pass
    except Exception as err:
        log.exception(err)
        send_notification("ImPosting", f"Got error on prcessing images {err}")
        




