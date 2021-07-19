import pytest
from icecream import ic

from web.models import Project
from web.tests.factories import EntryFactory, ReviewerFactory


@pytest.fixture(scope="module")
def project_factory(django_db_blocker):
    def create_project(
        name="Example project", number_of_entries=25, number_of_reviewers=10
    ) -> Project:
        with django_db_blocker.unblock():
            project = Project.objects.create(name=name)

            for i in range(0, number_of_entries):
                EntryFactory(project=project)

            for i in range(0, number_of_reviewers):
                ReviewerFactory(create_profile_with_project=project)

            return project

    return create_project


@pytest.fixture(scope="module")
def project_mid_review(project_factory):
    return project_factory(name="Mid-review")


def test_project(db, project_mid_review):
    project = project_mid_review
    ic(project)
    assert project.name == "Mid-review"
    assert project.entry_set.count() == 25
    assert project.userprofile_set.count() == 10
