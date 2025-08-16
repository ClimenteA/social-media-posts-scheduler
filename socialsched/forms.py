from django import forms
from .models import PostModel


class PostForm(forms.ModelForm):
    class Meta:
        model = PostModel
        fields = "__all__"
        exclude = ["account_id"]

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
            "process_video": forms.CheckboxInput(attrs={"role":"switch"}),
            "tiktok_allow_comment": forms.CheckboxInput(),
            "tiktok_allow_duet": forms.CheckboxInput(),
            "tiktok_allow_stitch": forms.CheckboxInput(),
            "tiktok_disclose_video_content": forms.CheckboxInput(attrs={"role":"switch"}),
            "tiktok_your_brand": forms.CheckboxInput(),
            "tiktok_branded_content": forms.CheckboxInput(),
            "tiktok_ai_generated": forms.CheckboxInput(),
        }


    def clean(self):
        cleaned_data = super().clean()

        if cleaned_data.get("post_on_tiktok"):

            if cleaned_data.get("disclose_video_content"):
                if not any([cleaned_data.get("your_brand"), cleaned_data.get("branded_content")]):
                    self.add_error('disclose_video_content', "When Disclose video content is checked you need to choose 'Your Brand' or 'Branded Content' or both.")

            if cleaned_data.get("branded_content"):
                if cleaned_data.get("privacy_level_options") != "PUBLIC_TO_EVERYONE":
                    self.add_error("privacy_level_options", "When 'Branded Content' is checked only 'Public to Everyone' option is available.")

