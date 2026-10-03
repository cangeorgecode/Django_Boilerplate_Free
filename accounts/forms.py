from django import forms


class AdminEmailForm(forms.Form):
    """Explicit field whitelist — only these fields are accepted."""

    subject = forms.CharField(max_length=200, required=True)
    body = forms.CharField(widget=forms.Textarea(attrs={"rows": 12}), required=True)
    recipients_mode = forms.ChoiceField(
        choices=[("selected", "Selected users"), ("all", "All users")],
        initial="selected",
        required=True,
    )
    user_ids = forms.CharField(required=False, widget=forms.HiddenInput)
