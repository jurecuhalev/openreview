from django.db import models
from django.contrib.auth.models import User
from django.db.models import JSONField


class Project(models.Model):
    name = models.CharField(max_length=120)

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


class Entry(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    title = models.TextField()
    key = models.CharField(null=True, blank=True, max_length=120)

    category = models.ForeignKey(Category, null=True, on_delete=models.CASCADE)

    data = JSONField(blank=True, null=True)

    class Meta:
        verbose_name = "Entry"
        verbose_name_plural = "Entries"

    def __str__(self):
        if self.key:
            return "#{} - {}".format(self.key, self.title)
        else:
            return self.title
