from web.models import SiteSettings


def logo_url(request):
    try:
        site_settings = SiteSettings.objects.latest("pk")
    except SiteSettings.DoesNotExist:
        return {}

    if site_settings.logo:
        return {"logo_url": site_settings.logo.url}

    return {}
