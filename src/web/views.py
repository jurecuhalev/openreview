# from django.shortcuts import render
from icecream import ic

from django.views.generic import ListView, DetailView
from django.contrib import messages
from django.views.generic.edit import FormMixin

from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.html import format_html


from web.forms import RatingForm
from web.models import Entry, RatingQuestion, RatingAnswer
from web.submissions_processing import merge_fields_with_submission_data


class EntryListView(LoginRequiredMixin, ListView):
    model = Entry
    context_object_name = "entry_list"

    def get_queryset(self):
        return Entry.objects.filter(project__pk=self.kwargs["project"])


class EntryDetailView(LoginRequiredMixin, DetailView, FormMixin):
    model = Entry
    template_name = "web/entry_detail.html"
    context_object_name = "entry"
    questions = None
    answers = None
    object = None

    def get_form(self, form_class=None):
        entry = self.get_object()
        self.questions = RatingQuestion.objects.filter(project=entry.project).order_by(
            "order"
        )
        self.answers = RatingAnswer.objects.filter(user=self.request.user, entry=entry)

        if self.request.POST:
            form = RatingForm(
                data=self.request.POST, questions=self.questions, answers=self.answers
            )

        else:
            form = RatingForm(questions=self.questions, answers=self.answers)

        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        entry = self.get_object()
        context["submission_data"] = merge_fields_with_submission_data(
            fields=entry.project.fields, data=entry.data
        )

        return context

    def post(self, request, *args, **kwargs):
        """
        Handle POST requests: instantiate a form instance with the passed
        POST variables and then check if it's valid.
        """
        self.object = self.get_object()
        form = self.get_form()

        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        data = form.cleaned_data
        for key, value in data.items():
            answer, is_created = RatingAnswer.objects.get_or_create(
                user=self.request.user,
                entry=self.get_object(),
                question=RatingQuestion.objects.get(pk=key),
            )
            answer.value = value
            answer.save()

        return super().form_valid(form)

    def get_success_url(self):
        entries_url = reverse_lazy(
            "entry-list",
            kwargs={
                "project": self.get_object().project.pk,
            },
        )
        message = format_html(
            'Your review has been saved. <a class="underline" href="{}">Review another</a>.',
            entries_url,
        )
        messages.add_message(
            self.request,
            messages.INFO,
            message,
        )
        return reverse_lazy(
            "entry-detail",
            kwargs={
                "project": self.get_object().project.pk,
                "pk": self.get_object().pk,
            },
        )
