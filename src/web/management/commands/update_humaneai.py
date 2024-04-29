import json
from collections import namedtuple

import requests
from django.conf import settings
from django.core.management import BaseCommand
from django.template.loader import render_to_string
from requests.auth import HTTPBasicAuth
from web.models import Entry
from web.submissions_processing import merge_fields_with_submission_data

LabelOrder = namedtuple("LabelOrder", ["label", "type", "new_label"])

order_of_labels = [
    LabelOrder(
        "Results description (1000-4000 char): including how it addresses the call topics",
        "textarea",
        "Results Description",
    ),
    LabelOrder("List of pubications, if applicable", "textarea", "Publications"),
    LabelOrder(
        "Links to Tangible results: paper pdfs, videos, coder repositories etc.",
        "textarea",
        "Links to Tangible results",
    ),
]

UPDATES_TO_DO = [
    (1803, "437"),
    (2274, "384"),
    (1115, "445"),
    (1104, "440"),
    (1811, "443"),
    (1810, "400"),
    (1794, "441"),
    (2551, "406"),
    (2279, "382"),
    (1982, "393"),
    (1947, "383"),
    (1795, "447"),
    (1114, "510"),
    (1980, "386"),
    (1797, "390"),
    (2282, "442"),
    (1121, "388"),
    (1098, "450"),
    (1983, "430"),
    (2004, "377"),
    (2003, "417"),
    (1119, "425"),
    (1793, "439"),
]


def build_results_html(key: str):
    entry = Entry.objects.get(key=key, project_id=4)
    # print(f"   Entry:  #{entry.id} {entry.title}")
    submission = merge_fields_with_submission_data(
        fields=entry.project.fields,
        data=entry.data,
        excluded_labels=[],
    )

    final_submission = []
    for label_order in order_of_labels:
        for item in submission:
            if item["label"] == label_order.label and item["type"] == label_order.type:
                if label_order.new_label is not None:
                    item["label"] = label_order.new_label

                final_submission.append(item)

    return render_to_string("web/export/wp_humaneai.html", {"submission_data": final_submission})


class Command(BaseCommand):
    help = "Updates HumaneAI in Wordpress"
    session = requests.Session()

    def handle(self, *args, **options):
        self.session.auth = HTTPBasicAuth(settings.EXPORT_WP_USER, settings.EXPORT_WP_PASS)

        for post_id, entry_key_id in UPDATES_TO_DO:
            self.update_existing_section_with_results(post_id, entry_key_id)

    def get_existing_wp_section(self, post_id: int):
        url = f"{settings.EXPORT_HUMANEAI_WP_URL}/wp/v2/project/{post_id}"
        content = self.session.get(url).json()
        # print(f"WP Title: #{content['id']} {content['title']['rendered']}")
        return content.get("acf", {}).get("section", [])

    def update_existing_section_with_results(self, post_id: int, entry_key_id: str):
        sections = self.get_existing_wp_section(post_id)

        if not sections[0]["title"]:
            sections[0]["title"] = "Application"

        sections.append(
            {
                "section_content": [{"acf_fc_layout": "simple_content", "content": build_results_html(entry_key_id)}],
                "title": "Results",
            }
        )

        url = f"{settings.EXPORT_HUMANEAI_WP_URL}/wp/v2/project/{post_id}"

        response = self.session.post(
            url,
            data={"section": json.dumps(sections)},
        )
        # print(response.json()['guid']['rendered'].replace('https://www.humane-ai.eu', 'https://humaneai.local'))
        print(response.json()["guid"]["rendered"])
        print("\n\n")
