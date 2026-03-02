from django import forms
from django.core.validators import MinValueValidator
from decimal import Decimal

from .models import TokenWithdrawal, VentureTokenWithdrawal


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


class SRTProjectInvestmentForm(forms.Form):
    """Form for SRT partners to invest tokens in a project/venture"""
    amount = forms.DecimalField(
        min_value=Decimal('1'),
        max_digits=15,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Enter amount in SRT',
            'step': '0.01',
        })
    )

    def __init__(self, *args, project=None, account=None, **kwargs):
        self.project = project
        self.account = account
        super().__init__(*args, **kwargs)
        if project:
            self.fields['amount'].min_value = project.minimum_investment
            self.fields['amount'].widget.attrs['min'] = str(project.minimum_investment)
            self.fields['amount'].widget.attrs['placeholder'] = f"Min: {project.minimum_investment} SRT"
            if project.maximum_investment:
                self.fields['amount'].max_value = project.maximum_investment
                self.fields['amount'].widget.attrs['max'] = str(project.maximum_investment)

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount and self.project:
            can_invest, message = self.project.can_invest_srt(amount)
            if not can_invest:
                raise forms.ValidationError(message)
        if amount and self.account:
            if amount > self.account.available_tokens:
                raise forms.ValidationError(
                    f'Insufficient tokens. You have {self.account.available_tokens:.2f} SRT available.'
                )
        return amount


class VentureWithdrawalForm(forms.ModelForm):
    """Form for venture founders to withdraw raised SRT tokens"""

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
        model = VentureTokenWithdrawal
        fields = ['tokens', 'bank_name', 'account_number', 'account_name']

    def __init__(self, *args, project=None, **kwargs):
        self.project = project
        super().__init__(*args, **kwargs)

    def clean_tokens(self):
        tokens = self.cleaned_data.get('tokens')
        if tokens and tokens < Decimal('100'):
            raise forms.ValidationError('Minimum withdrawal is 100 SRT.')
        if tokens and self.project:
            available = VentureTokenWithdrawal.get_available_tokens(self.project)
            if tokens > available:
                raise forms.ValidationError(
                    f'Insufficient tokens. {available:.2f} SRT available for withdrawal.'
                )
        return tokens

    def clean_account_number(self):
        account_number = self.cleaned_data.get('account_number')
        if account_number:
            account_number = account_number.replace(' ', '').replace('-', '')
            if not account_number.isdigit():
                raise forms.ValidationError('Account number must contain only digits.')
            if len(account_number) != 10:
                raise forms.ValidationError('Account number must be exactly 10 digits.')
        return account_number
