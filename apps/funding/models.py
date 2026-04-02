from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.conf import settings
from django.db import transaction
from django.db.models import F, ExpressionWrapper, FloatField, Sum
from decimal import Decimal
import uuid

# Assuming Project model is in apps.projects
from apps.projects.models import Project

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
        ('pending_payment', 'Awaiting Payment'),
        ('pending_approval', 'Pending Founder Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('refund_requested', 'Refund Requested'),
        ('refunded', 'Refunded'),
        ('completed', 'Completed'),
        # legacy statuses kept for existing records
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('failed', 'Failed'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('unpaid', 'Unpaid'),
        ('paid', 'Paid'),
        ('refund_requested', 'Refund Requested'),
        ('refunded', 'Refunded'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='investments')
    investor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    amount_ngn = models.PositiveIntegerField(default=0, help_text="Amount in NGN kobo units (amount * 1600)")
    equity_percentage = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    actual_return = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    terms = models.ForeignKey(InvestmentTerm, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending_payment')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='unpaid')
    paystack_reference = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_counted = models.BooleanField(default=False)

    def __str__(self):
        return f"${self.amount} investment in {self.project} by {self.investor}"

    def status_color(self):
        return {
            'pending_payment': 'secondary',
            'pending_approval': 'warning',
            'approved': 'success',
            'rejected': 'danger',
            'refund_requested': 'info',
            'refunded': 'info',
            'completed': 'primary',
            'pending': 'warning',
            'active': 'success',
            'failed': 'danger',
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

            # pending_approval = payment confirmed by Paystack; approved = founder approved
            counting_statuses = ('pending_approval', 'active', 'approved')

            with transaction.atomic():
                super().save(*args, **kwargs)

                if self.status in counting_statuses and (previous_status not in counting_statuses):
                    Project.objects.filter(pk=self.project.pk).update(
                        total_investment_raised=F('total_investment_raised') + self.amount
                    )
                elif previous_status in counting_statuses and self.status not in counting_statuses:
                    Project.objects.filter(pk=self.project.pk).update(
                        total_investment_raised=F('total_investment_raised') - self.amount
                    )
        except Exception as e:
            raise ValidationError(f"Error saving investment: {str(e)}")


class InvestorEscrowBalance(models.Model):
    """Tracks pooled/escrowed fiat funds for an investor (from rejected investments)."""
    investor = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='escrow_balance'
    )
    balance_usd = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.investor} — ${self.balance_usd} pool"

    def credit(self, amount):
        from decimal import Decimal
        self.balance_usd += Decimal(str(amount))
        self.save()

    def debit(self, amount):
        from decimal import Decimal
        amount = Decimal(str(amount))
        if amount > self.balance_usd:
            raise ValueError("Insufficient pool balance")
        self.balance_usd -= amount
        self.save()

class FounderWithdrawalRequest(models.Model):
    """Tracks withdrawal requests by founders for their investment funds."""
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]

    NGN_RATE = Decimal('1600')  # USD to NGN conversion rate

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='founder_withdrawals',
        help_text="The venture project funds are being withdrawn from"
    )
    founder = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='founder_withdrawal_requests'
    )

    amount_usd = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Amount requested in USD"
    )
    amount_ngn = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Equivalent amount in NGN (amount_usd * rate)"
    )

    # Bank account details
    bank_name = models.CharField(max_length=200, help_text="Recipient bank name")
    account_number = models.CharField(max_length=20)
    account_name = models.CharField(max_length=200, help_text="Account holder name")

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reference = models.CharField(max_length=50, unique=True, blank=True)

    notes = models.TextField(blank=True, help_text="Optional notes from founder")
    admin_notes = models.TextField(blank=True, help_text="Admin review notes")
    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='processed_founder_withdrawals'
    )
    payment_reference = models.CharField(max_length=100, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Founder Withdrawal Request"
        verbose_name_plural = "Founder Withdrawal Requests"

    def __str__(self):
        return f"{self.founder.get_full_name()} — ${self.amount_usd} from {self.project.title} ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = f"FWR-{uuid.uuid4().hex[:10].upper()}"
        self.amount_ngn = self.amount_usd * self.NGN_RATE
        super().save(*args, **kwargs)

    @classmethod
    def get_available_amount(cls, project):
        """
        USD available for withdrawal after Paystack + admin fees across all transactions.
        = net_total_usd (from fees.summarise_project_fees) minus already-locked requests.
        """
        from apps.funding.fees import summarise_project_fees
        summary = summarise_project_fees(project)
        net_usd = summary['net_total_usd']
        locked = cls.objects.filter(
            project=project,
            status__in=['pending', 'approved', 'processing']
        ).aggregate(total=Sum('amount_usd'))['total'] or Decimal('0')
        return max(Decimal('0'), net_usd - locked)

    def approve(self, admin_user):
        if self.status != 'pending':
            return False
        self.status = 'approved'
        self.processed_by = admin_user
        self.processed_at = timezone.now()
        self.save()
        return True

    def reject(self, admin_user, notes=''):
        if self.status not in ('pending', 'approved'):
            return False
        self.status = 'rejected'
        self.processed_by = admin_user
        self.processed_at = timezone.now()
        if notes:
            self.admin_notes = notes
        self.save()
        return True

    def mark_completed(self, admin_user, payment_ref=''):
        if self.status not in ('approved', 'processing'):
            return False
        self.status = 'completed'
        self.processed_by = admin_user
        self.completed_at = timezone.now()
        if payment_ref:
            self.payment_reference = payment_ref
        self.save()
        return True

    def cancel(self):
        if self.status != 'pending':
            return False
        self.status = 'cancelled'
        self.save()
        return True


class Pledge(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='pledges')
    backer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reward = models.ForeignKey('projects.Reward', on_delete=models.SET_NULL, null=True, blank=True) # Assuming Reward is in apps.projects
    pledged_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.backer} pledged ${self.amount} to {self.project}"