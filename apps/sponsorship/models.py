from django.db import models
from django.utils.text import slugify
from ckeditor.fields import RichTextField


class SponsorshipTier(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    price_usd = models.DecimalField(max_digits=10, decimal_places=2, help_text="Display price in USD")
    tagline = models.CharField(max_length=200, help_text="One-line value proposition")
    description = RichTextField(help_text="What this tier includes at a high level")
    benefits = RichTextField(help_text="Bullet list of specific sponsor benefits")
    cohort_slots = models.PositiveIntegerField(default=0, help_text="Number of founder slots included")
    icon_class = models.CharField(max_length=50, default='fas fa-star', help_text="Font Awesome icon class")
    color_class = models.CharField(
        max_length=20,
        default='bronze',
        choices=[('bronze', 'Bronze'), ('silver', 'Silver'), ('gold', 'Gold'), ('custom', 'Custom/Enterprise')],
    )
    is_featured = models.BooleanField(default=False, help_text="Highlight this tier on the page")
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
        verbose_name = 'Sponsorship Tier'
        verbose_name_plural = 'Sponsorship Tiers'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def price_display(self):
        if self.price_usd == 0:
            return 'Custom'
        return f'${self.price_usd:,.0f}'


class SponsorshipInquiry(models.Model):
    ORG_TYPE_CHOICES = [
        ('corporate', 'Corporate Company'),
        ('ngo', 'NGO / Non-Profit'),
        ('dev_partner', 'Development Partner'),
        ('government', 'Government Agency'),
        ('other', 'Other'),
    ]
    BUDGET_CHOICES = [
        ('under_5k', 'Under $5,000'),
        ('5k_15k', '$5,000 – $15,000'),
        ('15k_50k', '$15,000 – $50,000'),
        ('above_50k', '$50,000+'),
        ('tbd', 'To Be Discussed'),
    ]
    STATUS_CHOICES = [
        ('new', 'New'),
        ('contacted', 'Contacted'),
        ('in_discussion', 'In Discussion'),
        ('closed_won', 'Closed — Won'),
        ('closed_lost', 'Closed — Lost'),
    ]

    company_name = models.CharField(max_length=200)
    contact_name = models.CharField(max_length=150)
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=30, blank=True)
    organization_type = models.CharField(max_length=20, choices=ORG_TYPE_CHOICES, default='corporate')
    tier = models.ForeignKey(
        SponsorshipTier, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='inquiries'
    )
    program_interest = models.TextField(help_text="What kind of program or cohort are they interested in?")
    budget_range = models.CharField(max_length=20, choices=BUDGET_CHOICES, default='tbd')
    message = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    internal_notes = models.TextField(blank=True, help_text="Internal team notes — not visible to the sponsor")

    class Meta:
        ordering = ['-submitted_at']
        verbose_name = 'Sponsorship Inquiry'
        verbose_name_plural = 'Sponsorship Inquiries'

    def __str__(self):
        return f"{self.company_name} — {self.contact_name} ({self.get_status_display()})"


class SponsorshipPage(models.Model):
    hero_title = models.CharField(max_length=200, default="Partner With Nigeria's Startup Ecosystem")
    hero_subtitle = models.TextField(
        default="Sponsor a LaunchPadi cohort, co-design a program, or access Nigeria's most promising idea-stage founders — before anyone else."
    )
    intro_text = RichTextField(
        default="<p>StartUp Ripple is not a fund. We are an ecosystem operator. We source and develop Nigeria's earliest-stage founders — and we do it with the support of corporates, NGOs, and development partners who share our vision for African innovation.</p>"
    )
    why_sponsor_text = RichTextField(
        default="<ul><li>Direct access to pre-vetted, idea-stage Nigerian founders</li><li>Brand visibility across our founder and investor network</li><li>CSR impact reporting for development partners</li><li>Co-design programs aligned to your sector or mandate</li><li>First-look deal flow from each cohort's demo day</li></ul>"
    )
    show_tiers = models.BooleanField(default=True)
    cta_text = models.CharField(max_length=100, default="Send Us an Enquiry")
    last_updated = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return "Sponsorship Page"

    class Meta:
        verbose_name = 'Sponsorship Page'
        verbose_name_plural = 'Sponsorship Page'
