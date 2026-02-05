from django.contrib import admin
from django.utils.html import format_html
from .models import Category, FundingType, Project, Reward, Update, Donation, PaymentAttempt


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

    actions = ['approve_projects', 'reject_projects', 'recalculate_funding']

    def approve_projects(self, request, queryset):
        queryset.update(status='approved')
        self.message_user(request, f"{queryset.count()} projects have been approved.")
    approve_projects.short_description = "Approve selected projects"

    def reject_projects(self, request, queryset):
        queryset.update(status='rejected')
        self.message_user(request, f"{queryset.count()} projects have been rejected.")
    reject_projects.short_description = "Reject selected projects"

    def recalculate_funding(self, request, queryset):
        for project in queryset:
            project.recalculate_funding()
        self.message_user(request, f"Recalculated funding for {queryset.count()} projects.")
    recalculate_funding.short_description = "Recalculate funding from completed donations"


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
        # Recalculate funding for affected projects
        project_ids = queryset.values_list('project_id', flat=True).distinct()
        for project in Project.objects.filter(id__in=project_ids):
            project.recalculate_funding()
        self.message_user(request, f"{queryset.count()} donations marked as completed. Project funding recalculated.")
    mark_completed.short_description = "Mark selected as Completed"

    def mark_refunded(self, request, queryset):
        queryset.update(status='refunded')
        # Recalculate funding for affected projects
        project_ids = queryset.values_list('project_id', flat=True).distinct()
        for project in Project.objects.filter(id__in=project_ids):
            project.recalculate_funding()
        self.message_user(request, f"{queryset.count()} donations marked as refunded. Project funding recalculated.")
    mark_refunded.short_description = "Mark selected as Refunded"


@admin.register(PaymentAttempt)
class PaymentAttemptAdmin(admin.ModelAdmin):
    list_display = ['user_display', 'project', 'amount', 'status', 'paystack_reference', 'has_donation', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'paystack_reference', 'project__title']
    readonly_fields = ['paystack_reference', 'donation', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'

    def user_display(self, obj):
        if obj.user:
            return obj.user.get_full_name() or obj.user.email
        return "Unknown"
    user_display.short_description = 'User'

    def has_donation(self, obj):
        if obj.donation:
            return format_html('<span style="color: green; font-weight: bold;">Yes</span>')
        return format_html('<span style="color: gray;">No</span>')
    has_donation.short_description = 'Donation Created'

    actions = ['verify_and_resolve_pending']

    def verify_and_resolve_pending(self, request, queryset):
        """Re-verify pending payment attempts with Paystack and resolve them."""
        import requests as req
        from django.conf import settings as conf_settings

        paystack_secret = getattr(conf_settings, 'PAYSTACK_SECRET_KEY', '')
        if not paystack_secret:
            self.message_user(request, "Paystack secret key is not configured.", level='error')
            return

        headers = {'Authorization': f'Bearer {paystack_secret}'}
        resolved = 0
        failed = 0

        for attempt in queryset.filter(status='pending'):
            try:
                response = req.get(
                    f'https://api.paystack.co/transaction/verify/{attempt.paystack_reference}',
                    headers=headers,
                    timeout=30
                )
                if response.status_code == 200:
                    result = response.json()
                    if result.get('status') and result['data']['status'] == 'success':
                        # Payment was actually successful - create donation
                        donation = Donation.objects.create(
                            project=attempt.project,
                            donor=attempt.user,
                            amount=attempt.amount,
                            amount_ngn=attempt.amount_ngn,
                            reward=attempt.reward,
                            message=attempt.message,
                            is_anonymous=attempt.is_anonymous,
                            paystack_reference=attempt.paystack_reference,
                            status='completed'
                        )
                        attempt.status = 'success'
                        attempt.donation = donation
                        attempt.save()
                        attempt.project.recalculate_funding()
                        resolved += 1
                    else:
                        attempt.status = 'failed'
                        attempt.error_message = result['data'].get('gateway_response', 'Not successful')
                        attempt.save()
                        failed += 1
            except req.exceptions.RequestException:
                continue

        self.message_user(
            request,
            f"Resolved: {resolved} successful, {failed} failed. "
            f"(Remaining pending may need retry if Paystack was unreachable.)"
        )
    verify_and_resolve_pending.short_description = "Re-verify pending payments with Paystack"
