from django.shortcuts import render

from django.views.generic import ListView

from web.models import Entry


class EntryListView(ListView):
    model = Entry
    context_object_name = "entry_list"

    def get_queryset(self):
        return Entry.objects.filter(project__pk=self.kwargs["project"])
