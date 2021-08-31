from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from web.views import (
    EntryListView,
    EntryDetailView,
    IndexView,
    LoginKeyCheckView,
    ReviewerListView,
    EntryAssignReviewer,
)

urlpatterns = [
    path(
        "project/<int:project>/entry/<int:pk>",
        EntryDetailView.as_view(),
        name="entry-detail",
    ),
    path(
        "project/<int:project>/entry/<int:pk>/assign/<int:user>",
        EntryAssignReviewer.as_view(),
        name="entry-assign-reviewer",
    ),
    path("project/<int:project>/entry/", EntryListView.as_view(), name="entry-list"),
    path(
        "project/<int:project>/reviewer/",
        ReviewerListView.as_view(),
        name="reviewer-list",
    ),
    path("accounts/", include("django.contrib.auth.urls")),
    path("login/<str:key>/", LoginKeyCheckView.as_view(), name="login-key-check"),
    path("login/", LoginKeyCheckView.as_view(), name="login-key-check"),
    path("admin/", admin.site.urls),
    path("su/", include("django_su.urls")),
    path("", IndexView.as_view(), name="index"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
