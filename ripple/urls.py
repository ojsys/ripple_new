
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.projects.urls')),
    path('accounts/', include('apps.accounts.urls')),
    path('cms/', include('apps.cms.urls')),
    path('core/', include('apps.core.urls')),
    path('funding/', include('apps.funding.urls')),
    path('incubator/', include('apps.incubator.urls')),
    path('payments/', include('apps.payments.urls')),
    path('srt/', include('apps.srt.urls')),
    path('ckeditor/', include('ckeditor_uploader.urls')),
]

# Add static and media URL patterns for development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
