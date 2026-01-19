from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid


class TokenPackage(models.Model):
    """Predefined SRT token purchase packages"""
    name = models.CharField(max_length=100)
    tokens = models.PositiveIntegerField(help_text="Number of SRT tokens in this package")
    price_ngn = models.DecimalField(max_digits=12, decimal_places=2, help_text="Price in NGN")
    price_usd = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price in USD")
    bonus_tokens = models.PositiveIntegerField(default=0, help_text="Bonus tokens included")
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0, help_text="Display order")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'price_ngn']
        verbose_name = "Token Package"
        verbose_name_plural = "Token Packages"

    def __str__(self):
        return f"{self.name} - {self.tokens} SRT (₦{self.price_ngn:,.2f})"

    @property
    def total_tokens(self):
        return self.tokens + self.bonus_tokens

    @property
    def price_per_token(self):
        if self.total_tokens > 0:
            return self.price_ngn / self.total_tokens
        return Decimal('0')


class PartnerCapitalAccount(models.Model):
    """Partner's SRT token account - holds their token balance and investment tracking"""
    partner = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='capital_account'
    )
    token_balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    total_tokens_purchased = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00')
    )
    total_tokens_invested = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00')
    )
    total_tokens_earned = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Tokens earned from returns, bonuses, referrals"
    )
    total_investment_value_ngn = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Total NGN value of all investments"
    )
    locked_tokens = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Tokens locked in active investments"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Partner Capital Account"
        verbose_name_plural = "Partner Capital Accounts"

    def __str__(self):
        return f"{self.partner.get_full_name()} - {self.token_balance} SRT"

    @property
    def available_tokens(self):
        """Tokens available for investment (not locked)"""
        return self.token_balance - self.locked_tokens

    def add_tokens(self, amount, transaction_type='purchase', reference=None, description=''):
        """Add tokens to the account and create a transaction record"""
        amount = Decimal(str(amount))
        self.token_balance += amount

        if transaction_type == 'purchase':
            self.total_tokens_purchased += amount
        elif transaction_type in ['return', 'bonus', 'referral']:
            self.total_tokens_earned += amount

        self.save()

        # Create transaction record
        SRTTransaction.objects.create(
            account=self,
            transaction_type=transaction_type,
            amount=amount,
            balance_after=self.token_balance,
            reference=reference or str(uuid.uuid4())[:12].upper(),
            description=description
        )
        return True

    def invest_tokens(self, amount, venture=None, project=None, description=''):
        """Invest tokens in a venture or project"""
        amount = Decimal(str(amount))
        if amount > self.available_tokens:
            raise ValueError("Insufficient available tokens")

        target = project or venture
        if not target:
            raise ValueError("Must specify either a project or venture")

        self.locked_tokens += amount
        self.total_tokens_invested += amount
        self.save()

        # Create transaction record
        SRTTransaction.objects.create(
            account=self,
            transaction_type='investment',
            amount=-amount,
            balance_after=self.token_balance,
            venture=venture,
            project=project,
            reference=str(uuid.uuid4())[:12].upper(),
            description=description or f"Investment in {target.title}"
        )
        return True

    def release_tokens(self, amount, venture=None, project=None, is_return=False, description=''):
        """Release locked tokens (from completed/cancelled investment)"""
        amount = Decimal(str(amount))
        self.locked_tokens -= amount

        if is_return:
            self.token_balance += amount
            self.total_tokens_earned += amount

        self.save()

        if is_return:
            SRTTransaction.objects.create(
                account=self,
                transaction_type='return',
                amount=amount,
                balance_after=self.token_balance,
                venture=venture,
                project=project,
                reference=str(uuid.uuid4())[:12].upper(),
                description=description or "Investment return"
            )
        return True

    def withdraw_tokens(self, amount, reference=None, description=''):
        """Withdraw tokens from the account (converts to NGN)"""
        amount = Decimal(str(amount))
        if amount > self.available_tokens:
            raise ValueError("Insufficient available tokens for withdrawal")

        self.token_balance -= amount
        self.save()

        # Create withdrawal transaction record
        SRTTransaction.objects.create(
            account=self,
            transaction_type='withdrawal',
            amount=-amount,
            balance_after=self.token_balance,
            reference=reference or str(uuid.uuid4())[:12].upper(),
            description=description or "Token withdrawal"
        )
        return True


