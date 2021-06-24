import requests
from django.conf import settings
from django.core.management import BaseCommand
from icecream import ic

from web.models import Project, Entry


class Command(BaseCommand):
    help = "Imports Gravity Forms entries"

    def handle(self, *args, **options):
        self._import_entries()

    def _import_entries(self):
        entries_url = (
            settings.GFORMS_URL.format(settings.GFORMS_ID)
            + "/entries?paging[page_size]=300&_labels=1"
        )
        entries = requests.get(
            entries_url,
            auth=(settings.GFORMS_KEY, settings.GFORMS_SECRET),
        ).json()

        fields_url = settings.GFORMS_URL.format(settings.GFORMS_ID)
        fields = requests.get(
            fields_url,
            auth=(settings.GFORMS_KEY, settings.GFORMS_SECRET),
        ).json()

        project = Project.objects.latest("pk")
        project.fields = fields.get("fields")
        project.save()

        for raw_entry in entries.get("entries", []):
            # TODO: Make this dynamic lookup into fields
            title = raw_entry.get("30")
            key = raw_entry.get("id")
            entry, _ = Entry.objects.get_or_create(
                project=project, title=title, key=key
            )
            entry.data = raw_entry
            entry.save()
