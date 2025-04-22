from django.contrib import admin
from django.utils.safestring import mark_safe
from django.db import models
from django.urls import reverse
from django.http import HttpResponseRedirect
from django_json_widget.widgets import JSONEditorWidget
from django.contrib.auth.admin import UserAdmin
from .models import (
    CustomUser, Category, Project, FundingType, HeaderLink, FooterSection, FounderProfile, InvestorProfile,
    Reward, Pledge, InvestmentTerm, Investment, SiteSettings, SocialMediaLink, HeroSlider, Testimonial
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
    

@admin.register(HeroSlider)
class HeroSliderAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('title',)

    
class CustomUserAdmin(UserAdmin):
    # Fields to display in the admin list view
    list_display = ('email', 'username', 'user_type', 'phone_number', 'is_staff')
    
    # Fields to filter by
    list_filter = ('user_type', 'is_staff', 'is_superuser')
    
    # Fields to search
    search_fields = ('email', 'username', 'phone_number')
    
    # Fields ordering
    ordering = ('-date_joined',)
    
    # Fields in edit form
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('username', 'first_name', 'last_name', 'phone_number')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('User Type', {'fields': ('user_type',)}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    # Fields in add form
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2', 'user_type', 'phone_number'),
        }),
    )

@admin.register(FounderProfile)
class FounderProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'company_name', 'website')
    search_fields = ('user__email', 'company_name')

@admin.register(InvestorProfile)
class InvestorProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'investment_focus')
    list_filter = ('preferred_industries',)


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ('name', 'position', 'company', 'rating', 'is_active', 'created_at')
    list_filter = ('is_active', 'rating')
    search_fields = ('name', 'position', 'company', 'content')
    list_editable = ('is_active',)

# Register the admin class
admin.site.register(CustomUser, CustomUserAdmin)



admin.site.register(Category)
admin.site.register(FundingType)
admin.site.register(Project)
admin.site.register(Reward)
admin.site.register(Pledge)
admin.site.register(InvestmentTerm)
admin.site.register(Investment)


# Add this to your admin.py f
