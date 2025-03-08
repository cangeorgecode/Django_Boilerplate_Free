from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now
from wagtail.models import Page
from wagtail.fields import RichTextField
from wagtail.admin.panels import FieldPanel

class BlogIndexPage(Page):
    intro = RichTextField(blank=True)
    content_panels = Page.content_panels + ["intro"]


class HomePage(Page):
    body = RichTextField(blank=True)
    date = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    tag = RichTextField(blank=True)

    content_panels = Page.content_panels + ["body", "tag"]

    parent_page_types = ['core.BlogIndexPage']

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context['blog_index_page'] = BlogIndexPage.objects.filter(slug='blog').live().first()
        return context