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

    def full_name(self):
        if self.user.first_name and self.user.last_name:
            return "{} {}".format(self.user.first_name, self.user.last_name)

        return self.user.username


class Category(models.Model):
    name = models.CharField(max_length=120)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"


class ActiveEntriesManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)


class Entry(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    title = models.TextField()
    key = models.CharField(null=True, blank=True, max_length=120)

    category = models.ForeignKey(
        Category, blank=True, null=True, on_delete=models.CASCADE
    )

    data = models.JSONField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    reviewers = models.ManyToManyField(User)

    objects = models.Manager()
    active = ActiveEntriesManager()

    class Meta:
        verbose_name = "Entry"
        verbose_name_plural = "Entries"
        ordering = ["title", "key"]

    def __str__(self):
        return self.title

    def get_admin_url(self):
        return reverse_lazy(
            "admin:%s_%s_change" % (self._meta.app_label, self._meta.model_name),
            args=[self.id],
        )

    def ratings(self):
        reviewers_rated = self.rating_set.count()
        reviewers_total = self.reviewers.count()

        return {"reviewers_rated": reviewers_rated, "reviewers_total": reviewers_total}


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


class Rating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    entry = models.ForeignKey(Entry, on_delete=models.CASCADE)
    answers = models.ManyToManyField(RatingAnswer)

    changed = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "Rating for {}".format(self.entry)


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
