from django.contrib import admin
from django.utils.html import format_html
from .models import IncubatorAcceleratorPage, IncubatorApplication


@admin.register(IncubatorAcceleratorPage)
class IncubatorAcceleratorPageAdmin(admin.ModelAdmin):
    list_display = ['title', 'is_accepting_applications', 'application_deadline', 'last_updated']
    list_editable = ['is_accepting_applications']


@admin.register(IncubatorApplication)
class IncubatorApplicationAdmin(admin.ModelAdmin):
    list_display = ['project', 'applicant_name', 'applicant_email', 'stage',
                    'industry', 'status', 'reviewed', 'application_date']
    list_filter = ['status', 'reviewed', 'stage', 'industry', 'application_date']
    list_editable = ['status', 'reviewed']
    search_fields = ['project', 'applicant_name', 'applicant_email', 'applicant_company']
    readonly_fields = ['application_date']
    date_hierarchy = 'application_date'

    fieldsets = (
        ('Applicant Information', {
            'fields': ('applicant_name', 'applicant_email', 'applicant_phone', 'applicant_company')
        }),
        ('Project Details', {
            'fields': ('project', 'website', 'stage', 'industry')
        }),
        ('Application Content', {
            'fields': ('application_text', 'traction', 'team_background', 'goals_for_program')
        }),
        ('Funding', {
            'fields': ('funding_raised', 'funding_needed')
        }),
        ('Attachments', {
            'fields': ('pitch_deck',)
        }),
        ('Admin', {
            'fields': ('status', 'reviewed', 'application_date')
        }),
    )

    actions = ['mark_approved', 'mark_rejected', 'mark_waitlisted']

    def mark_approved(self, request, queryset):
        queryset.update(status='approved', reviewed=True)
        self.message_user(request, f"{queryset.count()} applications marked as approved.")
    mark_approved.short_description = "Mark selected as Approved"

    def mark_rejected(self, request, queryset):
        queryset.update(status='rejected', reviewed=True)
        self.message_user(request, f"{queryset.count()} applications marked as rejected.")
    mark_rejected.short_description = "Mark selected as Rejected"

    def mark_waitlisted(self, request, queryset):
        queryset.update(status='waitlisted', reviewed=True)
        self.message_user(request, f"{queryset.count()} applications marked as waitlisted.")
    mark_waitlisted.short_description = "Mark selected as Waitlisted"
