import statistics
import uuid

from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db import models
from django.db.models import Q
from django.template.loader import render_to_string
from django.urls import reverse_lazy

from web.submissions_processing import extract_search_text


class Project(models.Model):
    name = models.CharField(max_length=120)
    fields = models.JSONField(blank=True, null=True)

    is_active = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)

    gforms_key = models.CharField(max_length=50, default="")
    gforms_secret = models.CharField(max_length=50, default="")
    gforms_url = models.CharField(max_length=120, default="")
    gforms_id = models.IntegerField(blank=True, null=True)
    gforms_title_id = models.CharField(blank=True, null=True, max_length=10)

    automatic_import = models.BooleanField(
        default=False,
        help_text="Tries to automatically import new entries from Gravity Forms every N minutes",
    )
    assign_reviewers = models.BooleanField(
        default=False,
        help_text="Assigns all users that have access to project to be reviewers for newly imported entries",
    )

    def __str__(self):
        return self.name


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
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

    category = models.ForeignKey(Category, blank=True, null=True, on_delete=models.CASCADE)

    data = models.JSONField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    reviewers = models.ManyToManyField(User, blank=True)

    objects = models.Manager()
    active = ActiveEntriesManager()

    search_text = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Entry"
        verbose_name_plural = "Entries"
        ordering = ["title", "key"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        self.search_text = extract_search_text(self)
        super().save(*args, **kwargs)

    @property
    def extracted_search_text(self):
        text = extract_search_text(self)
        return text

    def get_full_url(self):
        site_settings = SiteSettings.objects.latest("pk")
        return site_settings.url + reverse_lazy("entry-detail", kwargs={"project": self.project.pk, "pk": self.pk})

    def get_admin_url(self):
        return reverse_lazy(
            "admin:%s_%s_change" % (self._meta.app_label, self._meta.model_name),
            args=[self.id],
        )

    def ratings(self):
        reviewers_rated = self.rating_set.count()
        reviewers_total = self.reviewers.count()

        return {"reviewers_rated": reviewers_rated, "reviewers_total": reviewers_total}

    def get_reviewers(self):
        reviewers = []
        for user in User.objects.filter(is_staff=False, userprofile__projects=self.project).order_by("first_name"):
            reviewers.append({"user": user, "assigned": self.reviewers.filter(pk=user.pk).exists()})
        return reviewers

    def get_average_ratings(self):
        scores = {}
        total_avg_keys = set()
        for rating in self.ratinganswer_set.filter(Q(question__scale="1-10") | Q(question__include_in_statistics=True)):
            title = rating.question.title

            try:
                value = int(rating.value)
            except ValueError:
                continue
            try:
                scores[title].append(value)
            except KeyError:
                scores[title] = [value]

            if rating.question.scale == "1-10":
                total_avg_keys.add(title)

        scores_avg = {}
        total = []
        for key, value in scores.items():
            if key in total_avg_keys:
                total += value

            scores_avg[key] = round(statistics.mean(value), 2)

        if total:
            scores_avg["Total Avg"] = round(statistics.mean(total), 2)
        else:
            scores_avg["Total Avg"] = 0

        return scores_avg

    def get_word_score(self):
        avg_ratings = self.get_average_ratings()
        total = avg_ratings.get("Total Avg")

        if not total:
            return "N/A"

        if total >= 8.67 and self.pk != 51:
            return "Outstanding"
        elif total >= 8:
            return "Excellent"
        elif total >= 6:
            return "Promising"
        else:
            return "Early stage"

    def get_fixed_score(self):
        # IDs for 2023
        scores = {
            "Outstanding": [135, 153, 211, 121, 123, 180, 204, 145, 185, 218],
            "Excellent": [
                162,
                155,
                224,
                201,
                119,
                195,
                197,
                198,
                179,
                165,
                157,
                120,
                146,
                161,
                217,
                183,
                213,
                149,
                124,
                154,
            ],
            "Promising": [
                126,
                219,
                210,
                214,
                192,
                215,
                130,
                139,
                159,
                144,
                151,
                206,
                190,
                177,
                212,
                203,
                163,
                136,
                199,
                228,
                184,
            ],
            "Early stage": [
                133,
                216,
                182,
                129,
                173,
                132,
                208,
                156,
                178,
                160,
                137,
                118,
                122,
                220,
                181,
                189,
                164,
                174,
                188,
                140,
                221,
                167,
                152,
                125,
                128,
                170,
                222,
                191,
                142,
                194,
                158,
                205,
                131,
                176,
                187,
                186,
                134,
                227,
                207,
                147,
                138,
                171,
                223,
                209,
                169,
                166,
                202,
                141,
                175,
            ],
        }

        for key, values in scores.items():
            if self.id in values:
                return key

    def is_special_mention(self):
        if self.id in [149, 154, 163]:
            return True

    def auto_assign_reviewers(self):
        if self.project.assign_reviewers:
            for profile in self.project.userprofile_set.filter(user__is_staff=False):
                self.reviewers.add(profile.user)


QUESTION_SCALES = (
    ("1-10", "1 to 10"),
    ("1-N", "1 to N"),
    ("text", "Text field"),
    ("bool", "Yes or no"),
)


class RatingQuestion(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    title = models.CharField(null=True, blank=True, max_length=120)
    description = models.TextField(blank=True)

    scale = models.CharField(choices=QUESTION_SCALES, max_length=64)
    num_of_options = models.IntegerField(null=True, blank=True, help_text="If 1 to N scale, define N >= 2 here")
    has_na = models.BooleanField(default=False)
    is_required = models.BooleanField(default=False)
    include_in_statistics = models.BooleanField(default=False, help_text="Include 1 to N scale question in statistics")

    order = models.IntegerField()
    changed = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.project} / {self.title}"


class RatingAnswer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    entry = models.ForeignKey(Entry, on_delete=models.CASCADE)
    question = models.ForeignKey(RatingQuestion, on_delete=models.CASCADE)

    value = models.TextField(blank=True, null=True)
    is_na = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.entry.title}"


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
    url = models.TextField(default="http://localhost:8000", help_text="URL without ending slash")

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
        return f"{self.user} - {self.email}"

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = uuid.uuid4().hex

        super(LoginKey, self).save(*args, **kwargs)

    def send_email(self):
        site_settings = SiteSettings.objects.latest("pk")

        body = render_to_string(
            "mail-login/mail_body.txt",
            {"url": self.get_absolute_url(), "email": site_settings.email},
        )
        send_mail(
            f"{site_settings.name} login information",
            body,
            settings.DEFAULT_FROM_EMAIL,
            [self.email],
        )

    def get_absolute_url(self):
        site_settings = SiteSettings.objects.latest("pk")

        if settings.DEBUG:
            url = "http://localhost:8000"
        else:
            url = site_settings.url

        return url + reverse_lazy("login-key-check", kwargs={"key": self.key})
