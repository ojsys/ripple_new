from .models import SocialMediaLink

def social_links(request):
    return {
        'social_links': SocialMediaLink.objects.all().order_by('order')
    }