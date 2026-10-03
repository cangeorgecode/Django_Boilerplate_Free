from django.contrib.auth.models import User
from django.core import mail
from django.test import Client, TestCase, override_settings
from django.urls import reverse

TEST_SETTINGS = override_settings(
    SECURE_SSL_REDIRECT=False,
    ALLOWED_HOSTS=["testserver"],
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    STORAGES={
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        }
    },
)


@TEST_SETTINGS
class AdminEmailTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user("staff", email="staff@example.com", password="x", is_staff=True)
        self.a = User.objects.create_user("a", email="a@example.com", password="x")
        self.b = User.objects.create_user("b", email="b@example.com", password="x")

    def test_requires_staff(self):
        client = Client()
        client.force_login(self.a)
        response = client.get(reverse("admin_send_email"))
        self.assertEqual(response.status_code, 302)

    def test_send_to_selected(self):
        client = Client()
        client.force_login(self.staff)
        response = client.post(
            reverse("admin_send_email"),
            {
                "subject": "Hello",
                "body": "Body text",
                "recipients_mode": "selected",
                "user_ids": f"{self.a.pk},{self.b.pk},999999",  # unknown id must be ignored
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 2)

    def test_send_to_all(self):
        client = Client()
        client.force_login(self.staff)
        response = client.post(
            reverse("admin_send_email"),
            {"subject": "Hello", "body": "Body text", "recipients_mode": "all", "user_ids": ""},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 3)  # staff + a + b

    def test_rejects_invalid_ids(self):
        client = Client()
        client.force_login(self.staff)
        response = client.post(
            reverse("admin_send_email"),
            {"subject": "H", "body": "B", "recipients_mode": "selected", "user_ids": "not-a-number"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 0)
