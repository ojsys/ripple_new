from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.utils import timezone
from django.contrib.auth.models import AbstractUser
from django.urls import reverse
from django.conf import settings
from django.db import transaction
from django.db.models import F, ExpressionWrapper, FloatField
from ckeditor.fields import RichTextField

class CustomUser(AbstractUser):
    USER_TYPES = (
        ('', 'Select User Type'),
        ('founder', 'Founder'),
        ('donor', 'Donor/Pledger'),
        ('investor', 'Investor'),
    )
    
    user_type = models.CharField(max_length=20, choices=USER_TYPES, blank=False, null=False)
    phone_number = models.CharField(max_length=20)
    profile_completed = models.BooleanField(default=False)
    location = models.CharField(max_length=100, blank=True, null=True)
    
    # New address fields
    address_line1 = models.CharField(max_length=255, blank=True, null=True)
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state_province = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    email_verified = models.BooleanField(default=False)
    registration_fee_paid = models.BooleanField(default=False)
    
    # Add these if missing
    email = models.EmailField(unique=True)
    
    # Update the USERNAME_FIELD if needed
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return f"{self.get_full_name()} ({self.get_user_type_display()})"
    
    def get_registration_fee(self):
        """Get the registration fee amount based on user type"""
        if self.user_type == 'founder':
            return 5.00  # $5 USD
        elif self.user_type in ['donor', 'investor']:
            return 25.00  # $25 USD
        return 0.00
    
    def get_registration_fee_ngn(self):
        """Get the registration fee in NGN (using the same conversion rate as other payments)"""
        usd_amount = self.get_registration_fee()
        return int(usd_amount * 1600)  # 1 USD = 1600 NGN


class FounderProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='profile_images/', blank=True, null=True)
    company_name = models.CharField(max_length=100, blank=True, null=True)
    industry = models.CharField(max_length=100, blank=True, null=True)
    experience = models.TextField(blank=True, null=True)
    cv = models.FileField(upload_to='founder_cvs/', blank=True, null=True)
    
    def __str__(self):
        return f"{self.user.username}'s Founder Profile"
    
    website = models.URLField(blank=True)
    bio = models.TextField()

class InvestorProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    investment_focus = models.TextField()
    preferred_industries = models.CharField(max_length=200)



class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Categories"
    
    


class FundingType(models.Model):
    name = models.CharField(max_length=100)  # e.g., "Donation", "Equity", "Loan"
    description = models.TextField()

    def __str__(self):
        return self.name

class Project(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    
    title = models.CharField(max_length=200)
    description = RichTextField()  # Changed from TextField to RichTextField
    funding_goal = models.DecimalField(max_digits=10, decimal_places=2)
    amount_raised = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_investment_raised = models.DecimalField(max_digits=10, decimal_places=2, default=0)  
    created_at = models.DateTimeField(default=timezone.now)
    deadline = models.DateTimeField()
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='projects_created')
    image = models.ImageField(upload_to='project_images/')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    funding_type = models.ForeignKey(FundingType, on_delete=models.SET_NULL, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    short_description = models.CharField(max_length=255, blank=True, null=True)
    video_url = models.URLField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_notes = models.TextField(blank=True, null=True, help_text="Notes from admin about approval/rejection")

    def __str__(self):
        return self.title
    
    

    def get_calculated_percent(self):
        """Method to access the annotated value or fallback"""
        if hasattr(self, 'annotated_percent'):
            return self.annotated_percent
        return self.percent_funded
    
    def get_percent_funded(self):
        """Calculate funding percentage without using a property"""
        if self.funding_goal == 0:
            return 0
        return (self.amount_raised / self.funding_goal) * 100
    
    def get_absolute_url(self):
        return reverse('project_detail', kwargs={'project_id': self.id})

class InvestmentTerm(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='investment_terms')
    equity_offered = models.DecimalField(max_digits=5, decimal_places=2, help_text="Percentage of equity offered")
    minimum_investment = models.DecimalField(max_digits=10, decimal_places=2)
    maximum_investment = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, 
                                           help_text="Maximum investment amount allowed (optional)")
    valuation = models.DecimalField(max_digits=10, decimal_places=2, help_text="Project valuation in USD")
    deadline = models.DateTimeField()

    def __str__(self):
        return f"{self.equity_offered}% equity for ${self.minimum_investment}+"
    

