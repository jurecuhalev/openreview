from django import forms
from icecream import ic

from .models import SiteSettings, RatingAnswer
from django_svg_image_form_field import SvgAndImageFormField

ONE_TO_TEN_CHOICES = [(str(i), str(i)) for i in range(1, 11)]


class SiteSettingsForm(forms.ModelForm):
    class Meta:
        model = SiteSettings
        exclude = []
        field_classes = {
            "logo": SvgAndImageFormField,
        }


class RatingForm(forms.Form):
    def __init__(self, data=None, questions=None, answers=None, *args, **kwargs):
        super(RatingForm, self).__init__(data, *args, **kwargs)

        for question in questions:
            try:
                answer = answers.get(question=question)
            except RatingAnswer.DoesNotExist:
                answer = None

            field_id = str(question.pk)
            initial_value = None
            if data and data.get(field_id):
                initial_value = data.get(field_id)
            elif answer:
                initial_value = answer.value

            if question.scale == "1-10":
                field = forms.ChoiceField(
                    label=question.title,
                    widget=forms.RadioSelect(attrs={"class": "form-radio"}),
                    choices=ONE_TO_TEN_CHOICES,
                )
            else:
                field = forms.CharField(label=question.title, widget=forms.Textarea)

            if question.is_required:
                field.required = True
            else:
                field.required = False
            ic(field.required)

            self.fields[field_id] = field
            self.initial[field_id] = initial_value
