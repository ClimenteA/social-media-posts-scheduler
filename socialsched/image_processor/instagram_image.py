import os
import uuid
import shutil
import textwrap
from pathlib import Path
from core import settings
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from core.logger import log, send_notification
from .pexels import get_relevant_image_for_text


def resize_image_width(image_path: str, target_width: int = 1080):
    img = Image.open(image_path)

    # Calculate new height to maintain aspect ratio
    original_width, original_height = img.size
    aspect_ratio = original_height / original_width
    new_height = int(target_width * aspect_ratio)

    # Resize the image
    resized_img = img.resize((target_width, new_height), Image.LANCZOS)
    resized_img.save(image_path)

    return image_path


def resize_image(image_path: str, image_bg: str = None, target_width: int = 1080, target_height: int = 1350):
    bgimg_path = image_bg or Path(__file__).parent / "bg.jpg"

    # Open and convert both images to RGB
    img = Image.open(image_path).convert("RGB")
    bg_img = Image.open(bgimg_path).convert("RGB")

    # Resize and crop background to exactly match the target size
    bg_aspect = bg_img.width / bg_img.height
    target_aspect = target_width / target_height

    if bg_aspect > target_aspect:
        # Background is wider — match height, crop width
        new_bg_height = target_height
        new_bg_width = int(new_bg_height * bg_aspect)
        resized_bg = bg_img.resize((new_bg_width, new_bg_height), Image.LANCZOS)
        left = (new_bg_width - target_width) // 2
        top = 0
    else:
        # Background is taller — match width, crop height
        new_bg_width = target_width
        new_bg_height = int(new_bg_width / bg_aspect)
        resized_bg = bg_img.resize((new_bg_width, new_bg_height), Image.LANCZOS)
        left = 0
        top = (new_bg_height - target_height) // 2

    cropped_bg = resized_bg.crop((left, top, left + target_width, top + target_height))

    # Apply blur to the cropped background
    blurred_bg = cropped_bg.filter(ImageFilter.GaussianBlur(radius=10))

    # Resize the main image to fit within the frame (object-fit: contain)
    img_aspect = img.width / img.height
    frame_aspect = target_width / target_height

    if img_aspect > frame_aspect:
        # Image is wider than frame — match width
        new_img_width = target_width
        new_img_height = int(target_width / img_aspect)
    else:
        # Image is taller than frame — match height
        new_img_height = target_height
        new_img_width = int(target_height * img_aspect)

    resized_img = img.resize((new_img_width, new_img_height), Image.LANCZOS)

    # Center the resized image on the blurred background
    position_x = (target_width - new_img_width) // 2
    position_y = (target_height - new_img_height) // 2
    blurred_bg.paste(resized_img, (position_x, position_y))

    # Save the final image
    blurred_bg.save(image_path)
    return image_path


def create_image_from_text(
    text: str,
    image_path: str = None,
    width: int = 1080,
    font_size: int = 40,
    padding: int = 40,
    background_color: str = "black",
    text_color: str = "white",
):
    if image_path is None:
        image_path = os.path.join(settings.MEDIA_ROOT, f"{uuid.uuid4()}.png")

    font_path = Path(__file__).parent / "Inter_28pt-SemiBold.ttf"
    font = ImageFont.truetype(font_path, font_size)

    # Calculate how much space we have for text
    text_width = width - (2.3 * padding)

    # Split the text by newlines first to preserve manual line breaks
    paragraphs = text.split("\n")

    # Then wrap each paragraph to fit width
    all_lines = []
    for paragraph in paragraphs:
        if paragraph.strip():
            # Wrap non-empty paragraphs
            wrapped_lines = textwrap.wrap(
                paragraph, width=int(text_width / (font_size * 0.5))
            )
            all_lines.extend(wrapped_lines)
        else:
            # Preserve empty lines
            all_lines.append("")

    # Calculate height based on number of lines
    line_height = font_size * 1.5
    text_height = len(all_lines) * line_height
    height = int(text_height + (2 * padding))

    # Create image
    image = Image.new("RGB", (width, height), color=background_color)
    draw = ImageDraw.Draw(image)

    # Draw text
    y_position = padding
    for line in all_lines:
        draw.text((padding, y_position), line, font=font, fill=text_color)
        y_position += line_height

    image.save(image_path)

    return image_path


def concat_image_vertically(
    image_path: str, top_image_path: str, bottom_image_path: str
):
    top_img = Image.open(top_image_path)
    bottom_img = Image.open(bottom_image_path)

    # Create a new image with the height being the sum of both images' heights
    combined_height = top_img.height + bottom_img.height
    combined_img = Image.new("RGB", (top_img.width, combined_height))

    # Paste the first image at the top
    combined_img.paste(top_img, (0, 0))

    # Paste the second image below the first one
    combined_img.paste(bottom_img, (0, top_img.height))

    combined_img.save(image_path)
    return image_path


def create_image(*, image_path: str = None, text: str = None):
    if image_path and not text:
        resized_image_path = resize_image(image_path)
        return resized_image_path

    if text and not image_path:
        text_image_path = create_image_from_text(text)
        bg_image_path = get_relevant_image_for_text(text)
        resized_image_path = resize_image(text_image_path, bg_image_path)
        os.remove(bg_image_path)
        return resized_image_path

    if text and image_path:
        text_image_path = None
        resized_image_path_bk = None
        try:
            text_image_path = create_image_from_text(text)
            resized_image_path = resize_image_width(image_path)
            resized_image_path_bk = os.path.join(os.path.dirname(resized_image_path), "copy_" + os.path.basename(resized_image_path))
            shutil.copy(resized_image_path, resized_image_path_bk)
            concated_image_path = concat_image_vertically(
                image_path=image_path,
                top_image_path=text_image_path,
                bottom_image_path=resized_image_path,
            )
            resized_image_path = resize_image(concated_image_path, resized_image_path_bk)
            return resized_image_path
        finally:
            if text_image_path:
                os.remove(text_image_path)
            if resized_image_path_bk:
                os.remove(resized_image_path_bk)

    raise Exception("Image, text or both must be provided!")


def make_instagram_image(image_path: str = None, text: str = None):
    try:
        created_image_path = create_image(image_path=image_path, text=text)
        return os.path.basename(created_image_path)
    except Exception as err:
        log.exception(err)
        send_notification(email="ImPosting", message=str(err))
        return image_path
