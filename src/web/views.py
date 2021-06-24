# from django.shortcuts import render

from django.views.generic import ListView, DetailView

from web.models import Entry
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

        return context
