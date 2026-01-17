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

class Pledge(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='pledges')
    backer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reward = models.ForeignKey('projects.Reward', on_delete=models.SET_NULL, null=True, blank=True) # Assuming Reward is in apps.projects
    pledged_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.backer} pledged ${self.amount} to {self.project}"