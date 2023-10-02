import json
from styleframe import StyleFrame, Styler
import datetime
from io import BytesIO
from django.db.models import Case, When

from braces.views import StaffuserRequiredMixin
from django.db.models import Count
from django.shortcuts import render
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.shortcuts import redirect

from django.utils import timezone
from django.views import View
from django.http import HttpResponse

from django.views.generic import ListView, DetailView, TemplateView
from django.contrib import messages
from django.views.generic.edit import FormMixin, FormView

from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.html import format_html

from web.export import (
    get_df_reviewers,
    get_df_entries,
    get_df_ratings,
    get_df_ratings_avg,
    get_df_full_entries,
)
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
        return (
            Entry.active.filter(project__pk=self.kwargs["project"])
            .order_by("title")
            .prefetch_related("project")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        if not self.request.user.is_staff:
            reviewer_on = (
                self.get_queryset()
                .filter(reviewers=user)
                .exclude(ratinganswer__user=user)
            )

            rating_status = {
                "Assigned to you for review": reviewer_on,
                "Optional entries for review": self.get_queryset()
                .distinct()
                .exclude(pk__in=reviewer_on)
                .exclude(ratinganswer__user=user),
                "Completed reviews": self.get_queryset()
                .filter(ratinganswer__user=user)
                .distinct(),
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
            users_that_reviewed = entry.rating_set.all().values_list("user", flat=True)

            users_not_reviewed_yet = entry.reviewers.exclude(pk__in=users_that_reviewed)

            context["ratings"] = {
                "questions": questions,
                "answers": answers,
            }
            context["waiting_for_users"] = users_not_reviewed_yet

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

        today = timezone.now()
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


class ReviewerDetailView(StaffuserRequiredMixin, DetailView):
    template_name = "web/reviewer_detail.html"
    model = User

    def get_queryset(self, *args, **kwargs):
        project = Project.objects.get(pk=self.kwargs.get("project"))
        return project.userprofile_set.all()

    def get_object(self, queryset=None):
        return self.get_queryset().get(user__pk=self.kwargs.get("pk"))

    def get_context_object_name(self, obj):
        return "reviewer"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        entries = Entry.active.filter(project__pk=self.kwargs["project"]).order_by(
            "title"
        )
        user = self.get_object().user

        waiting_reviews = entries.filter(reviewers=user).exclude(rating__user=user)
        completed_reviews = entries.filter(reviewers=user).filter(rating__user=user)

        rating_status = {
            "Waiting for review": waiting_reviews,
            "Completed reviews": completed_reviews,
        }

        context["ratings_by_status"] = rating_status

        return context


class ReviewerListView(StaffuserRequiredMixin, TemplateView):
    template_name = "web/reviewer_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = Project.objects.get(pk=self.kwargs.get("project"))

        user_profiles = project.userprofile_set.all().order_by("user__first_name")
        reviewer_list = []

        for user_profile in user_profiles:
            count_done = (
                user_profile.user.ratinganswer_set.filter(entry__project=project)
                .values("entry")
                .distinct()
                .count()
            )
            count_total = user_profile.user.entry_set.filter(project=project).count()

            reviewer_list.append(
                {
                    "user": user_profile.user,
                    "count_total": count_total,
                    "count_done": count_done,
                }
            )

        context["reviewer_list"] = reviewer_list

        return context


class EntryAssignReviewer(StaffuserRequiredMixin, View):
    def post(self, request, pk, user, *args, **kwargs):
        user = User.objects.get(pk=user)
        entry = Entry.objects.get(pk=pk)

        if entry.reviewers.filter(pk=user.pk).exists():
            entry.reviewers.remove(user)
            resp = {"isAssigned": False}
        else:
            entry.reviewers.add(user)
            resp = {"isAssigned": True}

        return HttpResponse(json.dumps(resp))


class ProjectExportView(StaffuserRequiredMixin, View):
    def get(self, request, pk, *args, **kwargs):
        df_reviewers = get_df_reviewers(project_pk=pk)
        df_entries = get_df_entries(project_pk=pk)
        df_ratings = get_df_ratings(project_pk=pk)
        df_ratings_avg = get_df_ratings_avg(project_pk=pk)
        df_full_entries, limit_width_cols = get_df_full_entries(project_pk=pk)

        styler = Styler(horizontal_alignment="general")
        styler_ratings = Styler(horizontal_alignment="general", wrap_text=True)

        # Workaround for Excel interpreting some strings as formulas
        # https://stackoverflow.com/a/54095887/141200
        options = {"strings_to_formulas": False, "strings_to_urls": False}

        with BytesIO() as b:
            writer = StyleFrame.ExcelWriter(b, options=options)
            sf = StyleFrame(df_reviewers, styler_obj=styler)
            sf.to_excel(
                excel_writer=writer,
                sheet_name="Reviewers",
                best_fit=df_reviewers.columns.to_list(),
                index=False,
            )

            sf = StyleFrame(df_entries, styler_obj=styler)
            sf.to_excel(
                excel_writer=writer,
                sheet_name="Entries",
                best_fit=df_entries.columns.to_list(),
                index=False,
            )

            # FIXME: This should be a lookup into database for 'textarea' type of question
            sf = StyleFrame(df_ratings, styler_obj=styler_ratings)
            sf.apply_column_style(
                cols_to_style=df_ratings.columns[
                    df_ratings.columns.str.endswith("remarks")
                ].to_list(),
                width=100,
                styler_obj=styler_ratings,
            )
            sf.to_excel(
                excel_writer=writer,
                sheet_name="Reviews",
                best_fit=df_ratings.columns[
                    ~df_ratings.columns.str.endswith("remarks")
                ].to_list(),
                index=False,
            )

            sf = StyleFrame(df_ratings_avg, styler_obj=styler)
            sf.to_excel(
                excel_writer=writer,
                sheet_name="Reviews Avg Ratings",
                best_fit=df_ratings_avg.columns.to_list(),
                index=False,
            )

            sf = StyleFrame(df_full_entries, styler_obj=styler_ratings)
            best_fit_cols = set(df_full_entries.columns.to_list()) - limit_width_cols
            sf.apply_column_style(
                cols_to_style=limit_width_cols, width=200, styler_obj=styler_ratings
            )
            sf.to_excel(
                excel_writer=writer,
                sheet_name="Entries (detailed)",
                best_fit=best_fit_cols,
                index=False,
            )

            writer.close()

            filename = "export.xlsx"
            response = HttpResponse(
                b.getvalue(),
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
            response["Content-Disposition"] = "attachment; filename=%s" % filename
            return response


class RankingView(LoginRequiredMixin, TemplateView):
    template_name = "web/rankings.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = Project.objects.get(pk=self.kwargs.get("project"))

        numeric_questions = project.ratingquestion_set.filter(scale__in=["1-10", "1-N"])
        order_by = self.request.GET.get("order_by", 0)

        context["numeric_questions"] = numeric_questions
        context["order_by"] = int(order_by)

        if order_by:
            order_title = numeric_questions.get(pk=order_by).title
        else:
            order_title = "Total Avg"

        ratings = get_df_ratings_avg(project_pk=project.pk, sort_column=order_title)
        entry_ids = ratings["Entry ID"].array

        preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(entry_ids)])
        entry_list = Entry.objects.filter(pk__in=entry_ids).order_by(preserved)
        context["entry_list"] = entry_list

        return context
