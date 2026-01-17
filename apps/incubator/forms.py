from django import forms
from .models import IncubatorApplication


class IncubatorApplicationForm(forms.ModelForm):
    """Form for incubator/accelerator applications."""

    class Meta:
        model = IncubatorApplication
        fields = [
            'project', 'applicant_name', 'applicant_email', 'applicant_phone',
            'applicant_company', 'website', 'stage', 'industry', 'application_text',
            'traction', 'team_background', 'goals_for_program', 'funding_raised',
            'funding_needed', 'pitch_deck'
        ]
        widgets = {
            'project': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your startup/project name'
            }),
            'applicant_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Full name'
            }),
            'applicant_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'email@example.com'
            }),
            'applicant_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+234...'
            }),
            'applicant_company': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Company name (if registered)'
            }),
            'website': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://yourwebsite.com'
            }),
            'stage': forms.Select(attrs={
                'class': 'form-select'
            }),
            'industry': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., FinTech, AgriTech, HealthTech'
            }),
            'goals_for_program': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'What do you hope to achieve during the accelerator program?'
            }),
            'funding_raised': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., $10,000 from grants'
            }),
            'funding_needed': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., $50,000 seed round'
            }),
            'pitch_deck': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.ppt,.pptx'
            }),
        }
        labels = {
            'project': 'Project/Startup Name',
            'applicant_name': 'Your Full Name',
            'applicant_email': 'Email Address',
            'applicant_phone': 'Phone Number',
            'applicant_company': 'Company Name',
            'website': 'Website URL',
            'stage': 'Current Stage',
            'industry': 'Industry/Sector',
            'application_text': 'Describe Your Startup',
            'traction': 'Traction & Milestones',
            'team_background': 'Team Background',
            'goals_for_program': 'Goals for the Program',
            'funding_raised': 'Funding Already Raised',
            'funding_needed': 'Funding You\'re Seeking',
            'pitch_deck': 'Pitch Deck (Optional)',
        }
