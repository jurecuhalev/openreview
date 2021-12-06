import time

import requests
from django.utils.text import slugify
from requests.auth import HTTPBasicAuth

from icecream import ic
from tablib import Dataset

from django.conf import settings
from django.core.management import BaseCommand
from django.template.loader import render_to_string

from web.models import Project
from web.submissions_processing import merge_fields_with_submission_data

requests.packages.urllib3.disable_warnings(
    requests.packages.urllib3.exceptions.InsecureRequestWarning
)


class Command(BaseCommand):
    help = "Exports reviewed entries"
    reviews = {}
    session = requests.Session()

    def handle(self, *args, **options):
        self._load_ratings()
        self._export_entries()

    def _load_ratings(self):
        with open(
            "/Users/gandalf/freelance/1 Projects/ircai-globaltop100/IRCAI top 100 Analysis.xlsx",
            "rb",
        ) as fh:
            data = Dataset().load(fh.read(), headers=True)

        for entry in data.dict:
            self.reviews[entry["Entry ID"]] = entry

    def _get_or_create_taxonomy_item(self, slug, name, parent=None):
        response = self.session.get(
            settings.EXPORT_WP_TAXONOMY_URL, params={"slug": slug}
        ).json()

        if not response:
            params = {"slug": slug, "name": name}

            if parent:
                params["parent"] = parent

            response = self.session.post(
                settings.EXPORT_WP_TAXONOMY_URL,
                params=params,
            ).json()
            return response["id"]
        else:
            return response[0]["id"]

    def _export_entries(self):
        project = Project.objects.latest("pk")

        self.session.auth = HTTPBasicAuth(
            settings.EXPORT_WP_USER, settings.EXPORT_WP_PASS
        )
        self.session.verify = False

        country_parent_id = self._get_or_create_taxonomy_item(
            slug="country", name="Country"
        )
        industry_parent_id = self._get_or_create_taxonomy_item(
            slug="industry", name="Industry"
        )
        sdg_parent_id = self._get_or_create_taxonomy_item(slug="sdg", name="SDGs")
        word_score_parent_id = self._get_or_create_taxonomy_item(
            slug="score", name="Score"
        )

        for entry in project.entry_set.filter(is_active=True)[:]:
            excluded_labels = [
                "Organisation Address",
                "Email Address",
                "Contact Number",
                "LinkedIn handle",
                "Twitter handle",
                "Nominator",
                "Name",
                "Job Title",
            ]
            submission = merge_fields_with_submission_data(
                fields=entry.project.fields,
                data=entry.data,
                excluded_labels=excluded_labels,
            )

            content = render_to_string(
                "web/export/wp_post.html", {"submission_data": submission}
            )

            try:
                review = self.reviews[entry.pk]
            except KeyError:
                print(f"Missing review for {entry.pk} - {entry.title}")
                continue

            taxonomies = []
            countries = []
            for country in review["Country"].split(","):
                country_id = self._get_or_create_taxonomy_item(
                    slug=slugify(country), name=country, parent=country_parent_id
                )
                countries.append(country_id)
            taxonomies.extend(countries)

            industries = []
            for industry in review["Category"].split(","):
                industry_id = self._get_or_create_taxonomy_item(
                    slug=slugify(industry), name=industry, parent=industry_parent_id
                )
                industries.append(industry_id)
            taxonomies.extend(industries)

            sdgs = []
            for sdg in review["SDGs Covered"].split(","):
                sdg_id = self._get_or_create_taxonomy_item(
                    slug=slugify(sdg), name=sdg, parent=sdg_parent_id
                )
                sdgs.append(sdg_id)
            taxonomies.extend(sdgs)

            score = entry.get_word_score()
            if not score:
                print(f"Missing score for {entry.pk} - {entry.title}")
                continue

            word_score_id = self._get_or_create_taxonomy_item(
                slug=slugify(score), name=score, parent=word_score_parent_id
            )
            taxonomies.append(word_score_id)

            post_data = {
                "title": entry.title,
                "status": "publish",
                "content": content,
                "gt_category[]": taxonomies,
            }
            self.session.post(
                settings.EXPORT_WP_URL,
                data=post_data,
            )
            time.sleep(0.1)
