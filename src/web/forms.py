from django import forms
from django.contrib.auth.models import User
from icecream import ic

from .models import SiteSettings, RatingAnswer, RatingQuestion, Rating
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

            self.fields[field_id] = field
            self.initial[field_id] = initial_value

    def save(self, user, entry):
        data = self.cleaned_data

        rating, is_created = Rating.objects.get_or_create(user=user, entry=entry)
        rating.answers.clear()
        for key, value in data.items():
            key = RatingQuestion.objects.get(pk=key)
            answer, is_created = RatingAnswer.objects.get_or_create(
                user=user,
                entry=entry,
                question=key,
            )
            answer.value = value
            answer.save()
            rating.answers.add(answer)

        return rating


class LoginForm(forms.Form):
    email = forms.EmailField(
        widget=forms.TextInput(attrs={"class": "form-input w-3/4"})
    )

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email", "").strip()

        if not User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "Email you entered is not in our system. Please contact support.",
                code="invalid-email",
            )

        return cleaned_data
