from django.contrib import admin
from django.utils.html import format_html
from .models import Category, FundingType, Project, Reward, Update, Donation


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


@admin.register(FundingType)
class FundingTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name']


class RewardInline(admin.TabularInline):
    model = Reward
    extra = 1


class UpdateInline(admin.TabularInline):
    model = Update
    extra = 0
    readonly_fields = ['created_at']


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['title', 'creator', 'category', 'funding_type', 'funding_goal',
                    'amount_raised', 'percent_funded_display', 'status', 'deadline', 'created_at']
    list_filter = ['status', 'category', 'funding_type', 'created_at']
    list_editable = ['status']
    search_fields = ['title', 'description', 'creator__email', 'creator__first_name', 'creator__last_name']
    readonly_fields = ['amount_raised', 'total_investment_raised', 'created_at']
    date_hierarchy = 'created_at'
    inlines = [RewardInline, UpdateInline]

    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'short_description', 'description', 'image', 'video_url')
        }),
        ('Project Details', {
            'fields': ('creator', 'category', 'funding_type', 'location')
        }),
        ('Funding', {
            'fields': ('funding_goal', 'amount_raised', 'total_investment_raised', 'deadline')
        }),
        ('Admin', {
            'fields': ('status', 'admin_notes', 'created_at')
        }),
    )

    def percent_funded_display(self, obj):
        percent = obj.get_percent_funded()
        if percent >= 100:
            color = 'green'
        elif percent >= 50:
            color = 'orange'
        else:
            color = 'red'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}%</span>',
            color, f'{percent:.1f}'
        )
    percent_funded_display.short_description = 'Funded'

    actions = ['approve_projects', 'reject_projects']

    def approve_projects(self, request, queryset):
        queryset.update(status='approved')
        self.message_user(request, f"{queryset.count()} projects have been approved.")
    approve_projects.short_description = "Approve selected projects"

    def reject_projects(self, request, queryset):
        queryset.update(status='rejected')
        self.message_user(request, f"{queryset.count()} projects have been rejected.")
    reject_projects.short_description = "Reject selected projects"


@admin.register(Reward)
class RewardAdmin(admin.ModelAdmin):
    list_display = ['title', 'project', 'amount']
    list_filter = ['project']
    search_fields = ['title', 'project__title']


@admin.register(Update)
class UpdateAdmin(admin.ModelAdmin):
    list_display = ['title', 'project', 'created_at']
    list_filter = ['project', 'created_at']
    search_fields = ['title', 'content', 'project__title']
    readonly_fields = ['created_at']


@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = ['donor_display', 'project', 'amount', 'amount_ngn', 'status', 'is_anonymous', 'created_at']
    list_filter = ['status', 'is_anonymous', 'created_at']
    search_fields = ['donor__email', 'donor_name', 'donor_email', 'project__title']
    readonly_fields = ['paystack_reference', 'created_at']
    date_hierarchy = 'created_at'

    def donor_display(self, obj):
        if obj.is_anonymous:
            return "Anonymous"
        if obj.donor:
            return obj.donor.get_full_name() or obj.donor.email
        return obj.donor_name or obj.donor_email or "Unknown"
    donor_display.short_description = 'Donor'

    actions = ['mark_completed', 'mark_refunded']

    def mark_completed(self, request, queryset):
        queryset.update(status='completed')
        self.message_user(request, f"{queryset.count()} donations marked as completed.")
    mark_completed.short_description = "Mark selected as Completed"

    def mark_refunded(self, request, queryset):
        queryset.update(status='refunded')
        self.message_user(request, f"{queryset.count()} donations marked as refunded.")
    mark_refunded.short_description = "Mark selected as Refunded"
