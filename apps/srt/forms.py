from django import forms
from django.core.validators import MinValueValidator
from decimal import Decimal

from .models import TokenWithdrawal


class WithdrawalForm(forms.ModelForm):
    """Form for requesting token withdrawal"""

    tokens = forms.DecimalField(
        min_value=Decimal('100.00'),
        max_digits=15,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Enter amount in SRT',
            'step': '0.01',
            'min': '100',
        }),
        help_text='Minimum withdrawal: 100 SRT'
    )

    bank_name = forms.ChoiceField(
        choices=[('', 'Select Your Bank')] + TokenWithdrawal.BANK_CHOICES_GROUPED,
        widget=forms.Select(attrs={
            'class': 'form-select form-select-lg',
        })
    )

    account_number = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Enter 10-digit account number',
            'pattern': '[0-9]{10}',
            'maxlength': '10',
        })
    )

    account_name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Account holder name',
        })
    )

    class Meta:
        model = TokenWithdrawal
        fields = ['tokens', 'bank_name', 'account_number', 'account_name']

    def __init__(self, *args, account=None, **kwargs):
        self.account = account
        super().__init__(*args, **kwargs)

    def clean_tokens(self):
        tokens = self.cleaned_data.get('tokens')
        if tokens and self.account:
            if tokens > self.account.available_tokens:
                raise forms.ValidationError(
                    f'Insufficient tokens. You have {self.account.available_tokens:.2f} SRT available.'
                )
        if tokens and tokens < Decimal('100'):
            raise forms.ValidationError('Minimum withdrawal is 100 SRT.')
        return tokens

    def clean_account_number(self):
        account_number = self.cleaned_data.get('account_number')
        if account_number:
            # Remove any spaces or dashes
            account_number = account_number.replace(' ', '').replace('-', '')
            if not account_number.isdigit():
                raise forms.ValidationError('Account number must contain only digits.')
            if len(account_number) != 10:
                raise forms.ValidationError('Account number must be exactly 10 digits.')
        return account_number


class InvestmentModifyForm(forms.Form):
    """Form for modifying an existing investment (early withdrawal)"""

    REASON_CHOICES = [
        ('', 'Select a reason'),
        ('financial_emergency', 'Financial Emergency'),
        ('better_opportunity', 'Found Better Opportunity'),
        ('risk_concern', 'Concerned About Risk'),
        ('personal', 'Personal Reasons'),
        ('other', 'Other'),
    ]

    action = forms.ChoiceField(
        choices=[
            ('partial_withdraw', 'Partial Withdrawal'),
            ('full_withdraw', 'Full Withdrawal'),
        ],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )

    amount = forms.DecimalField(
        required=False,
        min_value=Decimal('0.01'),
        max_digits=15,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Amount to withdraw',
            'step': '0.01',
        })
    )

    reason = forms.ChoiceField(
        choices=REASON_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    additional_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Any additional information...',
        })
    )

    confirm = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='I understand there may be penalties for early withdrawal'
    )

    def __init__(self, *args, investment=None, **kwargs):
        self.investment = investment
        super().__init__(*args, **kwargs)

    def clean_amount(self):
        action = self.cleaned_data.get('action')
        amount = self.cleaned_data.get('amount')

        if action == 'partial_withdraw':
            if not amount:
                raise forms.ValidationError('Please specify the amount to withdraw.')
            if self.investment and amount >= self.investment.tokens_invested:
                raise forms.ValidationError(
                    'For partial withdrawal, amount must be less than total invested. '
                    'Use full withdrawal instead.'
                )
        return amount
