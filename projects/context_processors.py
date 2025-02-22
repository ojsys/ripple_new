from django.utils import timezone
from .models import SiteSettings, ThemeSettings, Announcement

def site_settings(request):
    return {
        'site_settings': SiteSettings.load()
    }


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