from django.core.management import BaseCommand
import random

from icecream import ic

from web.models import Entry, Project


class Command(BaseCommand):
    help = "assigns entries to reviewers"

    def add_arguments(self, parser):
        parser.add_argument(
            "--project",
            type=int,
            required=True,
            help="Internal project id",
        )

        # parser.add_argument(
        #     "--amount",
        #     type=int,
        #     required=True,
        #     help="How many entries per reviewer",
        # )

        parser.add_argument(
            "--amount",
            type=int,
            required=True,
            help="How many entries per paper",
        )

        parser.add_argument(
            "--dry",
            type=bool,
            required=False,
            help="Do dry run and print statistics",
        )

    def handle(self, *args, **options):
        amount = options.get("amount")
        project = Project.objects.get(pk=options.get("project"))
        reviewers = project.userprofile_set.filter(user__is_staff=False)
        entries = Entry.active.filter(project=project)

        reviewers_count = reviewers.count()
        entries_count = entries.count()
        entries_list = sorted(entries.values_list("pk", flat=True))

        self.stdout.write("Reviewers: {}".format(reviewers_count))
        self.stdout.write("Entries: {}".format(entries_count))

        for entry in Entry.objects.filter(project=project):
            entry.reviewers.clear()

        reviewers_counter = dict((reviewer.pk, 0) for reviewer in reviewers)
        max_reviewer_papers = round(entries_count * amount / reviewers_count)
        reviewers = list(reviewers)
        for entry in entries:
            entry_count = 0

            random.shuffle(reviewers)
            reviewers = sorted(reviewers, key=lambda reviewer: reviewers_counter[reviewer.pk])
            for reviewer in reviewers:
                if reviewers_counter[reviewer.pk] > max_reviewer_papers:
                    continue

                if entry_count < amount:
                    entry.reviewers.add(reviewer.user)
                    entry_count += 1
                    reviewers_counter[reviewer.pk] += 1
                else:
                    break

