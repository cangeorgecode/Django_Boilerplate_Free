from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now
from wagtail.models import Page
from wagtail.fields import RichTextField

class UserPayment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    stripe_customer_id = models.CharField(max_length=255)
    stripe_checkout_id = models.CharField(max_length=255)
    stripe_product_id = models.CharField(max_length=255)
    product_name = models.CharField(max_length=255)
    quantity = models.IntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3)
    has_paid = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.product_name} - Paid: {self.price}"

class Subscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    stripe_customer_id = models.CharField(max_length=255)
    stripe_subscription_id = models.CharField(max_length=255)
    product_name = models.CharField(max_length=255)
    price = models.IntegerField()
    interval = models.CharField(max_length=50, default='month')
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(null=True, blank=True)
    canceled_at = models.DateTimeField(null=True, blank=True)

    @property
    def is_active(self):
        if self.end_date:
            if now() < self.end_date:
                return True
            else:
                return False
        else:
            return True

    @property
    def tier(self):
        tier_mapping = {
            'Test Product 3': 1,
        }
        tier = tier_mapping.get(self.product_name, None)
        return tier

    def __str__(self):
        return f"{self.user.username} - {self.product_name} - Active: {self.is_active}"

class HomePage(Page):
    body = RichTextField(blank=True)
    date = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    tag = RichTextField(blank=True)

    content_panels = Page.content_panels + ["body", "tag"]