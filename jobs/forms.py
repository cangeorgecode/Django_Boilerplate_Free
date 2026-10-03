from django import forms

from uploads.models import MediaAsset


class JobCreateForm(forms.Form):
    """Explicit whitelist. Script and footage are the only accepted fields."""

    script = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 10, "class": "textarea textarea-bordered w-full"}),
        max_length=20000,
        required=True,
        label="Your script",
    )
    footage = forms.ModelChoiceField(
        queryset=MediaAsset.objects.none(),
        required=False,
        label="Footage",
        empty_label="(no footage selected)",
        widget=forms.Select(attrs={"class": "select select-bordered w-full"}),
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None:
            self.fields["footage"].queryset = user.media_assets.filter(
                status=MediaAsset.Status.VALIDATED
            ).order_by("-created_at")
