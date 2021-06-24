from django.contrib import admin
from django.urls import path

from web.views import EntryListView, EntryDetailView

urlpatterns = [
    path(
        "project/<int:project>/entry/<int:pk>",
        EntryDetailView.as_view(),
        name="entry-detail",
    ),
    path("project/<int:project>/entry/", EntryListView.as_view(), name="entry-list"),
    path("admin/", admin.site.urls),
]
