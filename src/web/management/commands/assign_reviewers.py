from django.core.management import BaseCommand
from django.contrib.auth.models import User
from icecream import ic
import random

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

        parser.add_argument(
            "--amount",
            type=int,
            required=True,
            help="How many entries per reviewer",
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

        entries_list_remove = entries_list[:]
        for reviewer in reviewers:
            if len(entries_list_remove) < amount:
                for entry_id in entries_list_remove:
                    Entry.objects.get(pk=entry_id).reviewers.add(reviewer.user)

                entries_list_remove = entries_list[:]
                entries_sample = random.sample(
                    entries_list_remove, amount - len(entries_list_remove)
                )
            else:
                entries_sample = random.sample(entries_list_remove, amount)

            for entry_id in entries_sample:
                Entry.objects.get(pk=entry_id).reviewers.add(reviewer.user)
                entries_list_remove.remove(entry_id)
