import uuid

from django.db import models
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.core.mail import send_mail


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
    changed = models.DateTimeField(auto_now=True)


class RatingAnswer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    entry = models.ForeignKey(Entry, on_delete=models.CASCADE)
    question = models.ForeignKey(RatingQuestion, on_delete=models.CASCADE)

    value = models.TextField(blank=True, null=True)
    is_na = models.BooleanField(default=False)


class SiteSettings(models.Model):
    logo = models.ImageField(upload_to="public", blank=True)
    name = models.CharField(max_length=255, default="Open Review System", blank=True)
    email = models.EmailField(max_length=255, default="")
    url = models.TextField(
        default="http://localhost:8000", help_text="URL without ending slash"
    )

    class Meta:
        verbose_name = "Site Settings"
        verbose_name_plural = "Site Settings"


class LoginKey(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    email = models.EmailField()
    key = models.CharField(max_length=32)

    used = models.BooleanField(default=False)
    pub_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "{} - {}".format(self.user, self.email)

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = uuid.uuid4().hex

        super(LoginKey, self).save(*args, **kwargs)

    def send_email(self):
        settings = SiteSettings.objects.latest("pk")
        body = render_to_string(
            "mail-login/mail_body.txt",
            {"url": self.get_absolute_url(), "email": settings.email},
        )
        send_mail(
            "{} login information".format(settings.name),
            body,
            settings.email,
            [self.email],
        )

    def get_absolute_url(self):
        settings = SiteSettings.objects.latest("pk")
        return settings.url + reverse_lazy("login-key-check", kwargs={"key": self.key})
