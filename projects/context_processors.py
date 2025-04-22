from django.utils import timezone
from .models import SiteSettings, ThemeSettings, Announcement

from projects.models import SiteSettings

def site_settings(request):
    """
    Context processor to add site settings to all templates
    """
    try:
        settings = SiteSettings.load()
        return {'site_settings': settings}
    except:
        return {'site_settings': None}


def theme_settings(request):
    return {'theme': ThemeSettings.load()}


def announcements(request):
    now = timezone.now()
    return {
        'active_announcements': Announcement.objects.filter(
            start_date__lte=now,
            end_date__gte=now,
            is_active=True
        )
    }