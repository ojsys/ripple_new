from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

class CustomUser(AbstractUser):
    USER_TYPES = (
        ('', 'Select User Type'),
        ('founder', 'Founder'),
        ('donor', 'Donor/Pledger'),
        ('investor', 'Investor'),
        ('partner', 'SRT Partner'),
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

    # SRT Partner capability - allows any user type to also be an SRT partner
    is_srt_partner = models.BooleanField(default=False, help_text="User has SRT Partner capabilities")
    srt_partner_since = models.DateTimeField(null=True, blank=True, help_text="Date when user became an SRT partner")

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

class PartnerProfile(models.Model):
    """Extended profile for SRT Partners"""
    ACCREDITATION_CHOICES = [
        ('pending', 'Pending Verification'),
        ('verified', 'Verified'),
        ('suspended', 'Suspended'),
    ]

    RISK_PROFILE_CHOICES = [
        ('conservative', 'Conservative'),
        ('moderate', 'Moderate'),
        ('aggressive', 'Aggressive'),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='partner_profile')
    partner_id = models.CharField(max_length=20, unique=True, help_text="Unique partner ID (SRT-XXXX format)")
    accreditation_status = models.CharField(max_length=20, choices=ACCREDITATION_CHOICES, default='pending')
    kyc_completed = models.BooleanField(default=False)
    risk_profile = models.CharField(max_length=20, choices=RISK_PROFILE_CHOICES, default='moderate')
    monthly_investment_limit = models.DecimalField(max_digits=12, decimal_places=2, default=400000,
                                                   help_text="Maximum monthly investment in NGN")
    bio = models.TextField(blank=True, null=True)
    company_name = models.CharField(max_length=200, blank=True, null=True)
    occupation = models.CharField(max_length=100, blank=True, null=True)
    image = models.ImageField(upload_to='partner_images/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.partner_id})"

    class Meta:
        verbose_name = "Partner Profile"
        verbose_name_plural = "Partner Profiles"

class PartnerCapitalAccount(models.Model):
    """Capital account for SRT Partners to manage their investments."""
    partner = models.OneToOneField(PartnerProfile, on_delete=models.CASCADE, related_name='capital_account')
    balance = models.DecimalField(max_digits=18, decimal_places=2, default=0.00,
                                  help_text="Current balance of the partner's capital account in NGN")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Capital Account for {self.partner.user.get_full_name()}"

    def deposit(self, amount):
        if amount > 0:
            self.balance += amount
            self.save()
            return True
        return False

    def withdraw(self, amount):
        if amount > 0 and self.balance >= amount:
            self.balance -= amount
            self.save()
            return True
        return False

    class Meta:
        verbose_name = "Partner Capital Account"
        verbose_name_plural = "Partner Capital Accounts"

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


class PendingRegistration(models.Model):
    """Model to store registration data temporarily before payment confirmation"""
    # User data
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20)
    user_type = models.CharField(max_length=20, choices=CustomUser.USER_TYPES)
    password_hash = models.CharField(max_length=128)  # Store hashed password
    
    # Payment tracking
    paystack_reference = models.CharField(max_length=100, unique=True)
    amount_usd = models.DecimalField(max_digits=10, decimal_places=2)
    amount_ngn = models.DecimalField(max_digits=10, decimal_places=2)
    payment_status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('successful', 'Successful'),
        ('failed', 'Failed'),
    ], default='pending')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()  # Registration expires after 24 hours
    
    def __str__(self):
        return f"Pending registration for {self.email} - {self.get_user_type_display()}"
    
    def is_expired(self):
        from django.utils import timezone
        return timezone.now() > self.expires_at
    
    def get_registration_fee(self):
        """Get the registration fee amount based on user type"""
        if self.user_type == 'founder':
            return 5.00  # $5 USD
        elif self.user_type in ['donor', 'investor']:
            return 25.00  # $25 USD
        return 0.00
    
    def get_registration_fee_ngn(self):
        """Get the registration fee in NGN"""
        usd_amount = self.get_registration_fee()
        return int(usd_amount * 1600)  # 1 USD = 1600 NGN