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

        for entry in entries:
            entry.reviewers.clear()

        entries_list_remove = entries_list[:]
        for reviewer in reviewers:
            selected_count = 0
            while selected_count < amount:
                random_entry_id = random.choice(entries_list_remove)
                random_entry = Entry.objects.get(pk=random_entry_id)

                if reviewer not in random_entry.reviewers.all():
                    ic(reviewer.user)
                    random_entry.reviewers.add(reviewer.user)
                    entries_list_remove.remove(random_entry_id)
                    selected_count += 1

                if not entries_list_remove:
                    entries_list_remove = entries_list[:]
