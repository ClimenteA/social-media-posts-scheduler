import uuid
import shutil
import ffmpeg
from pathlib import Path
from core.logger import log



def process_video(video_path: str, output_path: str) -> None:
    
    # Target shared specs
    width, height = 1080, 1920
    fps = 30
    max_duration = 90  # Maximum duration acceptable to all 3 platforms

    # Load input
    video = ffmpeg.input(video_path)

    # Trim to max duration and ensure proper timing
    video = video.trim(start=0, end=max_duration).setpts("PTS-STARTPTS")

    # Resize with padding to fit 1080x1920 exactly
    video = (
        video.filter("scale", width, height, force_original_aspect_ratio="decrease")
             .filter("pad", width, height, "(ow-iw)/2", "(oh-ih)/2", color="black")
             .filter("fps", fps=fps, round="up")
    )

    # Prepare audio stream
    audio = ffmpeg.input(video_path).audio

    # Output settings
    stream = ffmpeg.output(
        video,
        audio,
        output_path,
        format='mp4',
        vcodec='libx264',
        pix_fmt='yuv420p',
        video_bitrate='5M',
        r=fps,
        g=fps * 2,  # Closed GOP every ~2s
        acodec='aac',
        audio_bitrate='128k',
        ar='48000',
        ac=2,
        movflags='+faststart'
    )

    ffmpeg.run(stream, overwrite_output=True)



def make_video_postable(video_path: str, text: str = None):
    try:
        
        video_path = Path(video_path)
        output_path = video_path.parent / (uuid.uuid4().hex + ".mp4")

        process_video(str(video_path), str(output_path))        
        
        shutil.move(str(output_path), str(video_path))

        return str(video_path)

    except Exception as err:
        log.exception(err)
