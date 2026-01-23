from django.contrib import admin
from .models import (
    TeamMember, AboutPage, SiteSettings, HeroSlider,
    HeaderLink, FooterSection, ThemeSettings, Announcement,
    SocialMediaLink, SEOSettings, Testimonial, Contact,
    HomePage, HowItWorksStep, PartnerLogo, NewsletterSubscriber,
    LegalPage
)


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ['name', 'position', 'is_active', 'is_visible', 'order']
    list_filter = ['is_active', 'is_visible']
    list_editable = ['is_active', 'is_visible', 'order']
    search_fields = ['name', 'position']
    ordering = ['order']


@admin.register(AboutPage)
class AboutPageAdmin(admin.ModelAdmin):
    list_display = ['title', 'last_updated']
    filter_horizontal = ['team_members']


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ['site_name', 'primary_color', 'secondary_color']

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()


@admin.register(HeroSlider)
class HeroSliderAdmin(admin.ModelAdmin):
    list_display = ['title', 'is_active', 'created_at']
    list_filter = ['is_active']
    list_editable = ['is_active']


class HeaderLinkInline(admin.TabularInline):
    model = HeaderLink
    extra = 1


class FooterSectionInline(admin.TabularInline):
    model = FooterSection
    extra = 1


@admin.register(SocialMediaLink)
class SocialMediaLinkAdmin(admin.ModelAdmin):
    list_display = ['platform', 'url', 'icon_class', 'order']
    list_editable = ['url', 'icon_class', 'order']
    ordering = ['order']


@admin.register(ThemeSettings)
class ThemeSettingsAdmin(admin.ModelAdmin):
    list_display = ['primary_color', 'secondary_color']

    def has_add_permission(self, request):
        return not ThemeSettings.objects.exists()


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ['message', 'style', 'is_active', 'start_date', 'end_date']
    list_filter = ['is_active', 'style']
    list_editable = ['is_active']


@admin.register(SEOSettings)
class SEOSettingsAdmin(admin.ModelAdmin):
    list_display = ['meta_title', 'meta_description']

    def has_add_permission(self, request):
        return not SEOSettings.objects.exists()


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ['name', 'position', 'company', 'rating', 'is_active', 'created_at']
    list_filter = ['is_active', 'rating']
    list_editable = ['is_active']
    search_fields = ['name', 'company', 'content']


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'subject', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'email', 'subject', 'message']
    readonly_fields = ['name', 'email', 'subject', 'message', 'created_at']
    date_hierarchy = 'created_at'

    def has_add_permission(self, request):
        return False


class HowItWorksStepInline(admin.TabularInline):
    model = HowItWorksStep
    extra = 1
    fields = ['order', 'icon', 'title', 'description']


@admin.register(HomePage)
class HomePageAdmin(admin.ModelAdmin):
    inlines = [HowItWorksStepInline]

    fieldsets = (
        ('Hero Section', {
            'fields': (
                'hero_title', 'hero_subtitle', 'hero_background', 'hero_video_url',
                'hero_cta_primary_text', 'hero_cta_primary_url',
                'hero_cta_secondary_text', 'hero_cta_secondary_url'
            ),
            'classes': ('collapse',)
        }),
        ('Stats Section', {
            'fields': (
                'show_stats',
                ('stat_1_value', 'stat_1_label'),
                ('stat_2_value', 'stat_2_label'),
                ('stat_3_value', 'stat_3_label'),
                ('stat_4_value', 'stat_4_label'),
            ),
            'classes': ('collapse',)
        }),
        ('How It Works Section', {
            'fields': ('show_how_it_works', 'how_it_works_title', 'how_it_works_subtitle'),
            'classes': ('collapse',)
        }),
        ('Featured Projects Section', {
            'fields': ('show_featured_projects', 'featured_projects_title', 'featured_projects_subtitle'),
            'classes': ('collapse',)
        }),
        ('SRT Token Section', {
            'fields': (
                'show_srt_section', 'srt_title', 'srt_subtitle',
                'srt_description', 'srt_image', 'srt_cta_text', 'srt_cta_url'
            ),
            'classes': ('collapse',)
        }),
        ('Incubator Section', {
            'fields': (
                'show_incubator_section', 'incubator_title', 'incubator_subtitle',
                'incubator_description', 'incubator_image', 'incubator_cta_text', 'incubator_cta_url'
            ),
            'classes': ('collapse',)
        }),
        ('Testimonials Section', {
            'fields': ('show_testimonials', 'testimonials_title', 'testimonials_subtitle'),
            'classes': ('collapse',)
        }),
        ('Partners Section', {
            'fields': ('show_partners', 'partners_title'),
            'classes': ('collapse',)
        }),
        ('Call to Action Section', {
            'fields': (
                'show_cta_section', 'cta_title', 'cta_subtitle',
                'cta_primary_text', 'cta_primary_url',
                'cta_secondary_text', 'cta_secondary_url'
            ),
            'classes': ('collapse',)
        }),
        ('Newsletter Section', {
            'fields': ('show_newsletter', 'newsletter_title', 'newsletter_subtitle'),
            'classes': ('collapse',)
        }),
    )

    def has_add_permission(self, request):
        return not HomePage.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(PartnerLogo)
class PartnerLogoAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'order']
    list_editable = ['is_active', 'order']
    list_filter = ['is_active']
    search_fields = ['name']


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ['email', 'subscribed_at', 'is_active']
    list_filter = ['is_active', 'subscribed_at']
    search_fields = ['email']
    readonly_fields = ['email', 'subscribed_at']
    date_hierarchy = 'subscribed_at'

    def has_add_permission(self, request):
        return False


@admin.register(LegalPage)
class LegalPageAdmin(admin.ModelAdmin):
    list_display = ['page_type', 'title', 'version', 'effective_date', 'is_published', 'updated_at']
    list_filter = ['page_type', 'is_published']
    list_editable = ['is_published']
    search_fields = ['title', 'content']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'updated_at'

    fieldsets = (
        ('Page Information', {
            'fields': ('page_type', 'title', 'subtitle'),
        }),
        ('Content', {
            'fields': ('content',),
            'description': 'Use the rich text editor to format the content. You can add headings, lists, links, and more.',
        }),
        ('Version & Status', {
            'fields': ('version', 'effective_date', 'is_published', 'show_table_of_contents'),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        """Make page_type readonly after creation to prevent duplicates."""
        if obj:
            return self.readonly_fields + ('page_type',)
        return self.readonly_fields
