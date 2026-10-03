from celery import shared_task

from billing.models import CreditAccount, CreditTransaction
from .models import Job
from . import pipeline


@shared_task(bind=True, max_retries=0)
def process_job(self, job_id):
    job = Job.objects.get(pk=job_id)
    try:
        pipeline.run_pipeline(job)
    except Exception:
        # run_pipeline already marked the job failed; refund when nothing
        # external was consumed. Idempotent via the reference key.
        if pipeline.should_refund(job):
            try:
                CreditAccount.grant(
                    job.user,
                    job.credits_cost,
                    CreditTransaction.Reason.JOB_REFUND,
                    f"job:{job.pk}",
                )
                job.log("Credits refunded (job failed before work was consumed).")
            except Exception:
                pass
