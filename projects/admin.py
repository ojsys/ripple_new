from django.contrib import admin
from django.utils.safestring import mark_safe
from django.db import models
from django.urls import reverse
from django.http import HttpResponseRedirect, HttpResponse
from django_json_widget.widgets import JSONEditorWidget
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.utils import get_column_letter
from datetime import datetime
import io

# Import only the models that definitely exist
from .models import (
    CustomUser, Category, Project, FundingType, HeaderLink, FooterSection, FounderProfile, InvestorProfile,
    Reward, Pledge, InvestmentTerm, Investment, SiteSettings, SocialMediaLink, HeroSlider, Testimonial,
    AboutPage, IncubatorAcceleratorPage, IncubatorApplication, TeamMember, RegistrationPayment, PendingRegistration
)

# Try to import optional models
try:
    from .models import Update
    HAS_UPDATE = True
except ImportError:
    HAS_UPDATE = False

try:
    from .models import Contact
    HAS_CONTACT = True
except ImportError:
    HAS_CONTACT = False

try:
    from .models import Announcement
    HAS_ANNOUNCEMENT = True
except ImportError:
    HAS_ANNOUNCEMENT = False

class ExcelExportMixin:
    """Mixin to add Excel export functionality to admin classes"""
    
    def export_to_excel(self, request, queryset):
        """Export selected objects to Excel"""
        # Create workbook and worksheet
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = f"{self.model._meta.verbose_name_plural}"
        
        # Define styles
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        header_alignment = Alignment(horizontal="center", vertical="center")
        
        # Get field names and verbose names
        field_names = self.get_export_fields()
        verbose_names = [self.get_field_verbose_name(field) for field in field_names]
        
        # Write headers
        for col, header in enumerate(verbose_names, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment
        
        # Write data
        for row, obj in enumerate(queryset, 2):
            for col, field_name in enumerate(field_names, 1):
                value = self.get_field_value(obj, field_name)
                ws.cell(row=row, column=col, value=value)
        
        # Auto-adjust column widths
        for col in range(1, len(field_names) + 1):
            column_letter = get_column_letter(col)
            ws.column_dimensions[column_letter].auto_size = True
            # Set minimum width
            ws.column_dimensions[column_letter].width = max(ws.column_dimensions[column_letter].width, 12)
        
        # Create HTTP response
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{self.model._meta.verbose_name_plural}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx"'
        
        # Save workbook to response
        wb.save(response)
        return response
    
    def get_export_fields(self):
        """Get fields to export - override in subclasses for custom fields"""
        return [field.name for field in self.model._meta.fields if not field.name.endswith('_ptr')]
    
    def get_field_verbose_name(self, field_name):
        """Get verbose name for field"""
        try:
            field = self.model._meta.get_field(field_name)
            return field.verbose_name.title()
        except:
            return field_name.replace('_', ' ').title()
    
    def get_field_value(self, obj, field_name):
        """Get field value with proper formatting"""
        try:
            # Handle related field lookups
            if '__' in field_name:
                parts = field_name.split('__')
                value = obj
                for part in parts:
                    value = getattr(value, part, None)
                    if value is None:
                        return ""
                return str(value)
            
            value = getattr(obj, field_name)
            
            # Handle different field types
            if value is None:
                return ""
            elif hasattr(value, 'all'):  # ManyToMany field
                return ", ".join(str(item) for item in value.all())
            elif hasattr(value, '__call__'):  # Method
                return str(value())
            elif isinstance(value, bool):
                return "Yes" if value else "No"
            elif isinstance(value, (datetime, type(datetime.now().date()))):
                return value.strftime("%Y-%m-%d %H:%M:%S") if hasattr(value, 'hour') else value.strftime("%Y-%m-%d")
            else:
                return str(value)
        except:
            return ""
    
    export_to_excel.short_description = "Export selected items to Excel"


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
class HeroSliderAdmin(admin.ModelAdmin, ExcelExportMixin):
    list_display = ('title', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('title',)
    actions = ['export_to_excel']
    
    def get_export_fields(self):
        return ['title', 'subtitle', 'image', 'is_active', 'created_at']

class CustomUserAdmin(UserAdmin, ExcelExportMixin):
    # Fields to display in the admin list view
    list_display = ('email', 'username', 'user_type', 'phone_number', 'is_staff')
    
    # Fields to filter by
    list_filter = ('user_type', 'is_staff', 'is_superuser')
    
    # Fields to search
    search_fields = ('email', 'username', 'phone_number')
    
    # Fields ordering
    ordering = ('-date_joined',)
    
    # Add Excel export action
    actions = ['export_to_excel']
    
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
    
    def get_export_fields(self):
        return ['email', 'username', 'first_name', 'last_name', 'phone_number', 'user_type', 'location', 'address_line1', 'city', 'state_province', 'country', 'is_active', 'is_staff', 'email_verified', 'date_joined', 'last_login']

@admin.register(FounderProfile)
class FounderProfileAdmin(admin.ModelAdmin, ExcelExportMixin):
    list_display = ('user', 'company_name', 'website')
    search_fields = ('user__email', 'company_name')
    actions = ['export_to_excel']
    
    def get_export_fields(self):
        return ['user__email', 'user__username', 'company_name', 'industry', 'website', 'bio', 'experience']

@admin.register(InvestorProfile)
class InvestorProfileAdmin(admin.ModelAdmin, ExcelExportMixin):
    list_display = ('user', 'investment_focus')
    list_filter = ('preferred_industries',)
    actions = ['export_to_excel']
    
    def get_export_fields(self):
        return ['user__email', 'user__username', 'investment_focus', 'preferred_industries']

@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin, ExcelExportMixin):
    list_display = ('name', 'position', 'company', 'rating', 'is_active', 'created_at')
    list_filter = ('is_active', 'rating')
    search_fields = ('name', 'position', 'company', 'content')
    list_editable = ('is_active',)
    actions = ['export_to_excel']
    
    def get_export_fields(self):
        return ['name', 'position', 'company', 'content', 'rating', 'is_active', 'created_at']

# Register the admin class
admin.site.register(CustomUser, CustomUserAdmin)

# Simple admin registrations with Excel export
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin, ExcelExportMixin):
    list_display = ('name',)
    search_fields = ('name',)
    actions = ['export_to_excel']
    
    def get_export_fields(self):
        return ['name']

