from django import forms
from decimal import Decimal
from .models import FounderWithdrawalRequest


class FounderWithdrawalForm(forms.ModelForm):
    amount_usd = forms.DecimalField(
        min_value=Decimal('10.00'),
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Enter amount in USD',
            'step': '0.01',
            'min': '10',
        }),
        help_text='Minimum withdrawal: $10.00'
    )

    bank_name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'e.g. Zenith Bank, GTBank',
        })
    )

    account_number = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': '10-digit account number',
            'maxlength': '10',
        })
    )

    account_name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Account holder full name',
        })
    )

    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Optional: any additional notes for the admin',
        })
    )

    class Meta:
        model = FounderWithdrawalRequest
        fields = ['amount_usd', 'bank_name', 'account_number', 'account_name', 'notes']

    def __init__(self, *args, project=None, **kwargs):
        self.project = project
        super().__init__(*args, **kwargs)

    def clean_amount_usd(self):
        amount = self.cleaned_data.get('amount_usd')
        if amount and amount < Decimal('10'):
            raise forms.ValidationError('Minimum withdrawal is $10.00.')
        if amount and self.project:
            available = FounderWithdrawalRequest.get_available_amount(self.project)
            if amount > available:
                raise forms.ValidationError(
                    f'Insufficient funds. ${available:,.2f} available for withdrawal.'
                )
        return amount

    def clean_account_number(self):
        account_number = self.cleaned_data.get('account_number')
        if account_number:
            account_number = account_number.replace(' ', '').replace('-', '')
            if not account_number.isdigit():
                raise forms.ValidationError('Account number must contain only digits.')
            if len(account_number) != 10:
                raise forms.ValidationError('Account number must be exactly 10 digits.')
        return account_number
