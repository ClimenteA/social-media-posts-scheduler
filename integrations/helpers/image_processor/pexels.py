import re
import uuid
import random
import requests
from collections import Counter
from core import settings
from core.logger import log, send_notification


def extract_keywords(text):
    words = re.findall(r"\b[a-zA-Z]{4,}\b", text.lower())  # Words > 3 letters
    return Counter(words)


def get_relevant_image_for_text(text: str):
    try:

        # Step 1: Extract keywords and form query
        keyword_counts = extract_keywords(text)
        keywords = [word for word, _ in keyword_counts.most_common(4)]
        query = "+".join(keywords) or "random"

        # Step 2: Fetch images from Pexels
        response = requests.get(
            f"https://api.pexels.com/v1/search?query={query}&per_page=9",
            headers={"Authorization": settings.PEXELS_API_KEY},
        )
        response.raise_for_status()
        photos = response.json()["photos"]

        if not photos:
            return None  # No images found

        # Step 3: Find best match based on 'alt' field
        def score(photo):
            alt_words = re.findall(r"\b[a-zA-Z]{4,}\b", photo["alt"].lower())
            return sum(word in alt_words for word in keywords)

        scored_photos = [(photo, score(photo)) for photo in photos]
        scored_photos.sort(key=lambda x: x[1], reverse=True)

        best_photo = (
            scored_photos[0][0] if scored_photos[0][1] > 0 else random.choice(photos)
        )
        photo_url = best_photo["src"]["large"]  # Or "original", "large", etc.

        img_response = requests.get(photo_url)
        img_response.raise_for_status()

        image_path = f"/tmp/{uuid.uuid4().hex}.png"
        with open(image_path, "wb") as f:
            f.write(img_response.content)

        return image_path
    
    except Exception as err:
        log.exception(err)
        send_notification("ImPosting", f"Error on pexels: {err}")
        return None
