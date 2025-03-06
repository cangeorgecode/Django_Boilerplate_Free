from django.shortcuts import render, redirect, reverse
from django.contrib.auth.models import User
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from django.contrib.auth import update_session_auth_hash

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
def change_password_form(request):
    context = {'user': request.user}
    return HttpResponse(render_to_string('account/change_password_form.html', context, request=request))

@login_required
def change_email_form(request):
    context = {'user': request.user}
    return HttpResponse(render_to_string('account/change_email_form.html', context, request=request))

@login_required
def change_email(request):
    if request.method == 'POST':
        user = request.user
        email = request.POST.get('email')
        current_password = request.POST.get('current_password')

        if email and email != user.email:
            if not user.check_password(current_password):
                messages.error(request, "Invalid current password")
            else:
                user.email = email
                user.save()
                # Trigger email verification if using Allauth
                send_email_confirmation(request, user, signup=False)
                messages.success(request, 'Email change requested. Please check your inbox.')
                
        context = {
            'user': user,
            'messages': messages.get_messages(request),
        }
        return HttpResponse(render_to_string('partials/profile_display.html', context))
    return redirect('profile')

@login_required
def change_password(request):
    if request.method == 'POST':
        user = request.user
        current_password = request.POST.get('current_password')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        if password1 and password2:
            if not user.check_password(current_password):
                messages.error(request, "Invalid current password")
            elif password1 != password2:
                messages.error(request, "Passwords don’t match")
            else:
                user.set_password(password1)
                user.save()
                update_session_auth_hash(request, user)  # Keep user logged in
                messages.success(request, 'Password changed successfully!')
        
        context = {
            'user': user,
            'messages': messages.get_messages(request),
        }
        return HttpResponse(render_to_string('partials/profile_display.html', context))
    return redirect('profile')

@login_required
def change_avatar(request):
    if request.method == 'POST':
        user = request.user
        # Avatar Update
        if 'avatar' in request.FILES:
            user.profile.avatar = request.FILES['avatar']
            user.save()  # Saves User and triggers profile save via signal

        context = {
            'user': user,
            'messages': messages.get_messages(request),  # Fetch queued messages
        }
        return HttpResponse(render_to_string('partials/profile_display.html', context))
    return redirect('profile')

@login_required
def profile_delete_confirm(request):
    return HttpResponse(render_to_string('partials/delete_confirm.html', {'user': request.user}, request=request))

@login_required
def profile_delete(request):
    if request.method == 'POST':
        user = request.user
        user.delete()
        return JsonResponse({}, status=200, headers={'HX-Redirect': reverse('index')})
    return redirect('profile')

@login_required
def profile_display(request):
    print('cancel pressed')
    return HttpResponse(render_to_string('partials/profile_display.html', {'user': request.user}))

@login_required
def profile_edit_blank(request):
    return HttpResponse(render_to_string('partials/profile_edit_form_blank.html', {'user': request.user}))