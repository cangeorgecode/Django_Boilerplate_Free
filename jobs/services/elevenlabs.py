"""ElevenLabs text-to-speech for the uploaded script."""
import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

API_URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"


def configured():
    return bool(settings.ELEVENLABS_API_KEY and settings.ELEVENLABS_VOICE_ID)


def synthesize(script, output_path):
    headers = {
        "xi-api-key": settings.ELEVENLABS_API_KEY,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
    }
    payload = {
        "text": script,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
    }
    from .retry import retry_call
    response = retry_call(
        lambda: requests.post(
            API_URL.format(voice_id=settings.ELEVENLABS_VOICE_ID),
            headers=headers,
            json=payload,
            timeout=300,
        )
    )
    response.raise_for_status()
    with open(output_path, "wb") as fh:
        fh.write(response.content)
    return len(script), output_path
