from django import forms

from .models import SiteSettings
from django_svg_image_form_field import SvgAndImageFormField


class SiteSettingsForm(forms.ModelForm):
    class Meta:
        model = SiteSettings
        exclude = []
        field_classes = {
            "logo": SvgAndImageFormField,
        }
