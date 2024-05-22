from django.contrib.auth.models import User
from django.core.management import BaseCommand
from tablib import Dataset
from web.models import Project, UserProfile


class Command(BaseCommand):
    help = "imports reviewers"

    def add_arguments(self, parser):
        parser.add_argument(
            "filename",
            type=str,
            help="Filename of XLSX",
        )

        parser.add_argument(
            "--project",
            type=int,
            required=True,
            help="Internal project id",
        )

    def handle(self, *args, **options):
        with open(options.get("filename"), "rb") as fh:
            data = Dataset().load(fh.read())

        project = Project.objects.get(pk=options.get("project"))

        for row in data:
            if row[2] and "@" in row[2]:
                email = row[2].lower().strip()
                first_name = row[0]
                last_name = row[1]

                user, is_created = User.objects.get_or_create(
                    username=email,
                    defaults={
                        "first_name": first_name,
                        "last_name": last_name,
                        "email": email,
                        "is_active": True,
                    },
                )

                profile, is_created = UserProfile.objects.get_or_create(
                    user=user,
                )
                profile.projects.add(project)