@admin.register(FundingType)
class FundingTypeAdmin(admin.ModelAdmin, ExcelExportMixin):
    list_display = ('name', 'description')
    search_fields = ('name',)
    actions = ['export_to_excel']
    
    def get_export_fields(self):
        return ['name', 'description']

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin, ExcelExportMixin):
    list_display = ('title', 'creator', 'category', 'funding_goal', 'amount_raised', 'status')
    list_filter = ('category', 'status', 'funding_type', 'created_at')
    search_fields = ('title', 'creator__email')
    actions = ['export_to_excel']
    
    def get_export_fields(self):
        return ['title', 'creator__email', 'creator__username', 'category__name', 'funding_type__name', 
                'funding_goal', 'amount_raised', 'total_investment_raised', 'description', 'short_description', 
                'location', 'video_url', 'status', 'admin_notes', 'created_at', 'deadline']

@admin.register(Reward)
class RewardAdmin(admin.ModelAdmin, ExcelExportMixin):
    list_display = ('title', 'project', 'amount')
    list_filter = ('project',)
    search_fields = ('title', 'project__title')
    actions = ['export_to_excel']
    
    def get_export_fields(self):
        return ['title', 'project__title', 'description', 'amount']

@admin.register(Pledge)
class PledgeAdmin(admin.ModelAdmin, ExcelExportMixin):
    list_display = ('backer', 'project', 'amount', 'pledged_at')
    list_filter = ('pledged_at', 'project')
    search_fields = ('backer__email', 'project__title')
    actions = ['export_to_excel']
    
    def get_export_fields(self):
        return ['backer__email', 'backer__username', 'project__title', 'amount', 'reward__title', 'pledged_at']

@admin.register(InvestmentTerm)
class InvestmentTermAdmin(admin.ModelAdmin, ExcelExportMixin):
    list_display = ('project', 'equity_offered', 'minimum_investment', 'valuation')
    list_filter = ('project',)
    search_fields = ('project__title',)
    actions = ['export_to_excel']
    
    def get_export_fields(self):
        return ['project__title', 'equity_offered', 'minimum_investment', 'maximum_investment', 'valuation', 'deadline']

@admin.register(Investment)
class InvestmentAdmin(admin.ModelAdmin, ExcelExportMixin):
    list_display = ('investor', 'project', 'amount', 'status', 'created_at')
    list_filter = ('status', 'created_at', 'project')
    search_fields = ('investor__email', 'project__title')
    actions = ['export_to_excel']
    
    def get_export_fields(self):
        return ['investor__email', 'investor__username', 'project__title', 'amount', 'equity_percentage', 
                'actual_return', 'terms__equity_offered', 'status', 'is_counted', 'created_at']

@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin, ExcelExportMixin):
    list_display = ('name', 'position', 'order', 'created_at') 
    search_fields = ('name', 'position')
    ordering = ('order',)
    actions = ['export_to_excel']
    
    def get_export_fields(self):
        return ['name', 'position', 'bio', 'linkedin_url', 'email', 'is_active', 'is_visible', 'order', 'created_at', 'updated_at']

