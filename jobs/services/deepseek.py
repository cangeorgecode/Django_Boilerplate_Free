"""DeepSeek (agent stage): break the uploaded script into caption cues.

The LLM is treated as an untrusted transformer of user data: output is
validated, bounded, and falls back to a deterministic sentence splitter.
Transcribed/user text is ALWAYS sent as data, never as instructions.
"""
import json
import logging
import re

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def configured():
    return bool(settings.DEEPSEEK_API_KEY)


SYSTEM_PROMPT = (
    "You break narration scripts into short caption cues for a video. "
    "Output STRICT JSON only: {\"cues\": [{\"text\": \"...\"}, ...]}. "
    "Rules: each cue is one short clause (max ~10 Chinese characters or ~6 English "
    "words); keep all meaning; preserve the original language of the script; "
    "do not add or remove content."
)


def plan_captions(script):
    """Returns a list of cue strings. Never trusts raw LLM output blindly."""
    if not configured():
        return _deterministic_split(script)

    headers = {
        "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.DEEPSEEK_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": script},
        ],
        "temperature": 0.3,
        "max_tokens": 2000,
        "response_format": {"type": "json_object"},
    }
    try:
        from .retry import retry_call
        response = retry_call(
            lambda: requests.post(
                f"{settings.DEEPSEEK_BASE_URL}/chat/completions",
                headers=headers,
                json=payload,
                timeout=120,
            )
        )
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        parsed = json.loads(content)
        cues = [str(c.get("text", "")).strip() for c in parsed.get("cues", [])]
        cues = [c for c in cues if c]
        # Sanity: the cues must be a plausible partition of the script.
        joined = "".join(cues).replace(" ", "")
        source = script.replace(" ", "").replace("\n", "")
        if not cues or len(joined) < 0.7 * len(source):
            logger.warning("LLM caption plan failed sanity check; using deterministic split")
            return _deterministic_split(script)
        return cues
    except Exception:
        logger.exception("LLM caption planning failed; using deterministic split")
        return _deterministic_split(script)


def _deterministic_split(script):
    """Fallback: split on sentence punctuation, then long-clause breaks."""
    parts = re.split(r"(?<=[。！？!?.;；\n])", script.strip())
    cues = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        # Break very long clauses at commas.
        if len(part) > 24:
            for sub in re.split(r"(?<=[，,、])", part):
                sub = sub.strip()
                if sub:
                    cues.append(sub)
        else:
            cues.append(part)
    return cues or [script]
