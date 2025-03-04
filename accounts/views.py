from django.shortcuts import render, redirect, reverse
from django.contrib.auth.models import User
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string

@login_required
def profile(request):
    if not request.user.is_authenticated:
        return redirect(f'{settings.BASE_URL}{reverse("account_login")}?next={request.get_full_path()}')

    context = {
        'user': request.user
    }
    return render(request, 'account/profile.html', context)

def check_username(request):
    username = request.GET.get('username')
    user = User.objects.filter(username=username).first()
    if user is not None:
        return HttpResponse('<span class="text-red-500">Username is taken</span>', status=200)
    else:
        return HttpResponse('<span class="text-green-600">Username is available</span>', status=200)

@login_required
def profile_edit_form(request):
    return HttpResponse(render_to_string('account/profile_edit_form.html', {'user': request.user}))

@login_required
def profile_edit(request):
    if request.method == 'POST':
        user = request.user
        email = request.POST.get('email')
        current_password = request.POST.get('current_password')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        # Email Update
        if email and email != user.email:
            if not user.check_password(current_password):
                return HttpResponse("Invalid current password", status=400)
            user.email = email
            # If Allauth requires email verification, this triggers it
            from allauth.account.utils import send_email_confirmation
            send_email_confirmation(request, user, signup=False)

        # Password Update
        if password1 and password2:
            if not user.check_password(current_password):
                return HttpResponse("Invalid current password", status=400)
            if password1 != password2:
                return HttpResponse("Passwords don’t match", status=400)
            user.set_password(password1)
            update_session_auth_hash(request, user)  # Keeps user logged in after password change

        # Avatar Update
        if 'avatar' in request.FILES:
            user.profile.avatar = request.FILES['avatar']

        user.save()  # Saves User and triggers profile save via signal
        return HttpResponse(render_to_string('accounts/profile_display.html', {
            'user': user,
            'user_payment': user.payment_set.first()
        }))
    return redirect('profile')

@login_required
def profile_delete_confirm(request):
    return HttpResponse(render_to_string('partials/delete_confirm.html', {'user': request.user}))

@login_required
def profile_delete(request):
    if request.method == 'POST':
        user = request.user
        user.delete()
        return JsonResponse({}, status=200, headers={'HX-Redirect': reverse('account_logout')})
    return redirect('profile')