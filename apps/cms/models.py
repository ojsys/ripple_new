from django.db import models
from django.core.exceptions import ValidationError
from ckeditor.fields import RichTextField

class TeamMember(models.Model):
    name = models.CharField(max_length=100)
    position = models.CharField(max_length=100)
    bio = RichTextField()
    image = models.ImageField(upload_to='team/', blank=True)
    linkedin_url = models.URLField(blank=True)
    email = models.EmailField(blank=True, help_text="Contact email for the team member")
    is_active = models.BooleanField(default=True, help_text="Indicate if the team member is currently active")
    is_visible = models.BooleanField(default=True, help_text="Indicate if the team member should be visible on the site")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.name

class AboutPage(models.Model):
    title = models.CharField(max_length=200)
    content = RichTextField()
    mission = models.TextField()
    vision = models.TextField()
    core_values = RichTextField()
    about_image = models.ImageField(upload_to='about/', blank=True)
    about_video = models.FileField(upload_to='about/videos/', blank=True)
    about_video_thumbnail = models.ImageField(upload_to='about/thumbnails/', blank=True)
    about_video_description = models.TextField(blank=True)
    about_video_url = models.URLField(blank=True)
    about_video_embed_code = models.TextField(blank=True, help_text="Embed code for the video, e.g., from YouTube")
    team_members = models.ManyToManyField(TeamMember, blank=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name_plural = "About Page Content"

class SiteSettings(models.Model):
    site_name = models.CharField(max_length=100, default='StartUpRipples')
    logo = models.ImageField(upload_to='site/logo/', blank=True)
    favicon = models.ImageField(upload_to='site/favicon/', blank=True)
    primary_color = models.CharField(max_length=7, default='#28a745')
    secondary_color = models.CharField(max_length=7, default='#2c3e50')

    # Singleton implementation
    def save(self, *args, **kwargs):
        if not self.pk and SiteSettings.objects.exists():
            raise ValidationError("Only one SiteSettings instance can exist")
        super().save(*args, **kwargs)


    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return "Site Settings"

    class Meta:
        verbose_name_plural = "Site Settings"


class HeroSlider(models.Model):
    title = models.CharField(max_length=255, blank=True)
    subtitle = models.TextField(blank=True)
    image = models.ImageField(upload_to='slider_images/')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title or f"Slider {self.id}"
    

class HeaderLink(models.Model):
    site_settings = models.ForeignKey(
        SiteSettings, 
        on_delete=models.CASCADE,
        related_name='header_links'
    )
    title = models.CharField(max_length=50)
    url = models.CharField(max_length=200)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']

class FooterSection(models.Model):
    site_settings = models.ForeignKey(
        SiteSettings,
        on_delete=models.CASCADE,
        related_name='footer_sections'
    )
    title = models.CharField(max_length=50)
    content = models.TextField(help_text="HTML content")
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order']


class ThemeSettings(models.Model):
    primary_color = models.CharField(max_length=7, default='#28a745')
    secondary_color = models.CharField(max_length=7, default='#2c3e50')
    custom_css = models.TextField(blank=True)
    
    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj
    

class Announcement(models.Model):
    message = models.TextField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    style = models.CharField(max_length=20, choices=[
        ('info', 'Info (Blue)'),
        ('alert', 'Alert (Red)'),
        ('success', 'Success (Green)')
    ], default='info')


class SocialMediaLink(models.Model):
    site_settings = models.ForeignKey(
        SiteSettings,
        on_delete=models.CASCADE,
        related_name='social_links'
    )

    PLATFORM_CHOICES = [
        ('facebook', 'Facebook'),
        ('twitter', 'Twitter'),
        ('linkedin', 'LinkedIn'),
        ('instagram', 'Instagram'),
        ('youtube', 'YouTube')
    ]
    
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
    url = models.URLField()
    icon_class = models.CharField(max_length=50, blank=True, null=True)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order']

    def get_icon_class(self):
        """Returns the Font Awesome icon class for the platform."""
        icon_map = {
            'facebook': 'fab fa-facebook-f',
            'twitter': 'fab fa-twitter',
            'linkedin': 'fab fa-linkedin-in',
            'instagram': 'fab fa-instagram',
            'youtube': 'fab fa-youtube',
        }
        return self.icon_class or icon_map.get(self.platform, 'fas fa-share-alt') # Default if custom icon not provided


class SEOSettings(models.Model):
    meta_title = models.CharField(max_length=60, blank=True)
    meta_description = models.TextField(max_length=160, blank=True)
    meta_keywords = models.CharField(max_length=255, blank=True)
    og_image = models.ImageField(upload_to='seo/', blank=True)
    
    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

class Testimonial(models.Model):
    name = models.CharField(max_length=100)
    position = models.CharField(max_length=100)
    company = models.CharField(max_length=100, blank=True, null=True)
    image = models.ImageField(upload_to='testimonials/', blank=True, null=True)
    content = models.TextField()
    rating = models.IntegerField(default=5, choices=[(i, i) for i in range(1, 6)])
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} - {self.position}"
    
    class Meta:
        ordering = ['-created_at']
    

