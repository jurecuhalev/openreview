# from django.shortcuts import render

from django.views.generic import ListView, DetailView
from icecream import ic

from web.forms import RatingForm
from web.models import Entry, RatingQuestion, RatingAnswer
from web.submissions_processing import merge_fields_with_submission_data


class EntryListView(ListView):
    model = Entry
    context_object_name = "entry_list"

    def get_queryset(self):
        return Entry.objects.filter(project__pk=self.kwargs["project"])


class EntryDetailView(DetailView):
    model = Entry
    context_object_name = "entry"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        entry = self.get_object()
        context["submission_data"] = merge_fields_with_submission_data(
            fields=entry.project.fields, data=entry.data
        )
        ic(context["submission_data"])

        questions = RatingQuestion.objects.filter(project=entry.project).order_by(
            "order"
        )
        answers = RatingAnswer.objects.filter(user=self.request.user, entry=entry)
        form = RatingForm(questions=questions, answers=answers)
        context["form"] = form

        return context
