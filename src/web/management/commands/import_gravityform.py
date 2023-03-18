import requests
from django.conf import settings
from django.core.management import BaseCommand
from icecream import ic

from web.models import Project, Entry


class Command(BaseCommand):
    help = "Imports Gravity Forms entries"

    def handle(self, *args, **options):
        for project in Project.objects.filter(automatic_import=True):
            self._import_entries(project=project)

    def _import_entries(self, project: Project):
        entries_url = (
            project.gforms_url.format(project.gforms_id)
            + "/entries?paging[page_size]=300&_labels=1"
        )
        entries = requests.get(
            entries_url,
            auth=(project.gforms_key, project.gforms_secret),
        ).json()

        fields_url = project.gforms_url.format(project.gforms_id)
        fields = requests.get(
            fields_url,
            auth=(project.gforms_key, project.gforms_secret),
        ).json()

        if project.fields != fields.get("fields"):
            project.fields = fields.get("fields")
            project.save()

        for raw_entry in entries.get("entries", []):
            # TODO: Make this dynamic lookup into fields
            title = raw_entry.get(project.gforms_title_id)
            key = raw_entry.get("id")
            entry, _ = Entry.objects.get_or_create(
                project=project, title=title, key=key
            )
            entry.data = raw_entry
            entry.save()
            entry.auto_assign_reviewers()
