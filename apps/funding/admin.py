from django.contrib import admin
from django.utils.html import format_html
from .models import Investment, InvestmentTerm, Pledge


@admin.register(InvestmentTerm)
class InvestmentTermAdmin(admin.ModelAdmin):
    list_display = ['project', 'equity_offered', 'minimum_investment', 'maximum_investment', 'valuation', 'deadline']
    list_filter = ['deadline']
    search_fields = ['project__title']
    raw_id_fields = ['project']


@admin.register(Investment)
class InvestmentAdmin(admin.ModelAdmin):
    list_display = ['investor', 'project', 'amount', 'equity_percentage', 'status', 'status_badge', 'created_at']
    list_filter = ['status', 'created_at']
    list_editable = ['status']
    search_fields = ['investor__email', 'investor__first_name', 'investor__last_name', 'project__title']
    readonly_fields = ['created_at', 'is_counted']
    raw_id_fields = ['investor', 'project', 'terms']
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Investment Details', {
            'fields': ('investor', 'project', 'amount', 'equity_percentage')
        }),
        ('Terms & Status', {
            'fields': ('terms', 'status', 'actual_return')
        }),
        ('System', {
            'fields': ('is_counted', 'created_at'),
            'classes': ('collapse',)
        }),
    )

    def status_badge(self, obj):
        colors = {
            'pending': '#f59e0b',
            'active': '#10b981',
            'completed': '#3b82f6',
            'failed': '#ef4444',
        }
        color = colors.get(obj.status, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 12px; font-size: 11px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    actions = ['mark_active', 'mark_completed', 'mark_failed']

    def mark_active(self, request, queryset):
        queryset.update(status='active')
        self.message_user(request, f"{queryset.count()} investments marked as active.")
    mark_active.short_description = "Mark selected as Active"

    def mark_completed(self, request, queryset):
        queryset.update(status='completed')
        self.message_user(request, f"{queryset.count()} investments marked as completed.")
    mark_completed.short_description = "Mark selected as Completed"

    def mark_failed(self, request, queryset):
        queryset.update(status='failed')
        self.message_user(request, f"{queryset.count()} investments marked as failed.")
    mark_failed.short_description = "Mark selected as Failed"


@admin.register(Pledge)
class PledgeAdmin(admin.ModelAdmin):
    list_display = ['backer', 'project', 'amount', 'reward', 'pledged_at']
    list_filter = ['pledged_at']
    search_fields = ['backer__email', 'backer__first_name', 'backer__last_name', 'project__title']
    readonly_fields = ['pledged_at']
    raw_id_fields = ['backer', 'project', 'reward']
    date_hierarchy = 'pledged_at'
