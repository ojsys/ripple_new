from django.contrib import admin
from django.utils.safestring import mark_safe
from django.db import models
from django.urls import reverse
from django.http import HttpResponseRedirect
from django_json_widget.widgets import JSONEditorWidget
from .models import (
    Category, Project, FundingType, HeaderLink, FooterSection,
    Reward, Pledge, InvestmentTerm, Investment, SiteSettings, SocialMediaLink
)

class HeaderLinkInline(admin.TabularInline):
    model = HeaderLink
    extra = 1

class FooterSectionInline(admin.StackedInline):
    model = FooterSection
    extra = 1
    formfield_overrides = {
        models.TextField: {'widget': JSONEditorWidget}
    }

class SocialMediaInline(admin.TabularInline):
    model = SocialMediaLink
    extra = 1

@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False  # Disable adding new instances

    def has_delete_permission(self, request, obj=None):
        return False  # Disable deletion

    def change_view(self, request, object_id, form_url='', extra_context=None):
        # Always redirect to the singleton instance
        if object_id != '1':
            return HttpResponseRedirect(reverse('admin:core_sitesettings_change', args=[1]))
        return super().change_view(request, object_id, form_url, extra_context)

    def add_view(self, request, form_url='', extra_context=None):
        # Redirect to change view if instance exists
        if SiteSettings.objects.exists():
            return HttpResponseRedirect(reverse('admin:core_sitesettings_change', args=[1]))
        return super().add_view(request, form_url, extra_context)
    





admin.site.register(Category)
admin.site.register(FundingType)
admin.site.register(Project)
admin.site.register(Reward)
admin.site.register(Pledge)
admin.site.register(InvestmentTerm)
admin.site.register(Investment)