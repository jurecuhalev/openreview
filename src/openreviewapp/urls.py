from django.contrib import admin
from django.urls import path

from web.views import EntryListView

urlpatterns = [
    path("project/<project>/entry/", EntryListView.as_view()),
    path("admin/", admin.site.urls),
]
