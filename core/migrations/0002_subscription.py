# Generated by Django 5.1.4 on 2024-12-26 07:22

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Subscription',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('stripe_customer_id', models.CharField(max_length=255)),
                ('stripe_subscription_id', models.CharField(max_length=255)),
                ('product_name', models.CharField(max_length=255)),
                ('price', models.IntegerField()),
                ('interval', models.CharField(default='month', max_length=50)),
                ('start_date', models.DateTimeField(auto_now_add=True)),
                ('end_date', models.DateTimeField(blank=True, null=True)),
                ('canceled_at', models.DateTimeField(blank=True, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
