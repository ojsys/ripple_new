from django.contrib import admin
from django.utils.html import format_html
from .models import SponsorshipTier, SponsorshipInquiry, SponsorshipPage


@admin.register(SponsorshipTier)
class SponsorshipTierAdmin(admin.ModelAdmin):
    list_display = ['name', 'price_display_col', 'cohort_slots', 'color_class', 'is_featured', 'is_active', 'order']
    list_editable = ['is_featured', 'is_active', 'order']
    list_filter = ['is_active', 'color_class']
    prepopulated_fields = {'slug': ('name',)}
    fieldsets = (
        ('Tier Info', {
            'fields': ('name', 'slug', 'price_usd', 'tagline', 'color_class', 'icon_class', 'cohort_slots'),
        }),
        ('Content', {
            'fields': ('description', 'benefits'),
        }),
        ('Display', {
            'fields': ('is_featured', 'is_active', 'order'),
        }),
    )

    def price_display_col(self, obj):
        return obj.price_display()
    price_display_col.short_description = 'Price'


@admin.register(SponsorshipInquiry)
class SponsorshipInquiryAdmin(admin.ModelAdmin):
    list_display = ['company_name', 'contact_name', 'contact_email', 'tier', 'organization_type', 'budget_range', 'status_badge', 'submitted_at']
    list_filter = ['status', 'organization_type', 'tier', 'budget_range']
    list_editable = []
    search_fields = ['company_name', 'contact_name', 'contact_email']
    readonly_fields = ['submitted_at']
    date_hierarchy = 'submitted_at'
    actions = ['mark_contacted', 'mark_in_discussion', 'mark_closed_won']

    fieldsets = (
        ('Contact', {
            'fields': ('company_name', 'contact_name', 'contact_email', 'contact_phone', 'organization_type'),
        }),
        ('Inquiry Details', {
            'fields': ('tier', 'program_interest', 'budget_range', 'message'),
        }),
        ('Status & Notes', {
            'fields': ('status', 'internal_notes', 'submitted_at'),
        }),
    )

    def status_badge(self, obj):
        colors = {
            'new': '#2563eb',
            'contacted': '#d97706',
            'in_discussion': '#7c3aed',
            'closed_won': '#16a34a',
            'closed_lost': '#dc2626',
        }
        color = colors.get(obj.status, '#6b7280')
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 10px;border-radius:12px;font-size:0.75rem;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    @admin.action(description='Mark selected as Contacted')
    def mark_contacted(self, request, queryset):
        queryset.update(status='contacted')

    @admin.action(description='Mark selected as In Discussion')
    def mark_in_discussion(self, request, queryset):
        queryset.update(status='in_discussion')

    @admin.action(description='Mark selected as Closed — Won')
    def mark_closed_won(self, request, queryset):
        queryset.update(status='closed_won')


@admin.register(SponsorshipPage)
class SponsorshipPageAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Hero', {
            'fields': ('hero_title', 'hero_subtitle'),
        }),
        ('Body Content', {
            'fields': ('intro_text', 'why_sponsor_text'),
        }),
        ('Settings', {
            'fields': ('show_tiers', 'cta_text'),
        }),
    )

    def has_add_permission(self, request):
        return not SponsorshipPage.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
