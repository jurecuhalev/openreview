# Generated by Django 3.2.5 on 2021-07-26 13:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("web", "0013_rating"),
    ]

    operations = [
        migrations.AddField(
            model_name="entry",
            name="is_active",
            field=models.BooleanField(default=True),
        ),
    ]