class Investment(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='investments')
    investor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    equity_percentage = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    actual_return = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    terms = models.ForeignKey(InvestmentTerm, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    is_counted = models.BooleanField(default=False)

    def __str__(self):
        return f"${self.amount} investment in {self.project} by {self.investor}"
    
    def status_color(self):
        return {
            'pending': 'warning',
            'approved': 'success',
            'rejected': 'danger',
            'completed': 'primary',
        }.get(self.status, 'secondary')
    

    def save(self, *args, **kwargs):
        try:
            is_new = self.pk is None
            previous_status = None

            if not is_new:
                previous_status = Investment.objects.get(pk=self.pk).status

            # Auto-assign terms if not set
            if not self.terms and self.project:
                self.terms = self.project.investment_terms.first()

            with transaction.atomic():
                super().save(*args, **kwargs)

                # Update project's amount based on status
                if self.status == 'active' and previous_status != 'active':
                    Project.objects.filter(pk=self.project.pk).update(
                        amount_raised=F('amount_raised') + self.amount,
                        total_investment_raised=F('total_investment_raised') + self.amount
                    )
                elif previous_status == 'active' and self.status != 'active':
                    Project.objects.filter(pk=self.project.pk).update(
                        amount_raised=F('amount_raised') - self.amount,
                        total_investment_raised=F('total_investment_raised') - self.amount
                    )
        except Exception as e:
            raise ValidationError(f"Error saving investment: {str(e)}")


class RegistrationPayment(models.Model):
    """Model to track registration fee payments"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('successful', 'Successful'),
        ('failed', 'Failed'),
    ]
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='registration_payment')
    amount_usd = models.DecimalField(max_digits=10, decimal_places=2)
    amount_ngn = models.DecimalField(max_digits=10, decimal_places=2)
    paystack_reference = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Registration payment for {self.user.email} - ${self.amount_usd}"

    
class Reward(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='rewards')
    title = models.CharField(max_length=200)
    description = models.TextField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.title} (${self.amount})"

class Pledge(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='pledges')
    backer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reward = models.ForeignKey(Reward, on_delete=models.SET_NULL, null=True, blank=True)
    pledged_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.backer} pledged ${self.amount} to {self.project}"

class Update(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='updates')
    title = models.CharField(max_length=200)
    content = RichTextField()  # Changed from TextField to RichTextField
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


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


class IncubatorAcceleratorPage(models.Model):
    title = models.CharField(max_length=200)
    program_description = RichTextField()
    image = models.ImageField(upload_to='accelerator/', blank=True)
    application_info = RichTextField(help_text="Information about the call for applications, eligibility, timeline, etc.")
    application_deadline = models.DateTimeField(null=True, blank=True)
    is_accepting_applications = models.BooleanField(default=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name_plural = "Incubator/Accelerator Page Content"



class IncubatorApplication(models.Model):
    # Applicant & Project Basics
    project = models.CharField(max_length=200, default='' )
    applicant_name = models.CharField(max_length=200, default='' )
    applicant_email = models.EmailField(default='' )
    applicant_phone = models.CharField(max_length=20, blank=True, default='' )
    applicant_company = models.CharField(max_length=200, blank=True, default='' )

    # Startup Fundamentals
    website = models.URLField(blank=True, default='www.website.com' )
    stage = models.CharField(
        max_length=50,
        choices=[
            ('idea', 'Idea Stage'),
            ('mvp', 'Minimum Viable Product'),
            ('launched', 'Launched'),
            ('growing', 'Growing/Scaling')
        ],
        default='idea'
    )
    industry = models.CharField(max_length=100, default='', help_text="e.g. FinTech, AgriTech, HealthTech")

    # Descriptions & Key Content
    application_text = RichTextField(blank=True, default='', help_text="Describe your startup and what problem it solves")
    traction = RichTextField(blank=True, default='', help_text="Mention any traction, pilot users, revenue, etc.")
    team_background = RichTextField(blank=True, default='', help_text="Tell us about your team and why you're the right people to build this")
    goals_for_program = models.TextField(blank=True, default='', help_text="What do you hope to achieve during the accelerator?")
    funding_raised = models.CharField(max_length=100, blank=True, default='', help_text="e.g. $10,000 in grants, $5,000 from friends & family")
    funding_needed = models.CharField(max_length=100, blank=True, default='', help_text="How much are you looking to raise post-program?")

    # File Uploads (Optional)
    pitch_deck = models.FileField(upload_to='pitch_decks/', default='', blank=True, help_text="Upload your pitch deck (PDF, max 10MB)")

    # Admin & Meta
    application_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
            ('waitlisted', 'Waitlisted')
        ],
        default='pending'
    )
    reviewed = models.BooleanField(default=False)

    def __str__(self):
        return f"Application for {self.project} by {self.applicant_name}"



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
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order']


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

# Add this to your models.py file

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


