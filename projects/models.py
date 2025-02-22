from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.utils import timezone
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.db.models import F, ExpressionWrapper, FloatField


class CustomUser(AbstractUser):
    USER_TYPES = (
        ('founder', 'Founder'),
        ('donor', 'Donor/Pledger'),
        ('investor', 'Investor'),
    )
    
    user_type = models.CharField(max_length=20, choices=USER_TYPES)
    phone_number = models.CharField(max_length=20)
    profile_completed = models.BooleanField(default=False)

    # Add these if missing
    username = models.CharField(max_length=30, unique=True)
    email = models.EmailField(unique=True)
    
    # Update the USERNAME_FIELD if needed
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return f"{self.get_full_name()} ({self.get_user_type_display()})"


class FounderProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    company_name = models.CharField(max_length=100)
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
    
    


class FundingType(models.Model):
    name = models.CharField(max_length=100)  # e.g., "Donation", "Equity", "Loan"
    description = models.TextField()

    def __str__(self):
        return self.name

class Project(models.Model):
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    funding_goal = models.DecimalField(max_digits=10, decimal_places=2)
    amount_raised = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_investment_raised = models.DecimalField(max_digits=10, decimal_places=2, default=0)  
    created_at = models.DateTimeField(default=timezone.now)
    deadline = models.DateTimeField()
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='project_images/')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    funding_type = models.ForeignKey(FundingType, on_delete=models.SET_NULL, null=True) 

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

class InvestmentTerm(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='investment_terms')
    equity_offered = models.DecimalField(max_digits=5, decimal_places=2, help_text="Percentage of equity offered")
    minimum_investment = models.DecimalField(max_digits=10, decimal_places=2)
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
    actual_return = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    terms = models.ForeignKey(InvestmentTerm, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"${self.amount} investment in {self.project} by {self.investor}"
    

    
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
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
    

class SiteSettings(models.Model):
    site_name = models.CharField(max_length=100, default='Ripples')
    logo = models.ImageField(upload_to='site/logo/', blank=True)
    favicon = models.ImageField(upload_to='site/favicon/', blank=True)
    primary_color = models.CharField(max_length=7, default='#28a745')
    secondary_color = models.CharField(max_length=7, default='#2c3e50')

    # Singleton implementation
    def save(self, *args, **kwargs):
        if not self.pk and SiteSettings.objects.exists():
            raise ValidationError("Only one SiteSettings instance can exist")
        self.pk = 1  # Force primary key to maintain singleton
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
    

