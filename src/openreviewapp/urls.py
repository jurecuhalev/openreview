from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from web.views import EntryListView, EntryDetailView

urlpatterns = [
    path(
        "project/<int:project>/entry/<int:pk>",
        EntryDetailView.as_view(),
        name="entry-detail",
    ),
    path("project/<int:project>/entry/", EntryListView.as_view(), name="entry-list"),
    path("admin/", admin.site.urls),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
