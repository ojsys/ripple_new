from .models import SiteSettings


def site_settings(request):
    """
    Context processor to make site settings available in all templates.
    """
    try:
        settings = SiteSettings.load()
        return {'site_settings': settings}
    except Exception:
        return {'site_settings': None}
