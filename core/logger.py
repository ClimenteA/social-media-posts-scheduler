import os
import requests
from .settings import logpath
from loguru import logger as log
from .settings import NOTIFICATION_API_KEY, NOTIFICATION_API_URL


def overwrite_on_100mb(message, file):
    if os.path.exists(logpath) and os.path.getsize(logpath) >= 100 * 1024 * 1024:
        file.close()
        os.remove(logpath)  
        return logpath


log.add(
    logpath,
    enqueue=True,
    level="INFO",
    rotation=overwrite_on_100mb,
    retention=None,
    compression=None,
)


def send_notification(email: str, message: str):
    if not NOTIFICATION_API_KEY:
        return
    try:
        response = requests.post(
            NOTIFICATION_API_URL,
            headers={"Accept": "*/*", "Content-Type": "application/json"},
            json={
                "messageType": "general",
                "email": str(email),
                "message": message,
                "apikey": NOTIFICATION_API_KEY,
            },
        )
        response.raise_for_status()
    except Exception as err:
        log.exception(err)