class Venture(models.Model):
    """Investment opportunities available to SRT partners"""
    STAGE_CHOICES = [
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

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('open', 'Open for Investment'),
        ('funded', 'Fully Funded'),
        ('closed', 'Closed'),
        ('completed', 'Completed'),
    ]

    # Basic Info
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    short_description = models.CharField(max_length=300, blank=True)
    image = models.ImageField(upload_to='ventures/', blank=True, null=True)

    # Funding Details
    funding_goal = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Funding goal in SRT tokens"
    )
    minimum_investment = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('100.00'),
        help_text="Minimum SRT tokens per investment"
    )
    maximum_investment = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Maximum SRT tokens per investment (optional)"
    )
    amount_raised = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00')
    )

    # Investment Terms
    expected_return_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Expected annual return percentage"
    )
    investment_duration_months = models.PositiveIntegerField(
        help_text="Investment duration in months"
    )

    # Classification
    stage = models.CharField(max_length=20, choices=STAGE_CHOICES, default='seed')
    risk_level = models.CharField(max_length=20, choices=RISK_CHOICES, default='moderate')
    industry = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')

    # Dates
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Relations
    founder = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ventures_created',
        null=True,
        blank=True
    )

    # Featured
    is_featured = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-is_featured', 'order', '-created_at']
        verbose_name = "Venture"
        verbose_name_plural = "Ventures"

    def __str__(self):
        return self.title

    @property
    def percent_funded(self):
        if self.funding_goal > 0:
            return (self.amount_raised / self.funding_goal) * 100
        return 0

    @property
    def remaining_amount(self):
        return self.funding_goal - self.amount_raised

    @property
    def is_fully_funded(self):
        return self.amount_raised >= self.funding_goal

    @property
    def investor_count(self):
        return self.investments.filter(status='active').count()

    @property
    def days_remaining(self):
        if self.end_date:
            delta = self.end_date - timezone.now().date()
            return max(0, delta.days)
        return None

    def can_invest(self, amount):
        """Check if an investment amount is valid"""
        if self.status != 'open':
            return False, "This venture is not open for investment"
        if amount < self.minimum_investment:
            return False, f"Minimum investment is {self.minimum_investment} SRT"
        if self.maximum_investment and amount > self.maximum_investment:
            return False, f"Maximum investment is {self.maximum_investment} SRT"
        if amount > self.remaining_amount:
            return False, f"Only {self.remaining_amount} SRT remaining"
        return True, "OK"


