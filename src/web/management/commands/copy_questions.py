from django.core.management import BaseCommand
from web.models import Project, RatingQuestion


class Command(BaseCommand):
    """
    Example usage: `./manage.py copy_questions --src 2 --dst 5`
    """

    help = "Copy all Rating Questions from one Project to another"

    def add_arguments(self, parser):
        parser.add_argument(
            "--src",
            type=int,
            required=True,
            help="Source project ID",
        )

        parser.add_argument(
            "--dst",
            type=int,
            required=True,
            help="Destionation project ID",
        )

    def handle(self, *args, **options):
        source_project = Project.objects.get(pk=options.get("src"))
        destination_project = Project.objects.get(pk=options.get("dst"))

        for question in source_project.ratingquestion_set.all():
            destination_question = RatingQuestion.objects.create(
                project=destination_project,
                title=question.title,
                description=question.description,
                scale=question.scale,
                num_of_options=question.num_of_options,
                has_na=question.has_na,
                is_required=question.is_required,
                order=question.order,
            )
            self.stdout.write(f"Created {destination_question}")
