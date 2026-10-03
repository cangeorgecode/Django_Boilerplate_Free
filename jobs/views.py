from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from billing.models import CreditAccount, CreditTransaction

from .forms import JobCreateForm
from .models import Job
from .tasks import process_job

JOB_CREDITS_COST = 1  # 1 credit = 1 video (locked pricing decision)


@login_required
def create(request):
    account = CreditAccount.get_or_create_for(request.user)
    form = JobCreateForm(request.POST or None, user=request.user)

    if request.method == "POST" and form.is_valid():
        from django.db import transaction

        # Create the job and spend its credit in ONE transaction so no orphan
        # job can exist without a matching ledger entry (or vice versa).
        with transaction.atomic():
            job = Job.objects.create(
                user=request.user,
                script=form.cleaned_data["script"],
                footage=form.cleaned_data.get("footage"),
                credits_cost=JOB_CREDITS_COST,
            )
            try:
                CreditAccount.spend(
                    request.user,
                    JOB_CREDITS_COST,
                    CreditTransaction.Reason.JOB_SPEND,
                    f"job:{job.pk}",
                )
            except ValueError:
                transaction.set_rollback(True)
                messages.error(
                    request,
                    "Not enough credits. Top up from your plan page to run more videos.",
                )
                return redirect("jobs:create")

        process_job.delay(job.pk)
        messages.success(request, "Your video is queued — we'll get to work.")
        return redirect("jobs:detail", job_id=job.pk)

    context = {
        "form": form,
        "credit_balance": account.balance,
        "cost": JOB_CREDITS_COST,
        "has_validated_footage": request.user.media_assets.filter(
            status="validated"
        ).exists(),
    }
    return render(request, "jobs/create.html", context)


@login_required
def list_jobs(request):
    jobs = request.user.jobs.order_by("-created_at")[:30]
    return render(request, "jobs/list.html", {"jobs": jobs})


@login_required
def detail(request, job_id):
    job = get_object_or_404(Job, pk=job_id, user=request.user)
    return render(request, "jobs/detail.html", {"job": job})


@login_required
def progress(request, job_id):
    job = get_object_or_404(Job, pk=job_id, user=request.user)
    return JsonResponse(
        {
            "status": job.status,
            "progress": job.progress,
            "error": job.error,
            "logs": (job.logs or [])[-20:],
            "output_id": job.output_id,
        }
    )
