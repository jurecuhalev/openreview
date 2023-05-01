import time
from collections import namedtuple

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
    _taxonomy_cache = {}

    def handle(self, *args, **options):
        # self._load_ratings()
        self._export_entries()

    def _load_ratings(self):
        with open(
            "/Users/gandalf/freelance/1 Projects/ircai-globaltop100/2023 Analysis.xlsx",
            "rb",
        ) as fh:
            data = Dataset().load(fh.read(), headers=True)

        for entry in data.dict:
            self.reviews[entry["Entry ID"]] = entry

    def _get_or_create_taxonomy_item(self, slug, name, parent=None):
        key = f"{slug}_{name}_{parent}"
        if self._taxonomy_cache.get(key):
            return self._taxonomy_cache[key]

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

            self._taxonomy_cache[key] = response["id"]

            return response["id"]
        else:
            self._taxonomy_cache[key] = response[0]["id"]
            return response[0]["id"]

    def _export_entries(self):
        project = Project.objects.get(pk=2)

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
        year_parent_id = self._get_or_create_taxonomy_item(slug="score", name="Score")
        year_id = self._get_or_create_taxonomy_item(
            slug="2022", name="2022", parent=year_parent_id
        )

        LabelOrder = namedtuple("LabelOrder", ["label", "type", "new_label"])

        for entry in project.entry_set.filter(is_active=True)[:]:
            # score = entry.get_word_score()
            score = entry.get_fixed_score()
            if not score:
                print(f"Missing score for {entry.pk} - {entry.title}")
                continue

            excluded_labels = [
                # "Organisation Address",
                "Email Address",
                "Contact Number",
                "LinkedIn handle",
                "Twitter handle",
                "Nominator",
                "Name",
                "Job Title",
                # 2022 fields
                "Entry ID",
                "URL",
                "Prefix",
                "First",
                "Last",
                "Project",
                "Job Title",
                "Organisation",
                "Street Address",
                "Address Line 2",
                "City",
                "State / Province",
                "ZIP / Postal Code",
                "Email Address",
                "Secondary Email Address",
                "Contact Number",
                "LinkedIn handle",
                "Yes",
                "1. Excellence and Scientific Quality: Please detail the improvements made by the nominee or the nominees’ team or yourself if your applying for the award, and why they have been a success.",
                "2.	Scaling of impact to SDGs: Please detail how many citizens/communities and/or researchers/businesses this has had or can have a positive impact on, including particular groups where applicable and to what extent.",
                "3.	Scaling of AI solution: Please detail what proof of concept or implementations can you show now in terms of its efficacy and how the solution can be scaled to provide a global impact ad how realistic that scaling is.",
                "4.	Human Rights and Ethics aspect: Please detail the way the solution addresses any of the main ethical aspects, including trustworthiness, bias, gender issues, etc.",
                "5.	Business aspects: Plans for long-term success, leadership, team, diversity and inclusion:",
                "Middle",
                "Twitter handle",
                "Prototype password and username",
                "No",
                "If you are applying with the same project as in 2021, please briefly state the progress form last years application.",
                "Suffix",
                "Please describe Other",
                "Other",
                "Is this your first submission to the list?",
            ]
            submission = merge_fields_with_submission_data(
                fields=entry.project.fields,
                data=entry.data,
                excluded_labels=excluded_labels,
            )

            demo_links = set()
            order_of_links = [
                LabelOrder("Github", "website", None),
                LabelOrder("Open data repository", "website", None),
                LabelOrder("Prototype  or working demo", "website", None),
            ]
            for label_order in order_of_links:
                for item in submission:
                    if (
                        item["label"] == label_order.label
                        and item["type"] == label_order.type
                    ):
                        demo_links.add(item["value"])

            order_of_labels = [
                LabelOrder("Company or Institution", "text", None),
                LabelOrder("Category", "select", "Industry"),
                LabelOrder("Website", "website", None),
                LabelOrder("Organisation Address", "address", "Country"),
                LabelOrder(
                    "Category", "checkbox", "Sustainable Development Goals (SDGs)"
                ),
                LabelOrder("General description of the AI solution", "textarea", None),
                LabelOrder(
                    None,
                    "demo_links",
                    "Github, open data repository, prototype or working demo",
                ),
                LabelOrder("Publications", "textarea", None),
                LabelOrder(
                    "What is your main overall need at the moment:", "checkbox", "Needs"
                ),
            ]

            final_submission = []
            country = None
            industry = None
            sdgs = None
            for label_order in order_of_labels:
                for item in submission:
                    if (
                        item["label"] == label_order.label
                        and item["type"] == label_order.type
                    ):
                        if label_order.new_label:
                            item["label"] = label_order.new_label

                        if item["type"] == "address":
                            country_item = [
                                i for i in item["inputs"] if i["label"] == "Country"
                            ].pop()
                            del item["inputs"]
                            item["type"] = "text"
                            item["value"] = country_item["value"]
                            country = country_item["value"]

                        if item["label"] == "Industry":
                            industry = item["value"]

                        if item["label"] == "Sustainable Development Goals (SDGs)":
                            sdgs = [i["label"] for i in item["inputs"]]

                        final_submission.append(item)

                if label_order.type == "demo_links":
                    if demo_links:
                        custom_item = {
                            "label": label_order.new_label,
                            "type": "textarea",
                            "value": "\r\n".join(demo_links),
                        }
                        final_submission.append(custom_item)

            content = render_to_string(
                "web/export/wp_post.html", {"submission_data": final_submission}
            )
            print(content)

            # try:
            #     review = self.reviews[entry.pk]
            # except KeyError:
            #     print(f"Missing review for {entry.pk} - {entry.title}")
            #     continue

            taxonomies = [year_id]
            if country == "United States":
                country_slug = "usa"
            elif country == "United Kingdom":
                country_slug = "uk"
            else:
                country_slug = country

            country_id = self._get_or_create_taxonomy_item(
                slug=slugify(country_slug), name=country, parent=country_parent_id
            )
            taxonomies.extend([country_id])

            industry_id = self._get_or_create_taxonomy_item(
                slug=slugify(industry), name=industry, parent=industry_parent_id
            )
            taxonomies.extend([industry_id])

            sdg_ids = []
            for sdg_full in sdgs:
                sdg = sdg_full.split(":")[0].replace(" ", "")
                sdg_id = self._get_or_create_taxonomy_item(
                    slug=slugify(sdg), name=sdg, parent=sdg_parent_id
                )
                sdg_ids.append(sdg_id)
            taxonomies.extend(sdg_ids)

            if entry.is_special_mention():
                label = "Special Mention"
                special_mention_id = self._get_or_create_taxonomy_item(
                    slug=slugify(label), name=label, parent=word_score_parent_id
                )
                taxonomies.append(special_mention_id)

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
            response = self.session.post(
                settings.EXPORT_WP_URL,
                data=post_data,
            )
            print(response.content)
            time.sleep(0.1)
