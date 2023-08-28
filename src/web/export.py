from collections import OrderedDict

import pandas as pd
from icecream import ic

from web.models import Project
from web.submissions_processing import merge_fields_with_submission_data


def get_df_reviewers(project_pk: int) -> pd.DataFrame:
    project = Project.objects.get(pk=project_pk)

    reviewers = project.userprofile_set.all().order_by("user__last_name")
    reviewers_data = []
    for reviewer in reviewers:
        data = {
            "ID": reviewer.user.pk,
            "First name": reviewer.user.first_name,
            "Last name": reviewer.user.last_name,
            "Email": reviewer.user.email,
            "Is Admin": reviewer.user.is_staff,
        }
        reviewers_data.append(data)

    return pd.DataFrame(reviewers_data)


def get_df_entries(project_pk: int) -> pd.DataFrame:
    project = Project.objects.get(pk=project_pk)

    entries = project.entry_set.filter(is_active=True)
    entries_data = []
    for entry in entries:
        reviewers = []
        for reviewer in entry.get_reviewers():
            if reviewer["assigned"]:
                reviewers.append(reviewer["user"].get_full_name())

        data = {
            "Entry ID": entry.pk,
            "Title": entry.title,
            "URL": entry.get_full_url(),
            "Key": entry.key,
            "Reviewers": ", ".join(reviewers),
        }
        entries_data.append(data)

    return pd.DataFrame(entries_data)


def get_df_full_entries(project_pk: int) -> (pd.DataFrame, set):
    project = Project.objects.get(pk=project_pk)

    entries = project.entry_set.filter(is_active=True)
    entries_data = []
    limit_width_cols = set()

    for entry in entries:
        data = OrderedDict(
            {
                "Entry ID": entry.pk,
                "Title": entry.title,
                "URL": entry.get_full_url(),
            }
        )

        entry_data = merge_fields_with_submission_data(
            fields=entry.project.fields, data=entry.data, include_empty=True
        )

        for row in entry_data:
            if row.get("inputs", []):
                for input_row in row.get("inputs", []):
                    data[input_row["label_with_id"]] = input_row["value"]

                    if len(input_row["value"]) > 100:
                        limit_width_cols.add(input_row["label_with_id"])

            elif row.get("value"):
                data[row["label_with_id"]] = row["value"]

                if len(row["value"]) > 100:
                    limit_width_cols.add(row["label_with_id"])

            else:
                data[row["label_with_id"]] = ""

        entries_data.append(data)

    return pd.DataFrame(entries_data), limit_width_cols


def get_df_ratings(project_pk: int) -> pd.DataFrame:
    project = Project.objects.get(pk=project_pk)

    entries = project.entry_set.filter(is_active=True)
    ratings_data = []

    for entry in entries:
        ratings = entry.rating_set.all()
        for rating in ratings:
            data = {
                "Answer ID": rating.pk,
                "Entry ID": rating.entry.pk,
                "Entry": rating.entry.title,
                "Reviewer": rating.user.get_full_name(),
            }

            for answer in rating.answers.all().order_by("question__order"):
                data[answer.question.title] = answer.value

            ratings_data.append(data)

    return pd.DataFrame(ratings_data)


def get_df_ratings_avg(project_pk: int) -> pd.DataFrame:
    project = Project.objects.get(pk=project_pk)

    entries = project.entry_set.filter(is_active=True)
    ratings_data = []

    for entry in entries:
        scores = entry.get_average_ratings()
        number_of_reviews = entry.ratings()["reviewers_rated"]

        data = {
            "Entry ID": entry.pk,
            "Title": entry.title,
            "No. of reviews": number_of_reviews,
        }
        data.update(scores)

        ratings_data.append(data)

    df = pd.DataFrame(ratings_data)
    df = df.sort_values("Total Avg", ascending=False)

    return df
