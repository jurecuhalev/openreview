from django.urls import resolve

from web.models import Project, SiteSettings


def logo_url(request):
    try:
        site_settings = SiteSettings.objects.latest("pk")
    except SiteSettings.DoesNotExist:
        return {}

    if site_settings.logo:
        return {"logo_url": site_settings.logo.url}

    return {}


def current_project(request):
    kwargs = resolve(request.path_info).kwargs
    if kwargs.get("project"):
        return {"current_project": Project.objects.get(pk=kwargs.get("project"))}

    return {}


def current_tab(request):
    url_name = resolve(request.path_info).url_name

    if url_name.split("-"):
        if "list" in url_name:
            return {"current_tab": "list"}

        return {"current_tab": url_name.split("-")[0]}

    return {}