class Contact(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=255)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.subject}"

    class Meta:
        ordering = ['-created_at']


class HomePage(models.Model):
    """CMS model for the landing page content."""

    # Hero Section
    hero_title = models.CharField(max_length=200, default="Empowering African Startups")
    hero_subtitle = models.TextField(default="Join the revolution in startup funding. Connect founders with investors, donors, and partners through innovative crowdfunding and token-based investments.")
    hero_background = models.ImageField(upload_to='homepage/hero/', blank=True, null=True)
    hero_video_url = models.URLField(blank=True, null=True, help_text="Optional background video URL")
    hero_cta_primary_text = models.CharField(max_length=50, default="Explore Projects")
    hero_cta_primary_url = models.CharField(max_length=200, default="/projects/")
    hero_cta_secondary_text = models.CharField(max_length=50, default="Start a Project")
    hero_cta_secondary_url = models.CharField(max_length=200, default="/projects/create/")

    # Stats Section
    show_stats = models.BooleanField(default=True)
    stat_1_value = models.CharField(max_length=20, default="$2.5M+")
    stat_1_label = models.CharField(max_length=50, default="Total Funded")
    stat_2_value = models.CharField(max_length=20, default="150+")
    stat_2_label = models.CharField(max_length=50, default="Projects Launched")
    stat_3_value = models.CharField(max_length=20, default="5,000+")
    stat_3_label = models.CharField(max_length=50, default="Active Investors")
    stat_4_value = models.CharField(max_length=20, default="12")
    stat_4_label = models.CharField(max_length=50, default="African Countries")

    # How It Works Section
    show_how_it_works = models.BooleanField(default=True)
    how_it_works_title = models.CharField(max_length=100, default="How StartUpRipple Works")
    how_it_works_subtitle = models.TextField(default="Simple, transparent, and effective. Our platform connects innovative ideas with the resources they need to succeed.")

    # Featured Projects Section
    show_featured_projects = models.BooleanField(default=True)
    featured_projects_title = models.CharField(max_length=100, default="Featured Projects")
    featured_projects_subtitle = models.TextField(default="Discover innovative startups seeking funding")

    # SRT Token Section
    show_srt_section = models.BooleanField(default=True)
    srt_title = models.CharField(max_length=100, default="StartUp Ripple Tokens (SRT)")
    srt_subtitle = models.TextField(default="A revolutionary way to invest in Africa's most promising startups")
    srt_description = RichTextField(default="SRT tokens allow you to diversify your investment across multiple vetted ventures. Purchase tokens, invest in curated opportunities, and earn returns as startups succeed.")
    srt_image = models.ImageField(upload_to='homepage/srt/', blank=True, null=True)
    srt_cta_text = models.CharField(max_length=50, default="Become a Partner")
    srt_cta_url = models.CharField(max_length=200, default="/accounts/signup/")

    # Incubator Section
    show_incubator_section = models.BooleanField(default=True)
    incubator_title = models.CharField(max_length=100, default="Accelerator Program")
    incubator_subtitle = models.TextField(default="Take your startup to the next level")
    incubator_description = RichTextField(default="Our 12-week intensive program provides mentorship, funding, and resources to help early-stage startups scale rapidly.")
    incubator_image = models.ImageField(upload_to='homepage/incubator/', blank=True, null=True)
    incubator_cta_text = models.CharField(max_length=50, default="Apply Now")
    incubator_cta_url = models.CharField(max_length=200, default="/incubator/apply/")

    # Testimonials Section
    show_testimonials = models.BooleanField(default=True)
    testimonials_title = models.CharField(max_length=100, default="Success Stories")
    testimonials_subtitle = models.TextField(default="Hear from founders and investors who've found success on our platform")

    # Partners Section
    show_partners = models.BooleanField(default=True)
    partners_title = models.CharField(max_length=100, default="Our Partners & Supporters")

    # CTA Section
    show_cta_section = models.BooleanField(default=True)
    cta_title = models.CharField(max_length=100, default="Ready to Make an Impact?")
    cta_subtitle = models.TextField(default="Join thousands of founders and investors building the future of African innovation")
    cta_primary_text = models.CharField(max_length=50, default="Get Started")
    cta_primary_url = models.CharField(max_length=200, default="/accounts/signup/")
    cta_secondary_text = models.CharField(max_length=50, default="Learn More")
    cta_secondary_url = models.CharField(max_length=200, default="/cms/about/")

    # Newsletter Section
    show_newsletter = models.BooleanField(default=True)
    newsletter_title = models.CharField(max_length=100, default="Stay Updated")
    newsletter_subtitle = models.TextField(default="Get the latest news on funding opportunities and startup success stories")

    # Meta
    last_updated = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return "Home Page Content"

    class Meta:
        verbose_name = "Home Page"
        verbose_name_plural = "Home Page"


