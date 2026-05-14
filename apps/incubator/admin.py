from django.contrib import admin
from django.utils.html import format_html
from .models import (
    IncubatorAcceleratorPage,
    IncubatorApplication,
    ProgramPillar,
    ApplicationStep,
    WhatWeLookForItem,
)


class ProgramPillarInline(admin.TabularInline):
    model = ProgramPillar
    extra = 0
    fields = ['order', 'title', 'description', 'icon_class', 'icon_color', 'bg_color', 'cta_text', 'cta_url', 'is_active']
    ordering = ['order']


class ApplicationStepInline(admin.TabularInline):
    model = ApplicationStep
    extra = 0
    fields = ['order', 'step_number', 'title', 'description']
    ordering = ['order']


class WhatWeLookForInline(admin.TabularInline):
    model = WhatWeLookForItem
    extra = 0
    fields = ['order', 'title', 'description', 'icon_class', 'icon_color', 'bg_color']
    ordering = ['order']


@admin.register(IncubatorAcceleratorPage)
class IncubatorAcceleratorPageAdmin(admin.ModelAdmin):
    inlines = [ProgramPillarInline, WhatWeLookForInline, ApplicationStepInline]

    fieldsets = (
        ('Hero Section', {
            'fields': ('hero_title', 'hero_subtitle'),
        }),
        ('Hero Stats Bar', {
            'fields': (('stat_weeks', 'stat_lessons', 'stat_mentorship', 'stat_event', 'stat_cost'),),
            'classes': ('collapse',),
        }),
        ('Program Pillars Section', {
            'fields': ('pillars_section_title', 'pillars_section_subtitle'),
            'description': 'Edit the section title and subtitle. Add/edit the individual pillar cards in the "Program Pillars" inline below.',
        }),
        ('Curriculum Section', {
            'fields': ('curriculum_section_title', 'curriculum_section_subtitle'),
        }),
        ('Who Should Apply Section', {
            'fields': (
                'who_section_title', 'who_section_intro',
                'good_fit_items',
                'not_good_fit_label', 'not_good_fit_items',
                'look_for_section_title',
            ),
            'description': 'Edit the "What We Look For" criteria cards in the inline table below.',
        }),
        ('Application Process Section', {
            'fields': ('process_section_subtitle',),
            'description': 'Edit the individual steps in the "Application Steps" inline below.',
        }),
        ('Program Description (Body)', {
            'fields': ('title', 'program_description', 'image'),
        }),
        ('Application Sidebar & Status', {
            'fields': ('is_accepting_applications', 'application_deadline', 'application_info'),
        }),
        ('Bottom CTA', {
            'fields': (
                ('cta_title_open', 'cta_body_open'),
                ('cta_title_closed', 'cta_body_closed'),
            ),
        }),
    )

    def has_add_permission(self, request):
        return not IncubatorAcceleratorPage.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        obj = IncubatorAcceleratorPage.load()
        from django.shortcuts import redirect
        from django.urls import reverse
        return redirect(reverse('admin:incubator_incubatoracceleratorpage_change', args=[obj.pk]))


@admin.register(IncubatorApplication)
class IncubatorApplicationAdmin(admin.ModelAdmin):
    list_display = ['project', 'applicant_name', 'applicant_email', 'stage',
                    'industry', 'status_badge', 'lms_status', 'reviewed', 'application_date']
    list_filter = ['status', 'lms_provisioned', 'reviewed', 'stage', 'industry', 'application_date']
    list_editable = ['reviewed']
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
            'fields': ('status', 'reviewed', 'lms_provisioned', 'application_date')
        }),
    )
    readonly_fields = ['application_date', 'lms_provisioned']

    actions = ['mark_approved', 'mark_rejected', 'mark_waitlisted']

    def lms_status(self, obj):
        if obj.lms_provisioned:
            return format_html(
                '<span style="padding:3px 10px;border-radius:100px;font-size:0.75rem;font-weight:700;color:#15803d;background:#f0fdf4;">✓ LMS Active</span>'
            )
        if obj.status == 'approved':
            return format_html(
                '<span style="padding:3px 10px;border-radius:100px;font-size:0.75rem;font-weight:700;color:#d97706;background:#fffbeb;">Pending</span>'
            )
        return '—'
    lms_status.short_description = "LMS"

    def status_badge(self, obj):
        colors = {
            'pending': ('#d97706', '#fffbeb'),
            'approved': ('#16a34a', '#f0fdf4'),
            'rejected': ('#dc2626', '#fef2f2'),
            'waitlisted': ('#7c3aed', '#f5f3ff'),
        }
        color, bg = colors.get(obj.status, ('#6b7280', '#f9fafb'))
        return format_html(
            '<span style="padding:3px 10px;border-radius:100px;font-size:0.75rem;font-weight:700;color:{};background:{};">{}</span>',
            color, bg, obj.get_status_display()
        )
    status_badge.short_description = "Status"

    def mark_approved(self, request, queryset):
        queryset.update(status='approved', reviewed=True)
        self.message_user(request, f"{queryset.count()} applications marked as Approved.")
    mark_approved.short_description = "Mark selected as Approved"

    def mark_rejected(self, request, queryset):
        queryset.update(status='rejected', reviewed=True)
        self.message_user(request, f"{queryset.count()} applications marked as Rejected.")
    mark_rejected.short_description = "Mark selected as Rejected"

    def mark_waitlisted(self, request, queryset):
        queryset.update(status='waitlisted', reviewed=True)
        self.message_user(request, f"{queryset.count()} applications marked as Waitlisted.")
    mark_waitlisted.short_description = "Mark selected as Waitlisted"
