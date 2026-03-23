from django import forms
from django.forms import inlineformset_factory
from ckeditor.widgets import CKEditorWidget
from .models import Project, Reward, Update, Donation
from apps.funding.models import Investment, InvestmentTerm


class ProjectForm(forms.ModelForm):
    """Form for creating and editing projects."""

    description = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 10,
            'id': 'description-editor'
        }),
        required=True
    )

    class Meta:
        model = Project
        fields = [
            'listing_type', 'title', 'short_description', 'description', 'category',
            'funding_type', 'funding_goal', 'deadline', 'image', 'location', 'video_url',
            # Venture-specific fields
            'company_name', 'financing_type', 'equity_offered', 'valuation',
            'interest_rate', 'repayment_period_months', 'use_of_funds',
            # SRT investment fields
            'srt_enabled', 'srt_funding_goal', 'expected_return_rate',
            'investment_duration_months', 'minimum_investment', 'maximum_investment',
        ]
        widgets = {
            'listing_type': forms.RadioSelect(attrs={
                'class': 'form-check-input listing-type-radio',
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Give your project a compelling title'
            }),
            'short_description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Write a brief summary that captures your project essence (max 255 characters)',
                'maxlength': '255'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'funding_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'funding_goal': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '10000'
            }),
            'deadline': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Lagos, Nigeria'
            }),
            'video_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://youtube.com/watch?v=...'
            }),
            # Venture-specific widgets
            'company_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your company or business name'
            }),
            'financing_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'equity_offered': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '10.00',
                'step': '0.01',
                'min': '0',
                'max': '100'
            }),
            'valuation': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '100000',
                'step': '0.01'
            }),
            'interest_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '8.00',
                'step': '0.01',
                'min': '0'
            }),
            'repayment_period_months': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '24',
                'min': '1'
            }),
            'use_of_funds': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Explain how the investment funds will be allocated...'
            }),
            # SRT fields
            'srt_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'srt_funding_goal': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '10000',
                'step': '0.01',
                'min': '0'
            }),
            'expected_return_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '15.00',
                'step': '0.01',
                'min': '0'
            }),
            'investment_duration_months': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '12',
                'min': '1'
            }),
            'minimum_investment': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '10',
                'step': '0.01',
                'min': '0'
            }),
            'maximum_investment': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Leave blank for no limit',
                'step': '0.01',
                'min': '0'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].empty_label = "Select Category"
        self.fields['funding_type'].empty_label = "Select Funding Type"
        # Venture fields are optional at the form level; validated in clean()
        optional_fields = [
            'company_name', 'financing_type', 'equity_offered', 'valuation',
            'interest_rate', 'repayment_period_months', 'use_of_funds',
            'srt_enabled', 'srt_funding_goal', 'expected_return_rate',
            'investment_duration_months', 'minimum_investment', 'maximum_investment',
        ]
        for field_name in optional_fields:
            self.fields[field_name].required = False

    def clean(self):
        cleaned_data = super().clean()
        listing_type = cleaned_data.get('listing_type')

        if listing_type == 'venture':
            # Validate required venture fields
            if not cleaned_data.get('company_name'):
                self.add_error('company_name', 'Company name is required for ventures.')
            if not cleaned_data.get('financing_type'):
                self.add_error('financing_type', 'Please select a financing type.')

            financing_type = cleaned_data.get('financing_type')
            if financing_type == 'equity':
                equity = cleaned_data.get('equity_offered')
                if not equity or equity <= 0:
                    self.add_error('equity_offered', 'Equity percentage is required for equity financing.')
                valuation = cleaned_data.get('valuation')
                if not valuation or valuation <= 0:
                    self.add_error('valuation', 'Company valuation is required for equity financing.')
            elif financing_type == 'debt':
                rate = cleaned_data.get('interest_rate')
                if not rate or rate <= 0:
                    self.add_error('interest_rate', 'Interest rate is required for debt financing.')
                period = cleaned_data.get('repayment_period_months')
                if not period or period <= 0:
                    self.add_error('repayment_period_months', 'Repayment period is required for debt financing.')

        return cleaned_data


class RewardForm(forms.ModelForm):
    """Form for creating and editing project rewards."""

    class Meta:
        model = Reward
        fields = ['title', 'description', 'amount']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Reward title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describe what backers will receive...'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Minimum pledge amount',
                'min': '1'
            }),
        }


# Formset for managing multiple rewards during project creation/editing
RewardFormSet = inlineformset_factory(
    Project,
    Reward,
    form=RewardForm,
    extra=3,  # Show 3 empty reward forms by default
    can_delete=True,
    min_num=0,
    validate_min=False,
)


class UpdateForm(forms.ModelForm):
    """Form for posting project updates."""

    class Meta:
        model = Update
        fields = ['title', 'content']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Update title'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Share your progress with backers...'
            }),
        }


class DonationForm(forms.ModelForm):
    """Form for making donations to projects."""

    class Meta:
        model = Donation
        fields = ['amount', 'reward', 'message', 'is_anonymous']
        widgets = {
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter amount in USD',
                'min': '1'
            }),
            'reward': forms.Select(attrs={
                'class': 'form-select'
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Leave a message for the creator (optional)'
            }),
            'is_anonymous': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

    def __init__(self, *args, project=None, **kwargs):
        super().__init__(*args, **kwargs)
        if project:
            self.fields['reward'].queryset = project.rewards.all()
            self.fields['reward'].required = False
        self.fields['reward'].empty_label = "Select a Reward (Optional)"


class InvestmentForm(forms.ModelForm):
    """Form for submitting investments."""

    class Meta:
        model = Investment
        fields = ['amount', 'terms']
        widgets = {
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Investment amount in USD'
            }),
            'terms': forms.Select(attrs={
                'class': 'form-select'
            }),
        }

    def __init__(self, *args, project=None, **kwargs):
        super().__init__(*args, **kwargs)
        if project:
            self.fields['terms'].queryset = project.investment_terms.all()
            self.fields['terms'].required = False
        self.fields['terms'].empty_label = "Select Investment Terms"
