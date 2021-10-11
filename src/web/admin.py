from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from web.models import (
    UserProfile,
    Project,
    Category,
    Entry,
    RatingQuestion,
    RatingAnswer,
    SiteSettings,
    Rating,
)

from web.forms import SiteSettingsForm


class UserProfilelInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = "profile"


class UserAdmin(BaseUserAdmin):
    inlines = (UserProfilelInline,)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    pass


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    pass


@admin.register(Entry)
class EntryAdmin(admin.ModelAdmin):
    list_filter = ("is_active",)
    pass


@admin.register(RatingQuestion)
class RatingQuestionAdmin(admin.ModelAdmin):
    list_display = ["title", "project", "scale", "order"]


@admin.register(RatingAnswer)
class RatingAnswerAdmin(admin.ModelAdmin):
    list_display = ["pk", "user", "question", "entry"]
    list_filter = ["user"]


@admin.register(Rating)
class Rating(admin.ModelAdmin):
    list_display = ("pk", "entry", "user")


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    form = SiteSettingsForm


admin.site.unregister(User)
admin.site.register(User, UserAdmin)
