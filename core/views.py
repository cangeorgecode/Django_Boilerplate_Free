from django.shortcuts import render, redirect, reverse
import stripe
from django.conf import settings
from .models import *
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.contrib import messages
import logging
import os

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

def index(request):
    # Product 1
    product_id = settings.TEST_PRODUCT_ID_1
    product = stripe.Product.retrieve(product_id)
    prices = stripe.Price.list(product=product_id)
    price = prices.data[0]
    product_price = price.unit_amount / 100

    # Product 2
    product_2_id = settings.TEST_PRODUCT_ID_2
    product_2 = stripe.Product.retrieve(product_2_id)
    prices_2 = stripe.Price.list(product=product_2_id)
    price_2 = prices_2.data[0]
    product_2_price = price_2.unit_amount / 100

    # Subscription
    # sub_product_id = 'prod_RT5LsY8GOdMCQi'
    # sub_product = stripe.Product.retrieve(sub_product_id)
    # prices = stripe.Price.list(product=sub_product_id)
    # sub_price = prices.data[0]
    # sub_product_price = sub_price.unit_amount / 100

    if request.method == "POST":
        if not request.user.is_authenticated:
            messages.error(request, 'Login first, brother')
            return redirect(f'{settings.BASE_URL}{reverse("account_login")}?next={request.get_full_path()}')

        price_id = request.POST.get('price_id')
        mode = request.POST.get('mode')

        customer = None
        if mode == 'subscription':
            customer = stripe.Customer.create(
                email = request.user.email,
                name = request.user.get_full_name(),
            )

        checkout_session = stripe.checkout.Session.create(
            customer = customer.id if customer else None,
            line_items=[
                {
                    'price': price_id,
                    'quantity': 1,
                },
            ],
            payment_method_types=[
                'card',
            ],
            mode=mode,
            customer_creation='always' if mode == 'payment' else None,
            success_url=f'{settings.BASE_URL}{reverse("payment_successful")}?session_id={{CHECKOUT_SESSION_ID}}',
            cancel_url=f'{settings.BASE_URL}{reverse("payment_cancelled")}',
            ) 
        return redirect(checkout_session.url, code=303)

    return render(request, 'core/index.html', {
        'product': product,
        'product_2': product_2,
        'price': product_price,
        'price_2': product_2_price,
    })

def payment_successful(request):
    checkout_session_id = request.GET.get('session_id')

    if checkout_session_id:
        session = stripe.checkout.Session.retrieve(checkout_session_id)
        customer_id = session.customer
        customer = stripe.Customer.retrieve(customer_id)

        line_items = stripe.checkout.Session.list_line_items(checkout_session_id).data

        # Create a user payment object in the database. 
        if session.mode == 'payment':
            for line_item in line_items:
                # line_item = stripe.checkout.Session.list_line_items(checkout_session_id).data[0]
                UserPayment.objects.get_or_create(
                    user = request.user,
                    stripe_customer_id = customer_id,
                    stripe_checkout_id = checkout_session_id,
                    stripe_product_id = line_item.price.product,
                    product_name = line_item.description,
                    quantity = line_item.quantity,
                    price = line_item.price.unit_amount / 100,
                    currency = line_item.price.currency,
                    has_paid = True,
                )
        elif session.mode == 'subscription':
            for line_item in line_items:
                Subscription.objects.get_or_create(
                    user = request.user,
                    stripe_customer_id = customer_id,
                    stripe_subscription_id = session.subscription,
                    product_name = line_item.description,
                    price = line_item.price.unit_amount / 100,
                    interval = line_item.price.recurring.interval,
                )

    return render(request, 'core/payment_successful.html', {'customer': customer})

def payment_cancel(request):
    return render(request, 'core/payment_cancel.html')

@require_POST
@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_ENDPOINT_SECRET
        )
    except ValueError as e:
        # Invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return HttpResponse(status=400)

    # Handle the event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        checkout_session_id = session.get('id')
        user_payment = UserPayment.objects.get(stripe_checkout_id=checkout_session_id)
        user_payment.has_paid = True
        user_payment.save()

    return HttpResponse(status=200)

def pricing(request):
    return render(request, 'core/pricing.html')