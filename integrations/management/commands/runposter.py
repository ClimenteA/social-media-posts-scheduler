import signal
from core.logger import log
from threading import Thread, Event
from django.core.management.base import BaseCommand
from integrations.helpers.post_management import post_scheduled_posts

stop_event = Event()


def runner():
    buffer_seconds = 0
    while not stop_event.is_set():        
        buffer_seconds = post_scheduled_posts(buffer_seconds)
        stop_event.wait(5)
        buffer_seconds += 5


class Command(BaseCommand):
    help = "Run Poster."

    def handle(self, *args, **options):
        def handle_signal(signum, frame):
            log.info(f"Received termination signal ({signum}), shutting down...")
            stop_event.set()

        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, handle_signal)
        signal.signal(signal.SIGINT, handle_signal)

        poster = Thread(target=runner)
        log.info("Poster started!")
        poster.start()

        try:
            while poster.is_alive():
                poster.join(timeout=1)
        except Exception as e:
            log.exception("Unexpected error in poster runner.")
        finally:
            stop_event.set()
            poster.join()
            log.info("Poster stopped cleanly.")