class HowItWorksStep(models.Model):
    """Steps for the How It Works section."""
    homepage = models.ForeignKey(HomePage, on_delete=models.CASCADE, related_name='how_it_works_steps')
    icon = models.CharField(max_length=50, default="fas fa-lightbulb", help_text="Font Awesome icon class")
    title = models.CharField(max_length=100)
    description = models.TextField()
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title


class PartnerLogo(models.Model):
    """Partner/Sponsor logos for the homepage."""
    name = models.CharField(max_length=100)
    logo = models.ImageField(upload_to='homepage/partners/')
    website_url = models.URLField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.name


class NewsletterSubscriber(models.Model):
    """Newsletter subscription model."""
    email = models.EmailField(unique=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.email

    class Meta:
        ordering = ['-subscribed_at']


class LegalPage(models.Model):
    """Model for legal pages like Terms & Conditions, Privacy Policy, etc."""

    PAGE_TYPES = [
        ('terms_of_service', 'Terms of Service'),
        ('investor_terms', 'Investor Terms'),
        ('privacy_policy', 'Privacy Policy'),
        ('cookie_policy', 'Cookie Policy'),
        ('refund', 'Refund Policy'),
        ('aml', 'Anti-Money Laundering Policy'),
    ]

    page_type = models.CharField(max_length=20, choices=PAGE_TYPES, unique=True)
    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=500, blank=True,
                                help_text="Optional subtitle or brief description")
    content = RichTextField(help_text="Main content of the page. Use the editor to format text.")
    effective_date = models.DateField(null=True, blank=True,
                                      help_text="When this version of the document becomes effective")
    version = models.CharField(max_length=20, default="1.0",
                              help_text="Version number of this document")
    is_published = models.BooleanField(default=True,
                                       help_text="Only published pages are visible to users")
    show_table_of_contents = models.BooleanField(default=True,
                                                  help_text="Auto-generate table of contents from headings")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Legal Page"
        verbose_name_plural = "Legal Pages"
        ordering = ['page_type']

    def __str__(self):
        return self.get_page_type_display()

    @classmethod
    def get_page(cls, page_type):
        """Get a published legal page by type."""
        try:
            return cls.objects.get(page_type=page_type, is_published=True)
        except cls.DoesNotExist:
            return None

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('cms:legal_page', kwargs={'page_type': self.page_type})
