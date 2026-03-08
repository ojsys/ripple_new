from django.db import models
from django.db.models import Sum
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

    LISTING_TYPE_CHOICES = [
        ('project', 'Project (Donations)'),
        ('venture', 'Venture (Investments)'),
    ]

    FINANCING_TYPE_CHOICES = [
        ('equity', 'Equity Financing'),
        ('debt', 'Debt Financing'),
    ]

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

    # Listing Type
    listing_type = models.CharField(
        max_length=10,
        choices=LISTING_TYPE_CHOICES,
        default='project',
        help_text="Project for donations, Venture for investments"
    )

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

    # Venture-specific fields (only used when listing_type='venture')
    company_name = models.CharField(max_length=200, blank=True, null=True, help_text="Business or company name")
    financing_type = models.CharField(
        max_length=10,
        choices=[('equity', 'Equity Financing'), ('debt', 'Debt Financing')],
        blank=True,
        null=True,
        help_text="Type of investment financing"
    )
    equity_offered = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Percentage of equity offered to investors"
    )
    valuation = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Current company/venture valuation in USD"
    )
    interest_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Annual interest rate for debt financing (%)"
    )
    repayment_period_months = models.PositiveIntegerField(
        default=0,
        help_text="Repayment period in months (for debt financing)"
    )
    use_of_funds = models.TextField(
        blank=True,
        null=True,
        help_text="How the investment funds will be used"
    )

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

    @property
    def is_venture(self):
        """Check if this is a venture (investment) listing."""
        return self.listing_type == 'venture'

    @property
    def is_project(self):
        """Check if this is a project (donation) listing."""
        return self.listing_type == 'project'

    def get_calculated_percent(self):
        """Method to access the annotated value or fallback"""
        if hasattr(self, 'annotated_percent'):
            return self.annotated_percent
        return self.percent_funded

    @property
    def percent_funded(self):
        return self.get_percent_funded()

    def get_percent_funded(self):
        """Calculate funding percentage (fiat + SRT converted to USD)."""
        if self.funding_goal == 0:
            return 0
        total = self.get_total_raised()
        return min((total / self.funding_goal) * 100, Decimal('100'))

    def get_total_raised(self):
        """Total raised in USD: fiat donations + fiat investments + SRT tokens converted to USD."""
        if self.is_venture:
            return self.amount_raised + self.total_investment_raised + self.srt_raised_usd
        return self.amount_raised

    def recalculate_funding(self):
        """Recalculate amount_raised from all completed donations."""
        total = self.donations.filter(status='completed').aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')
        self.amount_raised = total
        self.save(update_fields=['amount_raised'])
        return total

    def get_backers_count(self):
        """Count unique backers for this project.
        - Logged-in users are counted uniquely by user ID
        - Anonymous donations (is_anonymous=True or no donor) each count as 1 backer
        """
        completed_donations = self.donations.filter(status='completed')

        # Count unique logged-in donors (non-anonymous with a user)
        unique_users = completed_donations.filter(
            donor__isnull=False,
            is_anonymous=False
        ).values('donor').distinct().count()

        # Count anonymous donations (each counts as a separate backer)
        anonymous_count = completed_donations.filter(
            models.Q(is_anonymous=True) | models.Q(donor__isnull=True)
        ).count()

        return unique_users + anonymous_count

    @property
    def backers_count(self):
        """Property to access backers count directly from templates."""
        return self.get_backers_count()

    def get_absolute_url(self):
        return reverse('project_detail', kwargs={'project_id': self.id})

    # SRT-related properties
    @property
    def srt_raised_usd(self):
        """SRT tokens raised converted to USD (1 SRT = ₦2,000 / ₦1,600 per USD = $1.25)"""
        return self.srt_amount_raised * Decimal('1.25')

    @property
    def srt_percent_of_goal(self):
        """SRT raised as a percentage of the USD funding goal, for progress bar display."""
        if self.funding_goal == 0 or self.srt_amount_raised == 0:
            return 0
        return min(float(self.srt_raised_usd / self.funding_goal * 100), 100)

    @property
    def fiat_percent_of_goal(self):
        """Fiat (USD + investments) raised as a percentage of goal, capped so fiat+SRT ≤ 100."""
        if self.funding_goal == 0:
            return 0
        fiat = float(self.get_percent_funded())
        srt = self.srt_percent_of_goal
        return min(fiat, max(0, 100 - srt))

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
            return False, "This venture is not approved for investment"
        if self.listing_type != 'venture':
            return False, "SRT investments are only available for ventures"
        if amount < self.minimum_investment:
            return False, f"Minimum investment is {self.minimum_investment} SRT"
        if self.maximum_investment and amount > self.maximum_investment:
            return False, f"Maximum investment is {self.maximum_investment} SRT"
        # Only check remaining cap if a funding goal is set
        if self.srt_funding_goal > 0 and amount > self.srt_remaining_amount:
            return False, f"Only {self.srt_remaining_amount} SRT remaining in this venture"
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


class PaymentAttempt(models.Model):
    """Track all payment attempts (pending, failed, abandoned).
    Successful payments are promoted to Donation records."""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('abandoned', 'Abandoned'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='payment_attempts')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='payment_attempts')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    amount_ngn = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    reward = models.ForeignKey(Reward, on_delete=models.SET_NULL, null=True, blank=True)
    message = models.TextField(blank=True, null=True)
    is_anonymous = models.BooleanField(default=False)
    paystack_reference = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    donation = models.OneToOneField(Donation, on_delete=models.SET_NULL, null=True, blank=True, related_name='payment_attempt',
                                     help_text="Linked donation (only set when payment succeeds)")
    error_message = models.TextField(blank=True, null=True, help_text="Error details if payment failed")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        user_name = self.user.get_full_name() if self.user else 'Unknown'
        return f"{user_name} - ${self.amount} - {self.status} ({self.paystack_reference})"

    class Meta:
        ordering = ['-created_at']


# Note: InvestmentTerm and Investment models are in apps.funding.models
# Use those for equity-based project investments
