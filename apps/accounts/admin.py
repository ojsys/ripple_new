from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import (
    CustomUser, FounderProfile, InvestorProfile, PartnerProfile,
    RegistrationPayment, PendingRegistration
)


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ['email', 'get_full_name', 'user_type', 'is_active',
                    'registration_fee_paid', 'email_verified', 'date_joined']
    list_filter = ['user_type', 'is_active', 'registration_fee_paid', 'email_verified', 'is_staff']
    search_fields = ['email', 'first_name', 'last_name', 'phone_number']
    ordering = ['-date_joined']

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {
            'fields': ('first_name', 'last_name', 'phone_number', 'user_type')
        }),
        ('Address', {
            'fields': ('address_line1', 'address_line2', 'city', 'state_province', 'postal_code', 'country', 'location'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active', 'email_verified', 'registration_fee_paid', 'profile_completed')
        }),
        ('Permissions', {
            'fields': ('is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        ('Important Dates', {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',)
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'first_name', 'last_name',
                       'phone_number', 'user_type'),
        }),
    )


@admin.register(FounderProfile)
class FounderProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'company_name', 'industry', 'has_cv']
    list_filter = ['industry']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'company_name']
    raw_id_fields = ['user']

    def has_cv(self, obj):
        return bool(obj.cv)
    has_cv.boolean = True
    has_cv.short_description = 'CV Uploaded'


@admin.register(InvestorProfile)
class InvestorProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'preferred_industries', 'investment_focus_preview']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'preferred_industries']
    raw_id_fields = ['user']

    def investment_focus_preview(self, obj):
        if obj.investment_focus:
            return obj.investment_focus[:100] + '...' if len(obj.investment_focus) > 100 else obj.investment_focus
        return '-'
    investment_focus_preview.short_description = 'Investment Focus'


@admin.register(PartnerProfile)
class PartnerProfileAdmin(admin.ModelAdmin):
    list_display = ['partner_id', 'user', 'company_name', 'accreditation_status',
                    'kyc_completed', 'risk_profile', 'created_at']
    list_filter = ['accreditation_status', 'kyc_completed', 'risk_profile']
    search_fields = ['partner_id', 'user__email', 'user__first_name',
                     'user__last_name', 'company_name']
    readonly_fields = ['partner_id', 'created_at', 'updated_at']
    raw_id_fields = ['user']

    fieldsets = (
        ('Partner Info', {
            'fields': ('user', 'partner_id', 'image')
        }),
        ('Professional', {
            'fields': ('company_name', 'occupation', 'bio')
        }),
        ('Verification', {
            'fields': ('accreditation_status', 'kyc_completed')
        }),
        ('Investment Settings', {
            'fields': ('risk_profile', 'monthly_investment_limit')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(RegistrationPayment)
class RegistrationPaymentAdmin(admin.ModelAdmin):
    list_display = ['user', 'amount_usd', 'amount_ngn', 'status', 'paystack_reference', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['user__email', 'paystack_reference']
    readonly_fields = ['user', 'amount_usd', 'amount_ngn', 'paystack_reference', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(PendingRegistration)
class PendingRegistrationAdmin(admin.ModelAdmin):
    list_display = ['email', 'first_name', 'last_name', 'user_type',
                    'payment_status', 'is_expired_display', 'created_at']
    list_filter = ['user_type', 'payment_status', 'created_at']
    search_fields = ['email', 'first_name', 'last_name']
    readonly_fields = ['password_hash', 'created_at']
    date_hierarchy = 'created_at'

    def is_expired_display(self, obj):
        if obj.is_expired():
            return format_html('<span style="color: red;">Expired</span>')
        return format_html('<span style="color: green;">Valid</span>')
    is_expired_display.short_description = 'Status'

    actions = ['delete_expired']

    def delete_expired(self, request, queryset):
        from django.utils import timezone
        expired = queryset.filter(expires_at__lt=timezone.now())
        count = expired.count()
        expired.delete()
        self.message_user(request, f"Deleted {count} expired registrations.")
    delete_expired.short_description = "Delete expired registrations"
