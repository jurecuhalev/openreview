from django.db import models
from django.contrib.auth.models import User


class Project(models.Model):
    name = models.CharField(max_length=120)
    fields = models.JSONField(blank=True, null=True)

    is_active = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.PROTECT)
    projects = models.ManyToManyField(Project)
    is_active = models.BooleanField(default=True)


class Category(models.Model):
    name = models.CharField(max_length=120)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"


class Entry(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    title = models.TextField()
    key = models.CharField(null=True, blank=True, max_length=120)

    category = models.ForeignKey(Category, null=True, on_delete=models.CASCADE)

    data = models.JSONField(blank=True, null=True)

    class Meta:
        verbose_name = "Entry"
        verbose_name_plural = "Entries"

    def __str__(self):
        if self.key:
            return "#{} - {}".format(self.key, self.title)
        else:
            return self.title


QUESTION_SCALES = (
    ("1-10", "1 to 10"),
    ("text", "Text field"),
    ("bool", "Yes or no"),
)


class RatingQuestion(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    title = models.CharField(null=True, blank=True, max_length=120)
    description = models.TextField(blank=True)

    scale = models.CharField(choices=QUESTION_SCALES, max_length=64)
    has_na = models.BooleanField(default=False)
    is_required = models.BooleanField(default=False)

    order = models.IntegerField()


class RatingAnswer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    entry = models.ForeignKey(Entry, on_delete=models.CASCADE)

    value = models.TextField(blank=True, null=True)
    is_na = models.BooleanField(default=False)


class SiteSettings(models.Model):
    logo = models.ImageField(upload_to="public", blank=True)

    class Meta:
        verbose_name = "Site Settings"
        verbose_name_plural = "Site Settings"
