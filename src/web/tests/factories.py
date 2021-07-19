import factory

from django.contrib.auth.models import User
from factory import post_generation
from icecream import ic

from web.models import UserProfile


class EntryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "web.Entry"

    title = factory.Faker("catch_phrase")
    key = factory.Sequence(int)


class ReviewerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Faker("ascii_company_email")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    email = factory.Faker("ascii_company_email")

    @post_generation
    def create_profile_with_project(self, create, project, **kwargs):
        if not create:
            return

        profile = UserProfile.objects.create(user=self, is_active=True)
        profile.projects.add(project)
