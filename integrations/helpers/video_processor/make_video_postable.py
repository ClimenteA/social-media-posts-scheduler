import uuid
import shutil
import ffmpeg
from pathlib import Path
from core.logger import log


def has_audio_stream(video_path: str) -> bool:
    probe = ffmpeg.probe(video_path)
    return any(stream["codec_type"] == "audio" for stream in probe["streams"])


def process_video(video_path: str, output_path: str) -> None:
    width, height = 1080, 1920
    fps = 30
    max_duration = 90

    # Load input
    video_input = ffmpeg.input(video_path)

    # Trim and reset timestamps
    video = video_input.trim(start=0, end=max_duration).setpts("PTS-STARTPTS")

    # Scale to at least 1080x1920 then crop to exact frame
    video = (
        video.filter("scale", width, height, force_original_aspect_ratio="increase")
             .filter("crop", width, height)
             .filter("fps", fps=fps, round="up")
    )

    stream_kwargs = dict(
        format='mp4',
        vcodec='libx264',
        pix_fmt='yuv420p',
        video_bitrate='5M',
        r=fps,
        g=fps * 2,  # Closed GOP every ~2s
        movflags='+faststart'
    )

    if has_audio_stream(video_path):
        audio = video_input.audio
        stream = ffmpeg.output(
            video, audio, output_path,
            acodec='aac', audio_bitrate='128k', ar='48000', ac=2,
            **stream_kwargs
        )
    else:
        stream = ffmpeg.output(video, output_path, **stream_kwargs)

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
        return str(video_path)
