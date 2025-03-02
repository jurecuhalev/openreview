from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from web.forms import SiteSettingsForm
from web.models import (
    Category,
    Entry,
    Project,
    Rating,
    RatingAnswer,
    RatingQuestion,
    SiteSettings,
    UserProfile,
)


class UserProfilelInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = "profile"


class UserAdmin(BaseUserAdmin):
    inlines = (UserProfilelInline,)
    list_display = ["username", "first_name", "last_name", "is_staff", "get_projects"]
    list_filter = [
        "is_staff",
        "userprofile__projects",
    ]

    @admin.display(ordering="userprofile__projects", description="Projects")
    def get_projects(self, obj):
        return ", ".join([p.name for p in obj.userprofile.projects.all()])


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_filter = ("is_active", "automatic_import", "assign_reviewers")
    list_display = ("name", "id")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    pass


@admin.register(Entry)
class EntryAdmin(admin.ModelAdmin):
    list_filter = ("project", "is_active")
    list_display = ("title", "project", "is_active")
    readonly_fields = ("extracted_search_text", "search_text")


@admin.register(RatingQuestion)
class RatingQuestionAdmin(admin.ModelAdmin):
    list_display = ["title", "project", "scale", "order"]
    list_filter = ["project"]


@admin.register(RatingAnswer)
class RatingAnswerAdmin(admin.ModelAdmin):
    list_display = ["pk", "user", "project", "question", "entry"]
    list_filter = ["entry__project", "user"]

    def project(self, obj):
        return obj.entry.project


@admin.register(Rating)
class Rating(admin.ModelAdmin):
    list_display = ("pk", "entry", "user")
    raw_id_fields = ("answers",)


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    form = SiteSettingsForm


admin.site.unregister(User)
admin.site.register(User, UserAdmin)
