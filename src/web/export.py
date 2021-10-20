import pandas as pd

from web.models import Project, RatingQuestion


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
