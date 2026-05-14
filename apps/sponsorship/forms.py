from django import forms
from .models import SponsorshipInquiry


class SponsorshipInquiryForm(forms.ModelForm):
    class Meta:
        model = SponsorshipInquiry
        fields = [
            'company_name', 'contact_name', 'contact_email', 'contact_phone',
            'organization_type', 'tier', 'program_interest', 'budget_range', 'message',
        ]
        widgets = {
            'company_name':       forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Dangote Group'}),
            'contact_name':       forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your full name'}),
            'contact_email':      forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'you@company.com'}),
            'contact_phone':      forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+234 800 000 0000'}),
            'organization_type':  forms.Select(attrs={'class': 'form-select'}),
            'tier':               forms.Select(attrs={'class': 'form-select'}),
            'program_interest':   forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': "Describe the kind of program or cohort you're interested in sponsoring..."}),
            'budget_range':       forms.Select(attrs={'class': 'form-select'}),
            'message':            forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Any other context or questions for our team...'}),
        }
        labels = {
            'tier': 'Sponsorship Tier (optional)',
            'message': 'Anything else? (optional)',
            'contact_phone': 'Phone Number (optional)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import SponsorshipTier
        self.fields['tier'].queryset = SponsorshipTier.objects.filter(is_active=True)
        self.fields['tier'].empty_label = "— Not sure yet —"
        self.fields['tier'].required = False
        self.fields['message'].required = False
        self.fields['contact_phone'].required = False
