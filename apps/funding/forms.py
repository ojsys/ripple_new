from django import forms
from decimal import Decimal
from .models import FounderWithdrawalRequest

NIGERIAN_BANKS = [
    ('', '— Select Bank —'),
    ('044', 'Access Bank'),
    ('063', 'Access Bank (Diamond)'),
    ('035A', 'ALAT by Wema'),
    ('401', 'ASO Savings and Loans'),
    ('023', 'Citibank Nigeria'),
    ('050', 'Ecobank Nigeria'),
    ('562', 'Ekondo Microfinance Bank'),
    ('070', 'Fidelity Bank'),
    ('011', 'First Bank of Nigeria'),
    ('214', 'First City Monument Bank'),
    ('058', 'Guaranty Trust Bank'),
    ('030', 'Heritage Bank'),
    ('301', 'Jaiz Bank'),
    ('082', 'Keystone Bank'),
    ('50211', 'Kuda Bank'),
    ('503', 'Moniepoint MFB'),
    ('526', 'Paycom (OPay)'),
    ('999992', 'PalmPay'),
    ('076', 'Polaris Bank'),
    ('101', 'Providus Bank'),
    ('125', 'Rubies MFB'),
    ('221', 'Stanbic IBTC Bank'),
    ('068', 'Standard Chartered'),
    ('232', 'Sterling Bank'),
    ('100', 'Suntrust Bank'),
    ('302', 'TAJ Bank'),
    ('032', 'Union Bank of Nigeria'),
    ('033', 'United Bank for Africa'),
    ('215', 'Unity Bank'),
    ('035', 'Wema Bank'),
    ('057', 'Zenith Bank'),
]


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

    bank_name = forms.ChoiceField(
        choices=NIGERIAN_BANKS,
        widget=forms.Select(attrs={'class': 'form-select form-select-lg'}),
    )

    bank_code = forms.CharField(
        widget=forms.HiddenInput(),
        required=False,
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
        fields = ['amount_usd', 'bank_name', 'bank_code', 'account_number', 'account_name', 'notes']

    def __init__(self, *args, project=None, **kwargs):
        self.project = project
        super().__init__(*args, **kwargs)

    def clean_bank_name(self):
        # The choice value IS the bank code; store name for display
        code = self.cleaned_data.get('bank_name')
        if not code:
            raise forms.ValidationError('Please select your bank.')
        # Find display name
        name = dict(NIGERIAN_BANKS).get(code, code)
        # Stash the code so clean_bank_code can pick it up
        self._selected_bank_code = code
        return name  # store human-readable name

    def clean_bank_code(self):
        return getattr(self, '_selected_bank_code', self.cleaned_data.get('bank_code', ''))

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
