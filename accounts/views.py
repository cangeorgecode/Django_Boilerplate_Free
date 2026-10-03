from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.urls import reverse
from django.contrib import messages
from django.conf import settings
from django.core.mail import send_mail

from .forms import AdminEmailForm


@staff_member_required
def admin_send_email(request):
    """Staff-only page: send an email to selected users or all users."""
    form = AdminEmailForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        subject = form.cleaned_data["subject"]
        body = form.cleaned_data["body"]

        if form.cleaned_data["recipients_mode"] == "all":
            recipients = User.objects.filter(is_active=True)
        else:
            # Server-side whitelist: only ids that resolve to real users.
            raw_ids = form.cleaned_data["user_ids"].split(",")
            try:
                ids = [int(i) for i in raw_ids if i.strip()]
            except ValueError:
                messages.error(request, "Invalid user selection.")
                return redirect("admin_send_email")
            recipients = User.objects.filter(pk__in=ids)

        sent, failed = 0, 0
        for user in recipients.iterator():
            if not user.email:
                failed += 1
                continue
            try:
                send_mail(
                    subject,
                    body,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                )
                sent += 1
            except Exception:
                failed += 1

        messages.success(request, f"Sent to {sent} user(s); {failed} failed.")
        return redirect("admin_send_email")

    context = {
        "form": form,
        "user_count": User.objects.filter(is_active=True).count(),
    }
    return render(request, "admin_send_email.html", context)


@login_required
def profile(request):
    context = {'user': request.user}
    return render(request, 'account/profile.html', context)


@login_required
def profile_delete_confirm(request):
    return HttpResponse(render_to_string('partials/delete_confirm.html', {'user': request.user}, request=request))


@login_required
def profile_delete(request):
    if request.method == 'POST':
        request.user.delete()
        return JsonResponse({}, status=200, headers={'HX-Redirect': reverse('home')})
    return redirect('profile')
