from .models import SocialMediaLink, SiteSettings

def social_links(request):
    return {
        'social_links': SocialMediaLink.objects.all().order_by('order')
    }

def site_settings(request):
    try:
        settings = SiteSettings.load()
    except Exception:
        settings = None
    return {
        'site_settings': settings
    }