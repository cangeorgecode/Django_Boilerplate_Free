from django.shortcuts import render, redirect, reverse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.urls import reverse
from django.views import View
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
import logging
import os
import stripe
import json

stripe.api_key = settings.STRIPE_SECRET_KEY

# Configure logging
log_file_path = os.path.join(settings.BASE_DIR, 'logs', 'app.log')  # Path to the log file
os.makedirs(os.path.dirname(log_file_path), exist_ok=True)  # Ensure the directory exists

logging.basicConfig(
    filename=log_file_path,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

class HomeView(View):
    template_name = 'core/home.html'  # your combined home + pricing page

    def get(self, request):
        # Show the home/pricing page with the "Buy Now" button
        return render(request, self.template_name)

    def post(self, request):
        # This handles the "Buy Now" form submission
        try:
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],  # add 'sepa_debit', etc. if needed
                line_items=[
                    {
                        'price': settings.STRIPE_PRICE_ID,  # e.g., 'price_1ABC123...'
                        'quantity': 1,
                    }
                ],
                mode='payment',
                success_url=request.build_absolute_uri(reverse('success')) + '?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=request.build_absolute_uri(reverse('home')),
            )
            return redirect(checkout_session.url, code=303)
        except Exception as e:
            return render(request, self.template_name, {
                'error': 'Something went wrong. Please try again.'
            })

def success_view(request):
    session_id = request.GET.get('session_id')
    if not session_id:
        return redirect('home')

    try:
        session = stripe.checkout.Session.retrieve(session_id)
        if session.payment_status == 'paid':
            return render(request, 'core/success.html', {
                'session_id': session_id,
                'email': session.customer_details.email if session.customer_details else None,
            })
    except stripe.error.StripeError:
        pass

    return redirect('home')

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError:
        print('invalid header')
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        print('invalid sig')
        return HttpResponse(status=400)

    # Handle the checkout.session.completed event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        handle_successful_payment(session)

    return HttpResponse(status=200)


def handle_successful_payment(session):
    payment_intent = session.get('payment_intent')
    customer_email = session.get('customer_details', {}).get('email')
    amount_total = session.get('amount_total')  # in cents
    session_id = session['id']

    logger.info(f"Payment successful - Session: {session_id} | Email: {customer_email} | Amount: ${amount_total / 100:.2f}")

    try:
        # Your real fulfillment here (uncomment and customize)
        # send_download_email(customer_email, session_id)
        # generate_license_and_email(customer_email)
        # ...

        logger.info(f"Fulfillment completed for session {session_id}")
    except Exception as exc:
        logger.exception(f"Fulfillment failed for session {session_id}")
        # Optionally notify yourself (Sentry, email, etc.)

def dashboard(request):
    return render(request, 'core/dashboard.html')

def terms(request):
    return render(request, 'core/terms.html')

def privacy(request):
    return render(request, 'core/privacy.html')