class VentureInvestment(models.Model):
    """Individual partner investments in projects/ventures"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('matured', 'Matured'),
        ('withdrawn', 'Withdrawn'),
        ('cancelled', 'Cancelled'),
    ]

    partner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='venture_investments'
    )
    # Keep venture for backward compatibility, but use project going forward
    venture = models.ForeignKey(
        Venture,
        on_delete=models.CASCADE,
        related_name='investments',
        null=True,
        blank=True
    )
    # New: Link to Project model
    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.CASCADE,
        related_name='srt_investments',
        null=True,
        blank=True
    )
    account = models.ForeignKey(
        PartnerCapitalAccount,
        on_delete=models.CASCADE,
        related_name='investments'
    )

    tokens_invested = models.DecimalField(max_digits=15, decimal_places=2)
    expected_return = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Expected return in SRT tokens"
    )
    actual_return = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    investment_date = models.DateTimeField(auto_now_add=True)
    maturity_date = models.DateField(null=True, blank=True)

    reference = models.CharField(max_length=50, unique=True)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Venture Investment"
        verbose_name_plural = "Venture Investments"

    def __str__(self):
        target = self.project or self.venture
        title = target.title if target else "Unknown"
        return f"{self.partner.get_full_name()} - {title} ({self.tokens_invested} SRT)"

    @property
    def investment_target(self):
        """Return either project or venture, whichever is set"""
        return self.project or self.venture

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = f"INV-{uuid.uuid4().hex[:10].upper()}"

        target = self.project or self.venture
        if target:
            if not self.maturity_date and target.investment_duration_months:
                from dateutil.relativedelta import relativedelta
                self.maturity_date = timezone.now().date() + relativedelta(months=target.investment_duration_months)
            if not self.expected_return:
                # Calculate expected return based on target's return rate
                rate = target.expected_return_rate / 100
                duration_years = target.investment_duration_months / 12
                self.expected_return = self.tokens_invested * (1 + rate * duration_years)
        super().save(*args, **kwargs)

    @property
    def return_rate(self):
        if self.tokens_invested > 0 and self.actual_return:
            return ((self.actual_return - self.tokens_invested) / self.tokens_invested) * 100
        return None

    @property
    def days_to_maturity(self):
        if self.maturity_date:
            delta = self.maturity_date - timezone.now().date()
            return max(0, delta.days)
        return None


class SRTTransaction(models.Model):
    """Transaction history for all SRT token movements"""
    TRANSACTION_TYPES = [
        ('purchase', 'Token Purchase'),
        ('investment', 'Investment'),
        ('return', 'Investment Return'),
        ('bonus', 'Bonus'),
        ('referral', 'Referral Reward'),
        ('withdrawal', 'Withdrawal'),
        ('adjustment', 'Manual Adjustment'),
    ]

    account = models.ForeignKey(
        PartnerCapitalAccount,
        on_delete=models.CASCADE,
        related_name='transactions'
    )
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    balance_after = models.DecimalField(max_digits=15, decimal_places=2)

    # Optional relations
    venture = models.ForeignKey(
        Venture,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions'
    )
    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='srt_transactions'
    )
    token_package = models.ForeignKey(
        TokenPackage,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    reference = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)

    # Payment tracking (for purchases)
    payment_reference = models.CharField(max_length=100, blank=True, null=True)
    payment_method = models.CharField(max_length=50, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "SRT Transaction"
        verbose_name_plural = "SRT Transactions"

    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.amount} SRT ({self.reference})"

    def save(self, *args, **kwargs):
        if not self.reference:
            prefix = self.transaction_type[:3].upper()
            self.reference = f"{prefix}-{uuid.uuid4().hex[:10].upper()}"
        super().save(*args, **kwargs)


class TokenPurchase(models.Model):
    """Track token purchase transactions"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('successful', 'Successful'),
        ('failed', 'Failed'),
    ]

    partner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='token_purchases'
    )
    account = models.ForeignKey(
        PartnerCapitalAccount,
        on_delete=models.CASCADE,
        related_name='purchases'
    )
    package = models.ForeignKey(
        TokenPackage,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    tokens = models.DecimalField(max_digits=15, decimal_places=2)
    bonus_tokens = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    amount_ngn = models.DecimalField(max_digits=12, decimal_places=2)
    amount_usd = models.DecimalField(max_digits=10, decimal_places=2)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    paystack_reference = models.CharField(max_length=100, unique=True)

    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Token Purchase"
        verbose_name_plural = "Token Purchases"

    def __str__(self):
        return f"{self.partner.get_full_name()} - {self.tokens} SRT"

    @property
    def total_tokens(self):
        return self.tokens + self.bonus_tokens

    def complete_purchase(self):
        """Mark purchase as successful and credit tokens to account"""
        if self.status == 'successful':
            return False

        self.status = 'successful'
        self.completed_at = timezone.now()
        self.save()

        # Add tokens to account
        self.account.add_tokens(
            amount=self.total_tokens,
            transaction_type='purchase',
            reference=self.paystack_reference,
            description=f"Token purchase - {self.package.name if self.package else 'Custom'}"
        )
        return True


class TokenWithdrawal(models.Model):
    """Track token withdrawal requests"""
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]

    # Commercial Banks
    COMMERCIAL_BANKS = [
        ('access', 'Access Bank'),
        ('citibank', 'Citibank Nigeria'),
        ('ecobank', 'Ecobank Nigeria'),
        ('fidelity', 'Fidelity Bank'),
        ('first', 'First Bank of Nigeria'),
        ('fcmb', 'First City Monument Bank (FCMB)'),
        ('globus', 'Globus Bank'),
        ('gtbank', 'Guaranty Trust Bank (GTBank)'),
        ('heritage', 'Heritage Bank'),
        ('keystone', 'Keystone Bank'),
        ('optimus', 'Optimus Bank'),
        ('polaris', 'Polaris Bank'),
        ('providus', 'Providus Bank'),
        ('stanbic', 'Stanbic IBTC Bank'),
        ('standard_chartered', 'Standard Chartered Bank'),
        ('sterling', 'Sterling Bank'),
        ('suntrust', 'SunTrust Bank'),
        ('titan', 'Titan Trust Bank'),
        ('union', 'Union Bank of Nigeria'),
        ('uba', 'United Bank for Africa (UBA)'),
        ('unity', 'Unity Bank'),
        ('wema', 'Wema Bank'),
        ('zenith', 'Zenith Bank'),
    ]

    # Non-Interest (Islamic) Banks
    NON_INTEREST_BANKS = [
        ('jaiz', 'Jaiz Bank'),
        ('taj', 'TAJ Bank'),
        ('lotus', 'Lotus Bank'),
    ]

    # Payment Service Banks (PSBs)
    PAYMENT_SERVICE_BANKS = [
        ('9psb', '9 Payment Service Bank (9PSB)'),
        ('hope_psb', 'Hope PSB'),
        ('kuda', 'Kuda Bank'),
        ('money_master', 'Money Master PSB'),
        ('moniepoint', 'Moniepoint MFB'),
        ('opay', 'OPay Digital Services'),
        ('palmpay', 'PalmPay'),
        ('paga', 'Paga'),
    ]

    # Microfinance Banks (MFBs)
    MICROFINANCE_BANKS = [
        ('ab_mfb', 'AB Microfinance Bank'),
        ('accion_mfb', 'Accion Microfinance Bank'),
        ('addosser_mfb', 'ADDOSSER Microfinance Bank'),
        ('aella_mfb', 'Aella Microfinance Bank'),
        ('alat_mfb', 'ALAT by Wema'),
        ('balogun_gambari_mfb', 'Balogun Gambari Microfinance Bank'),
        ('bowen_mfb', 'Bowen Microfinance Bank'),
        ('branch_mfb', 'Branch International'),
        ('brightway_mfb', 'Brightway Microfinance Bank'),
        ('carbon', 'Carbon (Paylater)'),
        ('cellulant_mfb', 'Cellulant'),
        ('chipper_cash', 'Chipper Cash'),
        ('corestep_mfb', 'Corestep Microfinance Bank'),
        ('covenant_mfb', 'Covenant Microfinance Bank'),
        ('eyowo', 'Eyowo'),
        ('fairmoney', 'FairMoney Microfinance Bank'),
        ('fbn_quest_mfb', 'FBNQuest Microfinance Bank'),
        ('finca_mfb', 'FINCA Microfinance Bank'),
        ('firmus_mfb', 'Firmus Microfinance Bank'),
        ('first_royal_mfb', 'First Royal Microfinance Bank'),
        ('flutterwave', 'Flutterwave'),
        ('fsdh_mfb', 'FSDH Merchant Bank'),
        ('gomoney', 'GoMoney'),
        ('grassroots_mfb', 'Grassroots Microfinance Bank'),
        ('grooming_mfb', 'Grooming Microfinance Bank'),
        ('hackman_mfb', 'Hackman Microfinance Bank'),
        ('hasal_mfb', 'Hasal Microfinance Bank'),
        ('ibile_mfb', 'IBILE Microfinance Bank'),
        ('infinity_mfb', 'Infinity Microfinance Bank'),
        ('kredi_mfb', 'Kredi Microfinance Bank'),
        ('lapo_mfb', 'LAPO Microfinance Bank'),
        ('mainstreet_mfb', 'Mainstreet Microfinance Bank'),
        ('mint_mfb', 'Mint Finex MFB'),
        ('mutual_trust_mfb', 'Mutual Trust Microfinance Bank'),
        ('navy_mfb', 'Navy Microfinance Bank'),
        ('npf_mfb', 'NPF Microfinance Bank'),
        ('parallex_mfb', 'Parallex Bank'),
        ('peace_mfb', 'Peace Microfinance Bank'),
        ('petra_mfb', 'Petra Microfinance Bank'),
        ('piggyvest', 'PiggyVest'),
        ('quickteller', 'Quickteller (Interswitch)'),
        ('rand_mfb', 'Rand Merchant Bank'),
        ('regent_mfb', 'Regent Microfinance Bank'),
        ('renmoney', 'Renmoney Microfinance Bank'),
        ('rubies_mfb', 'Rubies Microfinance Bank'),
        ('safe_haven_mfb', 'Safe Haven Microfinance Bank'),
        ('sparkle_mfb', 'Sparkle Microfinance Bank'),
        ('tcf_mfb', 'TCF Microfinance Bank'),
        ('trident_mfb', 'Trident Microfinance Bank'),
        ('unical_mfb', 'Unical Microfinance Bank'),
        ('unilag_mfb', 'Unilag Microfinance Bank'),
        ('vfd_mfb', 'VFD Microfinance Bank'),
        ('zedvance_mfb', 'Zedvance'),
    ]

    # Flat list of all bank choices for model validation
    ALL_BANK_CHOICES = (
        COMMERCIAL_BANKS +
        NON_INTEREST_BANKS +
        PAYMENT_SERVICE_BANKS +
        MICROFINANCE_BANKS +
        [('other', 'Other (Please specify in notes)')]
    )

    # Grouped choices for forms (with optgroups)
    BANK_CHOICES_GROUPED = [
        ('Commercial Banks', COMMERCIAL_BANKS),
        ('Non-Interest (Islamic) Banks', NON_INTEREST_BANKS),
        ('Payment Service Banks (PSBs)', PAYMENT_SERVICE_BANKS),
        ('Microfinance Banks', MICROFINANCE_BANKS),
        ('Other', [('other', 'Other (Please specify in notes)')]),
    ]

    # Combined flat choices for the model field
    BANK_CHOICES = ALL_BANK_CHOICES

    partner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='token_withdrawals'
    )
    account = models.ForeignKey(
        PartnerCapitalAccount,
        on_delete=models.CASCADE,
        related_name='withdrawals'
    )

    tokens = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('100.00'))],
        help_text="Minimum withdrawal: 100 SRT"
    )
    amount_ngn = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Amount in NGN to be paid"
    )
    fee = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Withdrawal fee in NGN"
    )

    # Bank details
    bank_name = models.CharField(max_length=50, choices=BANK_CHOICES)
    account_number = models.CharField(max_length=20)
    account_name = models.CharField(max_length=200)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reference = models.CharField(max_length=50, unique=True)

    # Processing details
    admin_notes = models.TextField(blank=True)
    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='processed_withdrawals'
    )
    payment_reference = models.CharField(max_length=100, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Token Withdrawal"
        verbose_name_plural = "Token Withdrawals"

    def __str__(self):
        return f"{self.partner.get_full_name()} - {self.tokens} SRT ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = f"WDR-{uuid.uuid4().hex[:10].upper()}"

        # Calculate gross amount, fee, and net amount
        srt_to_ngn_rate = Decimal('2000')
        fee_percentage = Decimal('0.04')

        gross_amount = self.tokens * srt_to_ngn_rate
        calculated_fee = gross_amount * fee_percentage

        self.fee = calculated_fee
        self.amount_ngn = gross_amount - calculated_fee
        
        super().save(*args, **kwargs)

    def approve(self, admin_user):
        """Approve the withdrawal request"""
        if self.status != 'pending':
            return False

        self.status = 'approved'
        self.processed_by = admin_user
        self.processed_at = timezone.now()
        self.save()

        # Deduct tokens from account
        self.account.withdraw_tokens(
            amount=self.tokens,
            reference=self.reference,
            description=f"Withdrawal to {self.get_bank_name_display()} - {self.account_number}"
        )
        return True

    def complete(self, payment_ref=None):
        """Mark withdrawal as completed"""
        if self.status not in ['approved', 'processing']:
            return False

        self.status = 'completed'
        self.completed_at = timezone.now()
        if payment_ref:
            self.payment_reference = payment_ref
        self.save()
        return True

    def reject(self, admin_user, reason=''):
        """Reject the withdrawal request"""
        if self.status != 'pending':
            return False

        self.status = 'rejected'
        self.processed_by = admin_user
        self.processed_at = timezone.now()
        self.admin_notes = reason
        self.save()
        return True

    def cancel(self):
        """Cancel the withdrawal request (by user)"""
        if self.status != 'pending':
            return False

        self.status = 'cancelled'
        self.save()
        return True
