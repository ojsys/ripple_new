from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.conf import settings
from django.db import transaction
from django.db.models import F, ExpressionWrapper, FloatField

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

class Pledge(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='pledges')
    backer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reward = models.ForeignKey('projects.Reward', on_delete=models.SET_NULL, null=True, blank=True) # Assuming Reward is in apps.projects
    pledged_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.backer} pledged ${self.amount} to {self.project}"