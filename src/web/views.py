from braces.views import StaffuserRequiredMixin
from django.db.models import Count
from django.shortcuts import render
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.shortcuts import redirect
import datetime

from django.views import View
from icecream import ic

from django.views.generic import ListView, DetailView, TemplateView
from django.contrib import messages
from django.views.generic.edit import FormMixin, FormView

from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.html import format_html

from web.forms import RatingForm, LoginForm
from web.models import Entry, RatingQuestion, RatingAnswer, LoginKey, Project
from web.submissions_processing import merge_fields_with_submission_data


class IndexView(LoginRequiredMixin, ListView):
    template_name = "web/project_list.html"
    context_object_name = "project_list"

    def get_queryset(self):
        return Project.objects.filter(is_active=True)


class EntryListView(LoginRequiredMixin, ListView):
    model = Entry
    context_object_name = "entry_list"

    def get_queryset(self):
        return Entry.active.filter(project__pk=self.kwargs["project"]).order_by("title")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if not self.request.user.is_staff:
            rating_status = {
                "Waiting for review": self.get_queryset()
                .exclude(ratinganswer__user=self.request.user)
                .distinct()
                .order_by("title"),
                "Completed reviews": self.get_queryset()
                .filter(ratinganswer__user=self.request.user)
                .distinct()
                .order_by("title"),
            }

            context["ratings_by_status"] = rating_status

        return context


class EntryDetailView(LoginRequiredMixin, DetailView, FormMixin):
    model = Entry
    template_name = "web/entry_detail.html"
    context_object_name = "entry"
    questions = None
    answers = None
    object = None

    def get_form(self, form_class=None):
        entry = self.get_object()
        self.questions = RatingQuestion.objects.filter(project=entry.project).order_by(
            "order"
        )
        self.answers = RatingAnswer.objects.filter(user=self.request.user, entry=entry)

        if self.request.POST:
            form = RatingForm(
                data=self.request.POST, questions=self.questions, answers=self.answers
            )

        else:
            form = RatingForm(questions=self.questions, answers=self.answers)

        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        entry = self.get_object()
        context["submission_data"] = merge_fields_with_submission_data(
            fields=entry.project.fields, data=entry.data
        )

        if self.request.user.is_staff:
            entry = self.get_object()
            questions = RatingQuestion.objects.filter(project=entry.project).order_by(
                "order"
            )
            answers = (
                RatingAnswer.objects.filter(entry=entry)
                .values(
                    "user",
                    "user__username",
                    "question__title",
                    "value",
                    "is_na",
                    "question__order",
                )
                .annotate(Count("user"))
                .order_by("user", "question__order")
            )
            context["ratings"] = {"questions": questions, "answers": answers}

        return context

    def post(self, request, *args, **kwargs):
        """
        Handle POST requests: instantiate a form instance with the passed
        POST variables and then check if it's valid.
        """
        self.object = self.get_object()
        form = self.get_form()

        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        form.save(user=self.request.user, entry=self.get_object())

        return super().form_valid(form)

    def get_success_url(self):
        entries_url = reverse_lazy(
            "entry-list",
            kwargs={
                "project": self.get_object().project.pk,
            },
        )
        message = format_html(
            'Your review has been saved. <a class="underline" href="{}">Review another</a>.',
            entries_url,
        )
        messages.add_message(
            self.request,
            messages.INFO,
            message,
        )
        return reverse_lazy(
            "entry-detail",
            kwargs={
                "project": self.get_object().project.pk,
                "pk": self.get_object().pk,
            },
        )


class LoginKeyCheckView(FormView):
    template_name = "registration/login.html"
    form_class = LoginForm

    def form_valid(self, form):
        email = form.cleaned_data.get("email")
        user = User.objects.get(email__iexact=email)
        ctx = {"email": email}

        key = LoginKey(user=user, email=email)
        key.save()
        key.send_email()

        return render(self.request, "mail-login/mail_sent.html", ctx)

    def get(self, request, *args, **kwargs):
        try:
            key = kwargs.pop("key")
        except KeyError:
            return redirect(reverse_lazy("index"))

        today = datetime.datetime.today()
        if LoginKey.objects.filter(
            key=key, pub_date__gte=(today - datetime.timedelta(days=7))
        ).exists():
            login_key = LoginKey.objects.get(
                key=key, pub_date__gte=(today - datetime.timedelta(days=7))
            )

            login_key.user.backend = "django.contrib.auth.backends.ModelBackend"
            login(self.request, login_key.user)

            return redirect(request.GET.get("next", reverse_lazy("index")))

        return redirect(reverse_lazy("index"))


class ReviewerListView(StaffuserRequiredMixin, TemplateView):
    template_name = "web/reviewer_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = Project.objects.get(pk=self.kwargs.get("project"))

        user_profiles = project.userprofile_set.all()
        reviewer_list = []

        for user_profile in user_profiles:
            count = (
                user_profile.user.ratinganswer_set.values("entry").distinct().count()
            )
            reviewer_list.append({"user": user_profile.user, "count": count})

        context["reviewer_list"] = reviewer_list

        return context
