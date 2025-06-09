from django import forms
from .models import PostModel, TikTokPostModel

class TikTokForm(forms.ModelForm):
    class Meta:
        model = TikTokPostModel
        fields = "__all__"


class PostForm(forms.ModelForm):
    class Meta:
        model = PostModel
        fields = [
            "post_on_x",
            "post_on_instagram",
            "post_on_facebook",
            "post_on_tiktok",
            "post_on_linkedin",
            "description",
            "scheduled_on",
            "media_file",
            "post_timezone",
            "process_image",
        ]

        widgets = {
            "scheduled_on": forms.DateTimeInput(
                format=("%Y-%m-%dT%H:%M"), attrs={"type": "datetime-local"}
            ),
            "post_on_x": forms.CheckboxInput(),
            "post_on_instagram": forms.CheckboxInput(),
            "post_on_facebook": forms.CheckboxInput(),
            "post_on_tiktok": forms.CheckboxInput(),
            "post_on_linkedin": forms.CheckboxInput(),
            "process_image": forms.CheckboxInput(attrs={"role":"switch"}),
        }
