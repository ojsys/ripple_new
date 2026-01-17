from django.db import models
from django.utils import timezone
from django.urls import reverse
from django.conf import settings
from ckeditor.fields import RichTextField
from decimal import Decimal

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

    STAGE_CHOICES = [
        ('idea', 'Idea Stage'),
        ('seed', 'Seed Stage'),
        ('early', 'Early Stage'),
        ('growth', 'Growth Stage'),
        ('expansion', 'Expansion Stage'),
    ]

    RISK_CHOICES = [
        ('low', 'Low Risk'),
        ('moderate', 'Moderate Risk'),
        ('high', 'High Risk'),
    ]

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True, null=True)
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

    # SRT Investment Fields
    srt_enabled = models.BooleanField(default=False, help_text="Enable SRT token investments for this project")
    stage = models.CharField(max_length=20, choices=STAGE_CHOICES, default='idea', blank=True)
    risk_level = models.CharField(max_length=20, choices=RISK_CHOICES, default='moderate', blank=True)
    expected_return_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Expected annual return percentage for SRT investors"
    )
    investment_duration_months = models.PositiveIntegerField(
        default=12,
        help_text="Investment duration in months"
    )
    minimum_investment = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('10.00'),
        help_text="Minimum SRT tokens per investment"
    )
    maximum_investment = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Maximum SRT tokens per investment (optional)"
    )
    srt_amount_raised = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Total SRT tokens invested in this project"
    )
    srt_funding_goal = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="SRT token funding goal"
    )
    is_featured = models.BooleanField(default=False)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while Project.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

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

    # SRT-related properties
    @property
    def srt_percent_funded(self):
        """Calculate SRT funding percentage"""
        if self.srt_funding_goal > 0:
            return (self.srt_amount_raised / self.srt_funding_goal) * 100
        return 0

    @property
    def srt_remaining_amount(self):
        """Calculate remaining SRT funding amount"""
        return max(Decimal('0'), self.srt_funding_goal - self.srt_amount_raised)

    @property
    def srt_is_fully_funded(self):
        """Check if SRT funding goal is met"""
        return self.srt_amount_raised >= self.srt_funding_goal

    @property
    def srt_investor_count(self):
        """Count active SRT investors"""
        return self.srt_investments.filter(status='active').count()

    @property
    def days_remaining(self):
        """Calculate days until deadline"""
        if self.deadline:
            delta = self.deadline - timezone.now()
            return max(0, delta.days)
        return None

    @property
    def industry(self):
        """Return category name as industry for SRT compatibility"""
        return self.category.name if self.category else "General"

    def can_invest_srt(self, amount):
        """Check if an SRT investment amount is valid"""
        if self.status != 'approved':
            return False, "This project is not approved for investment"
        if not self.srt_enabled:
            return False, "SRT investments are not enabled for this project"
        if amount < self.minimum_investment:
            return False, f"Minimum investment is {self.minimum_investment} SRT"
        if self.maximum_investment and amount > self.maximum_investment:
            return False, f"Maximum investment is {self.maximum_investment} SRT"
        if amount > self.srt_remaining_amount:
            return False, f"Only {self.srt_remaining_amount} SRT remaining"
        return True, "OK"

class Reward(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='rewards')
    title = models.CharField(max_length=200)
    description = models.TextField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.title} (${self.amount})"

class Update(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='updates')
    title = models.CharField(max_length=200)
    content = RichTextField()  # Changed from TextField to RichTextField
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Donation(models.Model):
    """Track donations/pledges to projects."""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='donations')
    donor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='donations')
    donor_name = models.CharField(max_length=200, blank=True, null=True)
    donor_email = models.EmailField(blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    amount_ngn = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    reward = models.ForeignKey(Reward, on_delete=models.SET_NULL, null=True, blank=True)
    message = models.TextField(blank=True, null=True)
    is_anonymous = models.BooleanField(default=False)
    paystack_reference = models.CharField(max_length=100, unique=True, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        name = self.donor_name or (self.donor.get_full_name() if self.donor else 'Anonymous')
        return f"{name} donated ${self.amount} to {self.project.title}"

    class Meta:
        ordering = ['-created_at']


# Note: InvestmentTerm and Investment models are in apps.funding.models
# Use those for equity-based project investments
