"""Deepgram nova-3 transcription (batch, pre-recorded). Bilingual EN + zh-HK."""
import json
import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

API_URL = "https://api.deepgram.com/v1/listen"


def configured():
    return bool(settings.DEEPGRAM_API_KEY)


def transcribe_url(audio_url):
    """Transcribe a publicly fetchable URL (R2 presigned GET URL)."""
    params = {"model": settings.DEEPGRAM_MODEL, "smart_format": "true", "language": "zh-HK"}
    headers = {"Authorization": f"Token {settings.DEEPGRAM_API_KEY}"}
    payload = {"url": audio_url}
    from .retry import retry_call
    response = retry_call(
        lambda: requests.post(API_URL, params=params, headers=headers, json=payload, timeout=300)
    )
    response.raise_for_status()
    return response.json()


def transcribe_file(file_path):
    """Transcribe a local file (used in dev / eager mode)."""
    params = {"model": settings.DEEPGRAM_MODEL, "smart_format": "true", "language": "zh-HK"}
    headers = {"Authorization": f"Token {settings.DEEPGRAM_API_KEY}"}
    with open(file_path, "rb") as fh:
        from .retry import retry_call
        response = retry_call(
            lambda: requests.post(API_URL, params=params, headers=headers, data=fh, timeout=300)
        )
    response.raise_for_status()
    return response.json()


def extract_transcript(result):
    """Return (text, segments) where segments = [{start, end, text}]."""
    results = result.get("results") or {}
    channels = results.get("channels") or []
    segments = []
    full_text = []
    for channel in channels:
        alternatives = channel.get("alternatives") or []
        for alt in alternatives:
            for word in alt.get("words") or []:
                segments.append(
                    {
                        "start": float(word.get("start", 0)),
                        "end": float(word.get("end", 0)),
                        "text": word.get("punctuated_word") or word.get("word", ""),
                    }
                )
            full_text.append(alt.get("transcript", ""))
    return " ".join(full_text), segments


def duration_minutes(result):
    metadata = result.get("metadata") or {}
    return float(metadata.get("duration") or 0) / 60.0
