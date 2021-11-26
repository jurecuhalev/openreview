import time

import requests
from requests.auth import HTTPBasicAuth

from icecream import ic

from django.conf import settings
from django.core.management import BaseCommand
from django.template.loader import render_to_string

from web.models import Project
from web.submissions_processing import merge_fields_with_submission_data


class Command(BaseCommand):
    help = "Exports reviewed entries"

    def handle(self, *args, **options):
        self._export_entries()

    def _export_entries(self):
        project = Project.objects.latest("pk")

        for entry in project.entry_set.filter(is_active=True)[:1]:
            excluded_labels = [
                "Organisation Address",
                "Email Address",
                "Contact Number",
                "LinkedIn handle",
                "Twitter handle",
            ]
            submission = merge_fields_with_submission_data(
                fields=entry.project.fields,
                data=entry.data,
                excluded_labels=excluded_labels,
            )

            content = render_to_string(
                "web/export/wp_post.html", {"submission_data": submission}
            )

            post_data = {"title": entry.title, "status": "publish", "content": content}
            r = requests.post(
                settings.EXPORT_WP_URL,
                auth=HTTPBasicAuth(settings.EXPORT_WP_USER, settings.EXPORT_WP_PASS),
                data=post_data,
                verify=False,
            )
            time.sleep(1)
