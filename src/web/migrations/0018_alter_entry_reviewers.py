# Generated by Django 3.2.5 on 2021-10-19 10:32

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("web", "0017_alter_entry_options"),
    ]

    operations = [
        migrations.AlterField(
            model_name="entry",
            name="reviewers",
            field=models.ManyToManyField(blank=True, to=settings.AUTH_USER_MODEL),
        ),
    ]
