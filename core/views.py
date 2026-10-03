from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views import View


class HomeView(View):
    template_name = 'core/home.html'

    def get(self, request):
        return render(request, self.template_name)


@login_required
def dashboard(request):
    return render(request, 'core/dashboard.html')


def terms(request):
    return render(request, 'core/terms.html')


def privacy(request):
    return render(request, 'core/privacy.html')