@admin.register(AboutPage)
class AboutPageAdmin(admin.ModelAdmin, ExcelExportMixin):
    list_display = ('title', 'last_updated')
    search_fields = ('title',)
    actions = ['export_to_excel']
    
    def get_export_fields(self):
        return ['title', 'content', 'mission', 'vision', 'core_values', 'about_video_description', 'about_video_url', 'last_updated']

@admin.register(IncubatorAcceleratorPage)
class IncubatorAcceleratorPageAdmin(admin.ModelAdmin, ExcelExportMixin):
    list_display = ('title', 'image', 'is_accepting_applications', 'application_deadline', 'last_updated')
    list_filter = ('is_accepting_applications',)
    search_fields = ('title', 'program_description')
    actions = ['export_to_excel']
    
    fieldsets = (
        (None, {
            'fields': ('title','image', 'program_description')
        }),
        ('Application Details', {
            'fields': ('application_info', 'application_deadline', 'is_accepting_applications')
        }),
    )
    
    def get_export_fields(self):
        return ['title', 'program_description', 'application_info', 'application_deadline', 'is_accepting_applications', 'last_updated']

@admin.register(IncubatorApplication)
class IncubatorApplicationAdmin(admin.ModelAdmin, ExcelExportMixin):
    list_display = ('project', 'applicant_name', 'application_date', 'status')
    list_filter = ('status', 'application_date')
    search_fields = ('project', 'applicant_name', 'applicant_email')
    actions = ['export_to_excel']
    
    def get_export_fields(self):
        return ['project', 'applicant_name', 'applicant_email', 'applicant_phone', 'applicant_company', 
                'website', 'stage', 'industry', 'application_text', 'traction', 'team_background', 
                'goals_for_program', 'funding_raised', 'funding_needed', 'application_date', 'status', 'reviewed']

# Register optional models if they exist
if HAS_UPDATE:
    @admin.register(Update)
    class UpdateAdmin(admin.ModelAdmin, ExcelExportMixin):
        list_display = ('title', 'project', 'created_at')
        list_filter = ('project', 'created_at')
        search_fields = ('title', 'project__title')
        actions = ['export_to_excel']
        
        def get_export_fields(self):
            return ['title', 'project__title', 'content', 'created_at']

if HAS_CONTACT:
    @admin.register(Contact)
    class ContactAdmin(admin.ModelAdmin, ExcelExportMixin):
        list_display = ('name', 'email', 'subject', 'created_at')
        list_filter = ('created_at',)
        search_fields = ('name', 'email', 'subject')
        actions = ['export_to_excel']
        
        def get_export_fields(self):
            return ['name', 'email', 'subject', 'message', 'created_at']

if HAS_ANNOUNCEMENT:
    @admin.register(Announcement)
    class AnnouncementAdmin(admin.ModelAdmin, ExcelExportMixin):
        list_display = ('message', 'start_date', 'end_date', 'is_active', 'style')
        list_filter = ('is_active', 'style', 'start_date')
        search_fields = ('message',)
        actions = ['export_to_excel']
        
        def get_export_fields(self):
            return ['message', 'start_date', 'end_date', 'is_active', 'style']


@admin.register(RegistrationPayment)
class RegistrationPaymentAdmin(admin.ModelAdmin, ExcelExportMixin):
    list_display = ('user', 'amount_usd', 'amount_ngn', 'status', 'created_at', 'paystack_reference')
    list_filter = ('status', 'created_at')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'paystack_reference')
    readonly_fields = ('paystack_reference', 'created_at', 'updated_at')
    actions = ['export_to_excel']
    
    def get_export_fields(self):
        return ['user__email', 'user__first_name', 'user__last_name', 'user__user_type', 
                'amount_usd', 'amount_ngn', 'paystack_reference', 'status', 'created_at', 'updated_at']


@admin.register(PendingRegistration)
class PendingRegistrationAdmin(admin.ModelAdmin, ExcelExportMixin):
    list_display = ('email', 'first_name', 'last_name', 'user_type', 'payment_status', 'created_at', 'expires_at')
    list_filter = ('user_type', 'payment_status', 'created_at')
    search_fields = ('email', 'first_name', 'last_name', 'paystack_reference')
    readonly_fields = ('paystack_reference', 'password_hash', 'created_at', 'expires_at')
    actions = ['export_to_excel', 'delete_expired_registrations']
    
    def delete_expired_registrations(self, request, queryset):
        """Delete expired pending registrations"""
        from django.utils import timezone
        expired_count = queryset.filter(expires_at__lt=timezone.now()).count()
        queryset.filter(expires_at__lt=timezone.now()).delete()
        self.message_user(request, f'{expired_count} expired registrations deleted.')
    delete_expired_registrations.short_description = "Delete expired registrations"
    
    def get_export_fields(self):
        return ['email', 'first_name', 'last_name', 'user_type', 'phone_number', 
                'amount_usd', 'amount_ngn', 'paystack_reference', 'payment_status', 'created_at', 'expires_at']