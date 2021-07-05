from django import forms

from .models import SiteSettings
from django_svg_image_form_field import SvgAndImageFormField

ONE_TO_TEN_CHOICES = [(i, i) for i in range(1, 11)]


class SiteSettingsForm(forms.ModelForm):
    class Meta:
        model = SiteSettings
        exclude = []
        field_classes = {
            "logo": SvgAndImageFormField,
        }


class RatingForm(forms.Form):
    def __init__(self, questions=None, answers=None, *args, **kwargs):
        super(RatingForm, self).__init__(*args, **kwargs)

        for question in questions:
            if question.scale == "1-10":
                field = forms.ChoiceField(
                    label=question.title,
                    widget=forms.RadioSelect,
                    choices=ONE_TO_TEN_CHOICES,
                )

            else:
                field = forms.CharField(label=question.title, widget=forms.Textarea)

            if question.is_required:
                field.required = True

            self.fields[question.pk] = field
