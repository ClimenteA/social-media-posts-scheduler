from django.forms import ModelForm, CheckboxInput, DateTimeInput
from .models import PostModel


class PostForm(ModelForm):
    class Meta:
        model = PostModel
        fields = [
            "post_on_x",
            "post_on_instagram",
            "post_on_facebook",
            "post_on_linkedin",
            "description",
            "scheduled_on",
            "media_file",
            "post_timezone",
            "process_image",
        ]

        widgets = {
            "scheduled_on": DateTimeInput(
                format=("%Y-%m-%dT%H:%M"), attrs={"type": "datetime-local"}
            ),
            "post_on_x": CheckboxInput(),
            "post_on_instagram": CheckboxInput(),
            "post_on_facebook": CheckboxInput(),
            "post_on_linkedin": CheckboxInput(),
            "process_image": CheckboxInput(attrs={"role":"switch"}),
        }
