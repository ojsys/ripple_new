from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Investment, InvestmentTerm, Pledge, FounderWithdrawalRequest


@admin.register(InvestmentTerm)
class InvestmentTermAdmin(admin.ModelAdmin):
    list_display = ['project', 'equity_offered', 'minimum_investment', 'maximum_investment', 'valuation', 'deadline']
    list_filter = ['deadline']
    search_fields = ['project__title']
    raw_id_fields = ['project']


@admin.register(Investment)
class InvestmentAdmin(admin.ModelAdmin):
    list_display = ['investor', 'project', 'amount', 'equity_percentage', 'status', 'payment_status', 'status_badge', 'created_at']
    list_filter = ['status', 'payment_status', 'created_at']
    list_editable = ['status']
    search_fields = ['investor__email', 'investor__first_name', 'investor__last_name', 'project__title']
    readonly_fields = ['created_at', 'is_counted']
    raw_id_fields = ['investor', 'project', 'terms']
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Investment Details', {
            'fields': ('investor', 'project', 'amount', 'amount_ngn', 'equity_percentage')
        }),
        ('Terms & Status', {
            'fields': ('terms', 'status', 'payment_status', 'paystack_reference', 'actual_return')
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

    actions = ['mark_approved', 'mark_active', 'mark_completed', 'mark_failed']

    def mark_approved(self, request, queryset):
        count = 0
        for investment in queryset.filter(payment_status='paid'):
            investment.status = 'approved'
            investment.is_counted = True
            investment.save()
            count += 1
        self.message_user(request, f"{count} paid investments marked as approved (project totals updated).")
    mark_approved.short_description = "Approve selected (paid) investments — updates venture progress"

    def mark_active(self, request, queryset):
        count = 0
        for investment in queryset:
            investment.status = 'active'
            investment.save()
            count += 1
        self.message_user(request, f"{count} investments marked as active.")
    mark_active.short_description = "Mark selected as Active"

    def mark_completed(self, request, queryset):
        count = 0
        for investment in queryset:
            investment.status = 'completed'
            investment.save()
            count += 1
        self.message_user(request, f"{count} investments marked as completed.")
    mark_completed.short_description = "Mark selected as Completed"

    def mark_failed(self, request, queryset):
        count = 0
        for investment in queryset:
            investment.status = 'failed'
            investment.save()
            count += 1
        self.message_user(request, f"{count} investments marked as failed.")
    mark_failed.short_description = "Mark selected as Failed"


@admin.register(Pledge)
class PledgeAdmin(admin.ModelAdmin):
    list_display = ['backer', 'project', 'amount', 'reward', 'pledged_at']
    list_filter = ['pledged_at']
    search_fields = ['backer__email', 'backer__first_name', 'backer__last_name', 'project__title']
    readonly_fields = ['pledged_at']
    raw_id_fields = ['backer', 'project', 'reward']
    date_hierarchy = 'pledged_at'


@admin.register(FounderWithdrawalRequest)
class FounderWithdrawalRequestAdmin(admin.ModelAdmin):
    list_display = [
        'reference', 'founder', 'project', 'amount_usd_display', 'amount_ngn_display',
        'bank_name', 'account_number', 'status_badge', 'created_at'
    ]
    list_filter = ['status', 'created_at']
    search_fields = [
        'founder__email', 'founder__first_name', 'founder__last_name',
        'project__title', 'reference', 'account_number', 'account_name'
    ]
    readonly_fields = [
        'reference', 'amount_ngn', 'created_at', 'processed_at', 'completed_at',
        'paystack_recipient_code', 'paystack_transfer_code', 'transfer_initiated_at',
    ]
    raw_id_fields = ['founder', 'project', 'processed_by']
    date_hierarchy = 'created_at'
    actions = ['mark_approved', 'initiate_paystack_transfer', 'mark_completed', 'mark_rejected']

    fieldsets = (
        ('Request Details', {
            'fields': ('reference', 'founder', 'project', 'amount_usd', 'amount_ngn', 'notes')
        }),
        ('Bank Account', {
            'fields': ('bank_name', 'bank_code', 'account_number', 'account_name')
        }),
        ('Status & Processing', {
            'fields': ('status', 'admin_notes', 'payment_reference', 'processed_by')
        }),
        ('Paystack Transfer', {
            'fields': ('paystack_recipient_code', 'paystack_transfer_code', 'transfer_initiated_at'),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'processed_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )

    def amount_usd_display(self, obj):
        return f"${obj.amount_usd:,.2f}"
    amount_usd_display.short_description = 'Amount (USD)'

    def amount_ngn_display(self, obj):
        return f"₦{obj.amount_ngn:,.2f}"
    amount_ngn_display.short_description = 'Amount (NGN)'

    def status_badge(self, obj):
        colors = {
            'pending': '#f59e0b',
            'approved': '#3b82f6',
            'processing': '#8b5cf6',
            'completed': '#10b981',
            'rejected': '#ef4444',
            'cancelled': '#6b7280',
        }
        color = colors.get(obj.status, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 12px; font-size: 11px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def mark_approved(self, request, queryset):
        count = 0
        for wr in queryset.filter(status='pending'):
            wr.approve(request.user)
            count += 1
        self.message_user(request, f"{count} withdrawal request(s) approved.")
    mark_approved.short_description = "Approve selected withdrawal requests"

    def initiate_paystack_transfer(self, request, queryset):
        from .paystack_transfer import process_withdrawal
        success_count = 0
        fail_msgs = []
        for wr in queryset.filter(status='approved'):
            ok, msg = process_withdrawal(wr)
            if ok:
                wr.processed_by = request.user
                wr.processed_at = timezone.now()
                wr.save(update_fields=['processed_by', 'processed_at'])
                success_count += 1
            else:
                fail_msgs.append(f"{wr.reference}: {msg}")
        if success_count:
            self.message_user(request, f"{success_count} transfer(s) initiated via Paystack.")
        for msg in fail_msgs:
            self.message_user(request, msg, level='ERROR')
    initiate_paystack_transfer.short_description = "Initiate Paystack transfer for approved requests"

    def mark_completed(self, request, queryset):
        count = 0
        for wr in queryset.filter(status__in=['approved', 'processing']):
            wr.mark_completed(request.user)
            count += 1
        self.message_user(request, f"{count} withdrawal request(s) marked as completed.")
    mark_completed.short_description = "Mark selected as Completed (transfer done)"

    def mark_rejected(self, request, queryset):
        count = 0
        for wr in queryset.filter(status__in=['pending', 'approved']):
            wr.reject(request.user)
            count += 1
        self.message_user(request, f"{count} withdrawal request(s) rejected.")
    mark_rejected.short_description = "Reject selected withdrawal requests"
