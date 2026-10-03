"""Deterministic ffmpeg assembly: footage + VO + burned captions -> 9:16 mp4."""
import json
import os
import shutil
import subprocess

from django.conf import settings


def ffmpeg_available():
    return shutil.which(settings.FFMPEG_BINARY) is not None


def probe_duration(path):
    result = subprocess.run(
        [settings.FFPROBE_BINARY, "-v", "error", "-show_entries",
         "format=duration", "-of", "json", path],
        capture_output=True, text=True, timeout=60,
    )
    result.check_returncode()
    return float(json.loads(result.stdout)["format"]["duration"])


def cues_to_srt(cues, total_duration):
    """Distribute total_duration across cues proportionally to text length."""
    weights = [max(len(c.replace(" ", "")), 1) for c in cues]
    total_weight = sum(weights)
    lines = []
    cursor = 0.0
    for index, (cue, weight) in enumerate(zip(cues, weights), start=1):
        duration = total_duration * weight / total_weight
        start, end = cursor, cursor + duration
        cursor = end
        text = cue.replace("\n", " ").strip()
        lines.append(
            f"{index}\n{_ts(start)} --> {_ts(end)}\n{text}\n"
        )
    return "\n".join(lines)


def _ts(seconds):
    ms = int(round((seconds - int(seconds)) * 1000))
    s = int(seconds) % 60
    m = (int(seconds) // 60) % 60
    h = int(seconds) // 3600
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def assemble(footage_path, vo_path, cues, workdir, output_path, tail_seconds=1.5):
    """Loop/crop footage to 9:16, mix the VO, burn captions, write the mp4."""
    vo_duration = probe_duration(vo_path)
    total_duration = vo_duration + tail_seconds

    srt_path = os.path.join(workdir, "captions.srt")
    with open(srt_path, "w", encoding="utf-8") as fh:
        fh.write(cues_to_srt(cues, vo_duration))

    width, height = settings.OUTPUT_VIDEO_WIDTH, settings.OUTPUT_VIDEO_HEIGHT
    filter_chain = (
        f"[0:v]scale={width}:{height}:force_original_aspect_ratio=increase,"
        f"crop={width}:{height},setsar=1,fade=t=in:st=0:d=0.4,"
        f"fade=t=out:st={vo_duration}:d={min(0.5, tail_seconds)}[v0];"
        f"[v0]subtitles=captions.srt:"
        "force_style='FontSize=54,Alignment=2,MarginV=260,Outline=2,Shadow=0'[v]"
    )
    command = [
        settings.FFMPEG_BINARY, "-y",
        "-stream_loop", "-1", "-i", footage_path,
        "-i", vo_path,
        "-filter_complex", filter_chain,
        "-map", "[v]", "-map", "1:a",
        "-t", f"{total_duration:.3f}",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        output_path,
    ]
    # Run from workdir so the relative 'captions.srt' path needs no escaping.
    process = subprocess.run(
        command, cwd=workdir, capture_output=True, text=True, timeout=1800
    )
    if process.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {process.stderr[-800:]}")
    return vo_duration, total_duration
