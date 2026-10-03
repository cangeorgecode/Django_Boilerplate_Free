"""Pipeline orchestration for faceless-explainer v1:

    upload footage + script
      -> Deepgram transcript (footage audio)
      -> DeepSeek/Hermes agent stage: script -> caption cues
      -> ElevenLabs TTS (script -> VO)
      -> ffmpeg assemble (footage + VO + burned captions -> 9:16 mp4)
      -> output saved to storage (R2 / local)

Every stage caches its artifact in the job workdir so a re-run resumes
without re-billing the expensive stages. All external services are
env-gated; a missing service fails the job with a clear message (and the
credits are refunded when no external API was consumed yet).
"""
import json
import logging
import os
import shutil
import uuid

from django.conf import settings
from django.core.files.base import ContentFile

from uploads import services as upload_services
from uploads.models import MediaAsset

from .models import Job
from .services import assembler, deepgram, deepseek, elevenlabs

logger = logging.getLogger(__name__)


def _local_footage_path(asset, workdir):
    """Footage as a local file path: copy from R2 or use the local disk path."""
    if upload_services.r2_enabled():
        local = os.path.join(workdir, "footage" + os.path.splitext(asset.object_key)[1])
        upload_services.download_to_file(asset.object_key, local)
        return local
    from django.core.files.storage import default_storage
    return default_storage.path(asset.object_key)


def _save_output(job, output_path):
    """Store the finished video in the media storage and create a MediaAsset."""
    extension = os.path.splitext(output_path)[1] or ".mp4"
    object_key = f"jobs/{job.user.pk}/{uuid.uuid4().hex}{extension}"
    if upload_services.r2_enabled():
        import boto3

        client = upload_services.get_client()
        client.upload_file(output_path, settings.R2_BUCKET_NAME, object_key)
    else:
        from django.core.files.storage import default_storage

        with open(output_path, "rb") as fh:
            default_storage.save(object_key, ContentFile(fh.read()))

    asset = MediaAsset.objects.create(
        user=job.user,
        object_key=object_key,
        original_name=f"video-{job.pk}{extension}",
        content_type="video/mp4",
        size=os.path.getsize(output_path),
        status=MediaAsset.Status.VALIDATED,
    )
    return asset


def run_pipeline(job):
    script = (job.script or "").strip()
    footage = job.footage

    # Pre-execution validation — failures here refund the credits.
    if not script:
        job.fail("The script is empty.")
        return
    if not footage or footage.status != MediaAsset.Status.VALIDATED:
        job.fail("The footage is missing or has not passed validation.")
        return
    if not assembler.ffmpeg_available():
        job.fail("ffmpeg is not installed on the worker.")
        return

    workdir = job.work_dir()
    breakdown = dict(job.cost_breakdown or {})

    try:
        local_footage = _local_footage_path(footage, workdir)
        if not os.path.exists(local_footage):
            job.fail("The footage file could not be found in storage.")
            return

        # Stage 1 — transcribe the footage audio (Deepgram).
        job.set_stage(Job.Status.TRANSCRIBING, 15)
        transcript_path = os.path.join(workdir, "transcript.json")
        if deepgram.configured():
            if upload_services.r2_enabled():
                url = upload_services.presign_get(footage.object_key)
                result = deepgram.transcribe_url(url)
            else:
                result = deepgram.transcribe_file(local_footage)
            breakdown["external_api_used"] = True
            breakdown["deepgram_minutes"] = round(deepgram.duration_minutes(result), 3)
            with open(transcript_path, "w", encoding="utf-8") as fh:
                json.dump(result, fh, ensure_ascii=False)
            job.log("Transcript ready.")
        else:
            job.log("Deepgram not configured — skipping transcription stage.")

        # Stage 2 — agent stage: script -> caption cues (DeepSeek + fallback).
        job.set_stage(Job.Status.PLANNING, 40)
        cues_path = os.path.join(workdir, "cues.json")
        if os.path.exists(cues_path):
            cues = json.load(open(cues_path, encoding="utf-8"))
        else:
            cues = deepseek.plan_captions(script)
            with open(cues_path, "w", encoding="utf-8") as fh:
                json.dump(cues, fh, ensure_ascii=False)
            breakdown["llm_chars"] = len(script)
        job.log(f"Caption plan ready ({len(cues)} cues).")

        # Stage 3 — voice the script (ElevenLabs). First billable-for-real stage:
        # from here on, failures do NOT refund credits.
        job.set_stage(Job.Status.VOICING, 60)
        vo_path = os.path.join(workdir, "vo.mp3")
        if not os.path.exists(vo_path):
            if not elevenlabs.configured():
                raise RuntimeError(
                    "Voice synthesis is not configured (ELEVENLABS_API_KEY / "
                    "ELEVENLABS_VOICE_ID missing)."
                )
            char_count, _ = elevenlabs.synthesize(script, vo_path)
            breakdown["external_api_used"] = True
            breakdown["tts_chars"] = char_count
        job.log("Voiceover ready.")

        # Stage 4 — assemble (ffmpeg, deterministic).
        job.set_stage(Job.Status.RENDERING, 80)
        output_path = os.path.join(workdir, "final.mp4")
        vo_duration, total_duration = assembler.assemble(
            local_footage, vo_path, cues, workdir, output_path
        )
        breakdown["ffmpeg_seconds"] = round(total_duration, 1)

        # Stage 5 — persist output.
        asset = _save_output(job, output_path)
        job.output = asset
        job.cost_breakdown = breakdown
        job.progress = 100
        job.status = Job.Status.DONE
        job.save(update_fields=["output", "cost_breakdown", "progress", "status", "updated_at"])
        job.log("Done.")
    except Exception as exc:
        job.cost_breakdown = breakdown
        job.save(update_fields=["cost_breakdown"])
        job.fail(str(exc))
        logger.exception("job %s failed", job.pk)
        raise
    finally:
        # Workdir is scratch — keep it for resume/debug in dev, prune later.
        pass


def should_refund(job):
    """Credits are refunded only when the job failed before any real external
    work was consumed (i.e. before the voice stage ran)."""
    if job.status != Job.Status.FAILED:
        return False
    return not (job.cost_breakdown or {}).get("external_api_used")
