from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, Submit
from .models import (Project, Reward, InvestmentTerm, Investment, 
                     Pledge, FundingType, CustomUser, FounderProfile, InvestorProfile, IncubatorApplication)
from ckeditor.widgets import CKEditorWidget
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth import get_user_model
from .signals import send_password_reset_email
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes


class CustomPasswordResetForm(PasswordResetForm):
    def send_mail(self, subject_template_name, email_template_name,
                  context, from_email, to_email, html_email_template_name=None):
        """
        Override the send_mail method to use our custom email function
        """
        user = context['user']
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = context['token']
        
        # Create the reset URL
        reset_url = f"{context['protocol']}://{context['domain']}/reset/{uid}/{token}/"
        
        # Use our custom email function
        send_password_reset_email(user, reset_url)


class SignUpForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput)

    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'user_type']

    def clean_password2(self):
        cd = self.cleaned_data
        if cd['password'] != cd['password2']:
            raise forms.ValidationError('Passwords don\'t match.')
        return cd['password2']


class ProjectForm(forms.ModelForm):
    description = forms.CharField(widget=CKEditorWidget())
    
    class Meta:
        model = Project
        fields = [
            'title', 'description', 'funding_type', 'category', 
            'funding_goal', 'deadline', 'image', 'location', 'short_description', 'video_url'
        ]
        widgets = {
            'deadline': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Replace empty labels for all ModelChoiceFields
        for field_name, field in self.fields.items():
            if hasattr(field, 'empty_label') and field.empty_label == "---------":
                field.empty_label = f"Select {field_name.replace('_', ' ')}"
        
        if 'category' in self.fields:
            self.fields['category'].empty_label = "Select a category"
        
        if 'funding_type' in self.fields:
            self.fields['funding_type'].empty_label = "Select funding type"

class RewardForm(forms.ModelForm):
    class Meta:
        model = Reward
        fields = ['title', 'description', 'amount']

class InvestmentTermForm(forms.ModelForm):
    class Meta:
        model = InvestmentTerm
        fields = ['equity_offered', 'minimum_investment', 'valuation', 'deadline']
        widgets = {
            'deadline': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }


class InvestmentForm(forms.ModelForm):
    class Meta:
        model = Investment
        fields = ['amount']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'min': '500'})
        }
    
    def __init__(self, *args, **kwargs):
        self.terms = kwargs.pop('terms', None)
        self.project = kwargs.pop('project', None)
        super().__init__(*args, **kwargs)
        
        if self.project:
            # Set minimum investment from terms or default to $500
            min_investment = 500
            if self.terms and hasattr(self.terms, 'minimum_investment'):  # Changed from min_investment
                min_investment = self.terms.minimum_investment  # Changed from min_investment
                
            self.fields['amount'].widget.attrs['min'] = min_investment
            # Set maximum investment to the project's total funding goal
            max_amount = self.project.funding_goal
            self.fields['amount'].widget.attrs['max'] = max_amount
            self.fields['amount'].help_text = f"Minimum investment: ${min_investment}. Maximum: ${max_amount}"
    
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount is None:
            raise forms.ValidationError("Please enter an investment amount.")
        
        # Validate minimum investment
        min_investment = 500
        if self.terms and hasattr(self.terms, 'minimum_investment'):  # Changed from min_investment
            min_investment = self.terms.minimum_investment  # Changed from min_investment
            
        if amount < min_investment:
            raise forms.ValidationError(f"Minimum investment amount is ${min_investment}.")
        
        # Validate maximum investment
        if self.project:
            max_amount = self.project.funding_goal
            if amount > max_amount:
                raise forms.ValidationError(f"Maximum investment amount is ${max_amount}.")
        
        return amount


class InvestmentAgreementForm(forms.Form):
    agree_to_terms = forms.BooleanField(
        required=True,
        label="I agree to the investment terms and conditions",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    electronic_signature = forms.CharField(
        required=True,
        label="Electronic Signature (Type your full name)",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
    
    def clean_electronic_signature(self):
        signature = self.cleaned_data.get('electronic_signature')
        if not self.user:
            raise forms.ValidationError("User information is missing.")
            
        user_full_name = f"{self.user.first_name} {self.user.last_name}".strip()
        
        if signature.lower() != user_full_name.lower():
            raise forms.ValidationError("Signature must match your full name.")
        
        return signature


class PledgeForm(forms.ModelForm):
    class Meta:
        model = Pledge
        fields = ['amount', 'reward']

    def __init__(self, *args, **kwargs):
        # Extract project from kwargs before initializing parent
        self.project = kwargs.pop('project', None)
        super().__init__(*args, **kwargs)
        
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Continue with Pledge', css_class='btn-success w-100'))
        
        # Filter rewards based on project
        if self.project:
            self.fields['reward'].queryset = self.project.rewards.all()
            
        # Change the empty label from dash to "Select Perks"
        self.fields['reward'].empty_label = "Select Perks"
    
    def clean(self):
        cleaned_data = super().clean()
        amount = cleaned_data.get('amount')
        reward = cleaned_data.get('reward')
        
        if reward and amount:
            if amount < reward.amount:
                raise forms.ValidationError(
                    f"Oops! This perk requires a minimum pledge of ${reward.amount}. "
                    f"Please increase your pledge amount or select a different perk that matches your budget."
                )
        
        return cleaned_data

class BaseProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'phone_number']

class FounderProfileForm(forms.ModelForm):
    class Meta:
        model = FounderProfile
        fields = ['image', 'company_name', 'industry', 'experience', 'cv']
        widgets = {
            'experience': forms.Textarea(attrs={'rows': 4, 'class': 'form-control', 'id': 'id_experience'}),
            'company_name': forms.TextInput(attrs={'class': 'form-control'}),
            'industry': forms.TextInput(attrs={'class': 'form-control'}),
            'cv': forms.FileInput(attrs={'class': 'form-control'})
        }
        labels = {
            'cv': 'CV/Resume',
        }
        help_texts = {
            'cv': 'Upload your CV or resume (PDF format recommended)',
            'experience': 'Use the rich text editor to format your experience',
        }

class InvestorProfileForm(forms.ModelForm):
    class Meta:
        model = InvestorProfile
        fields = ['investment_focus', 'preferred_industries']
        widgets = {
            'investment_focus': forms.Textarea(attrs={'rows': 3}),
            'preferred_industries': forms.TextInput(attrs={
                'placeholder': 'e.g., Technology, Agriculture, Healthcare'
            }),
        }

class EditProfileForm(forms.ModelForm):
    # Add country field with choices
    COUNTRIES = [
        ('', 'Select Country'),
        ('AF', 'Afghanistan'),
        ('AL', 'Albania'),
        ('DZ', 'Algeria'),
        ('AD', 'Andorra'),
        ('AO', 'Angola'),
        ('AG', 'Antigua and Barbuda'),
        ('AR', 'Argentina'),
        ('AM', 'Armenia'),
        ('AU', 'Australia'),
        ('AT', 'Austria'),
        ('AZ', 'Azerbaijan'),
        ('BS', 'Bahamas'),
        ('BH', 'Bahrain'),
        ('BD', 'Bangladesh'),
        ('BB', 'Barbados'),
        ('BY', 'Belarus'),
        ('BE', 'Belgium'),
        ('BZ', 'Belize'),
        ('BJ', 'Benin'),
        ('BT', 'Bhutan'),
        ('BO', 'Bolivia'),
        ('BA', 'Bosnia and Herzegovina'),
        ('BW', 'Botswana'),
        ('BR', 'Brazil'),
        ('BN', 'Brunei'),
        ('BG', 'Bulgaria'),
        ('BF', 'Burkina Faso'),
        ('BI', 'Burundi'),
        ('CV', 'Cabo Verde'),
        ('KH', 'Cambodia'),
        ('CM', 'Cameroon'),
        ('CA', 'Canada'),
        ('CF', 'Central African Republic'),
        ('TD', 'Chad'),
        ('CL', 'Chile'),
        ('CN', 'China'),
        ('CO', 'Colombia'),
        ('KM', 'Comoros'),
        ('CG', 'Congo'),
        ('CD', 'Congo (Democratic Republic)'),
        ('CR', 'Costa Rica'),
        ('CI', 'Côte d\'Ivoire'),
        ('HR', 'Croatia'),
        ('CU', 'Cuba'),
        ('CY', 'Cyprus'),
        ('CZ', 'Czech Republic'),
        ('DK', 'Denmark'),
        ('DJ', 'Djibouti'),
        ('DM', 'Dominica'),
        ('DO', 'Dominican Republic'),
        ('EC', 'Ecuador'),
        ('EG', 'Egypt'),
        ('SV', 'El Salvador'),
        ('GQ', 'Equatorial Guinea'),
        ('ER', 'Eritrea'),
        ('EE', 'Estonia'),
        ('SZ', 'Eswatini'),
        ('ET', 'Ethiopia'),
        ('FJ', 'Fiji'),
        ('FI', 'Finland'),
        ('FR', 'France'),
        ('GA', 'Gabon'),
        ('GM', 'Gambia'),
        ('GE', 'Georgia'),
        ('DE', 'Germany'),
        ('GH', 'Ghana'),
        ('GR', 'Greece'),
        ('GD', 'Grenada'),
        ('GT', 'Guatemala'),
        ('GN', 'Guinea'),
        ('GW', 'Guinea-Bissau'),
        ('GY', 'Guyana'),
        ('HT', 'Haiti'),
        ('HN', 'Honduras'),
        ('HU', 'Hungary'),
        ('IS', 'Iceland'),
        ('IN', 'India'),
        ('ID', 'Indonesia'),
        ('IR', 'Iran'),
        ('IQ', 'Iraq'),
        ('IE', 'Ireland'),
        ('IL', 'Israel'),
        ('IT', 'Italy'),
        ('JM', 'Jamaica'),
        ('JP', 'Japan'),
        ('JO', 'Jordan'),
        ('KZ', 'Kazakhstan'),
        ('KE', 'Kenya'),
        ('KI', 'Kiribati'),
        ('KP', 'North Korea'),
        ('KR', 'South Korea'),
        ('KW', 'Kuwait'),
        ('KG', 'Kyrgyzstan'),
        ('LA', 'Laos'),
        ('LV', 'Latvia'),
        ('LB', 'Lebanon'),
        ('LS', 'Lesotho'),
        ('LR', 'Liberia'),
        ('LY', 'Libya'),
        ('LI', 'Liechtenstein'),
        ('LT', 'Lithuania'),
        ('LU', 'Luxembourg'),
        ('MG', 'Madagascar'),
        ('MW', 'Malawi'),
        ('MY', 'Malaysia'),
        ('MV', 'Maldives'),
        ('ML', 'Mali'),
        ('MT', 'Malta'),
        ('MH', 'Marshall Islands'),
        ('MR', 'Mauritania'),
        ('MU', 'Mauritius'),
        ('MX', 'Mexico'),
        ('FM', 'Micronesia'),
        ('MD', 'Moldova'),
        ('MC', 'Monaco'),
        ('MN', 'Mongolia'),
        ('ME', 'Montenegro'),
        ('MA', 'Morocco'),
        ('MZ', 'Mozambique'),
        ('MM', 'Myanmar'),
        ('NA', 'Namibia'),
        ('NR', 'Nauru'),
        ('NP', 'Nepal'),
        ('NL', 'Netherlands'),
        ('NZ', 'New Zealand'),
        ('NI', 'Nicaragua'),
        ('NE', 'Niger'),
        ('NG', 'Nigeria'),
        ('MK', 'North Macedonia'),
        ('NO', 'Norway'),
        ('OM', 'Oman'),
        ('PK', 'Pakistan'),
        ('PW', 'Palau'),
        ('PA', 'Panama'),
        ('PG', 'Papua New Guinea'),
        ('PY', 'Paraguay'),
        ('PE', 'Peru'),
        ('PH', 'Philippines'),
        ('PL', 'Poland'),
        ('PT', 'Portugal'),
        ('QA', 'Qatar'),
        ('RO', 'Romania'),
        ('RU', 'Russia'),
        ('RW', 'Rwanda'),
        ('KN', 'Saint Kitts and Nevis'),
        ('LC', 'Saint Lucia'),
        ('VC', 'Saint Vincent and the Grenadines'),
        ('WS', 'Samoa'),
        ('SM', 'San Marino'),
        ('ST', 'Sao Tome and Principe'),
        ('SA', 'Saudi Arabia'),
        ('SN', 'Senegal'),
        ('RS', 'Serbia'),
        ('SC', 'Seychelles'),
        ('SL', 'Sierra Leone'),
        ('SG', 'Singapore'),
        ('SK', 'Slovakia'),
        ('SI', 'Slovenia'),
        ('SB', 'Solomon Islands'),
        ('SO', 'Somalia'),
        ('ZA', 'South Africa'),
        ('KR', 'South Korea'),
        ('ES', 'Spain'),
        ('LK', 'Sri Lanka'),
        ('SD', 'Sudan'),
        ('SR', 'Suriname'),
        ('SZ', 'Swaziland'),
        ('SE', 'Sweden'),
        ('CH', 'Switzerland'),
        ('SY', 'Syria'),
        ('TW', 'Taiwan'),
        ('TJ', 'Tajikistan'),
        ('TZ', 'Tanzania'),
        ('TH', 'Thailand'),
        ('TG', 'Togo'),
        ('TO', 'Tonga'),
        ('TT', 'Trinidad and Tobago'),
        ('TN', 'Tunisia'),
        ('TR', 'Turkey'),
        ('TM', 'Turkmenistan'),
        ('UG', 'Uganda'),
        ('UA', 'Ukraine'),
        ('AE', 'United Arab Emirates'),
        ('GB', 'United Kingdom'),
        ('US', 'United States'),
        ('UY', 'Uruguay'),
        ('UZ', 'Uzbekistan'),
        ('VU', 'Vanuatu'),
        ('VE', 'Venezuela'),
        ('VN', 'Vietnam'),
        ('YE', 'Yemen'),
        ('ZM', 'Zambia'),
        ('ZW', 'Zimbabwe'),
    ]
    
    country = forms.ChoiceField(
        choices=COUNTRIES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    address_line1 = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Street address'}),
        label="Address Line 1"
    )
    
    address_line2 = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apt, Suite, Building (optional)'}),
        label="Address Line 2"
    )
    
    city = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    
    state_province = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'State/Province/Region'}),
        label="State/Province"
    )
    
    postal_code = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ZIP/Postal Code'}),
        label="Postal/ZIP Code"
    )
    
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'location', 
                 'address_line1', 'address_line2', 'city', 'state_province', 'postal_code', 'country', 'user_type']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City, Country'}),
            'user_type': forms.Select(attrs={'class': 'form-control'}),
        }


class IncubatorApplicationForm(forms.ModelForm):
    class Meta:
        model = IncubatorApplication
        fields = [
            'project',
            'applicant_name',
            'applicant_email',
            'applicant_phone',
            'applicant_company',
            'website',
            'industry',
            'stage',
            'application_text',
            'traction',
            'team_background',
            'goals_for_program',
            'funding_raised',
            'funding_needed',
            'pitch_deck',
        ]
        labels = {
            'applicant_name': 'Full Name',
            'applicant_email': 'Email Address',
            'applicant_phone': 'Phone Number',
            'applicant_company': 'Startup / Company Name',
            'application_text': 'Describe Your Startup'
        }
        widgets = {
            'application_text': CKEditorWidget(),
            'traction': CKEditorWidget(),
            'team_background': CKEditorWidget(),
            'goals_for_program': forms.Textarea(attrs={'rows': 3}),
            'funding_raised': forms.TextInput(attrs={'placeholder': 'e.g. $5,000 in grants'}),
            'funding_needed': forms.TextInput(attrs={'placeholder': 'e.g. $25,000 seed round'}),
            'pitch_deck': forms.FileInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        
        # Optional UI enhancements
        self.fields['applicant_name'].widget.attrs.update({'placeholder': 'e.g. Adamu Eze Olabisi'})
        self.fields['applicant_email'].widget.attrs.update({'placeholder': 'e.g. mymail@email.com'})
        self.fields['applicant_phone'].widget.attrs.update({'placeholder': 'e.g. +234 803 111 2223'})
        self.fields['website'].widget.attrs.update({'placeholder': 'https://yourstartup.com'})
        self.fields['traction'].label = "Startup Traction"
        self.fields['application_text'].widget.attrs.update({'placeholder': 'Enter your startup description'})
        self.fields['team_background'].label = "Founding Team Background"
        self.fields['goals_for_program'].label = "What Are You Hoping to Achieve?"
        self.fields['pitch_deck'].label = "Upload Pitch Deck (PDF, Max 10MB)"



class BaseProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'phone_number']

class FounderProfileForm(forms.ModelForm):
    class Meta:
        model = FounderProfile
        fields = ['image', 'company_name', 'industry', 'experience', 'cv']
        widgets = {
            'experience': forms.Textarea(attrs={'rows': 4, 'class': 'form-control', 'id': 'id_experience'}),
            'company_name': forms.TextInput(attrs={'class': 'form-control'}),
            'industry': forms.TextInput(attrs={'class': 'form-control'}),
            'cv': forms.FileInput(attrs={'class': 'form-control'})
        }
        labels = {
            'cv': 'CV/Resume',
        }
        help_texts = {
            'cv': 'Upload your CV or resume (PDF format recommended)',
            'experience': 'Use the rich text editor to format your experience',
        }

class InvestorProfileForm(forms.ModelForm):
    class Meta:
        model = InvestorProfile
        fields = ['investment_focus', 'preferred_industries']
        widgets = {
            'investment_focus': forms.Textarea(attrs={'rows': 3}),
            'preferred_industries': forms.TextInput(attrs={
                'placeholder': 'e.g., Technology, Agriculture, Healthcare'
            }),
        }

class EditProfileForm(forms.ModelForm):
    # Add country field with choices
    COUNTRIES = [
        ('', 'Select Country'),
        ('AF', 'Afghanistan'),
        ('AL', 'Albania'),
        ('DZ', 'Algeria'),
        ('AD', 'Andorra'),
        ('AO', 'Angola'),
        ('AG', 'Antigua and Barbuda'),
        ('AR', 'Argentina'),
        ('AM', 'Armenia'),
        ('AU', 'Australia'),
        ('AT', 'Austria'),
        ('AZ', 'Azerbaijan'),
        ('BS', 'Bahamas'),
        ('BH', 'Bahrain'),
        ('BD', 'Bangladesh'),
        ('BB', 'Barbados'),
        ('BY', 'Belarus'),
        ('BE', 'Belgium'),
        ('BZ', 'Belize'),
        ('BJ', 'Benin'),
        ('BT', 'Bhutan'),
        ('BO', 'Bolivia'),
        ('BA', 'Bosnia and Herzegovina'),
        ('BW', 'Botswana'),
        ('BR', 'Brazil'),
        ('BN', 'Brunei'),
        ('BG', 'Bulgaria'),
        ('BF', 'Burkina Faso'),
        ('BI', 'Burundi'),
        ('CV', 'Cabo Verde'),
        ('KH', 'Cambodia'),
        ('CM', 'Cameroon'),
        ('CA', 'Canada'),
        ('CF', 'Central African Republic'),
        ('TD', 'Chad'),
        ('CL', 'Chile'),
        ('CN', 'China'),
        ('CO', 'Colombia'),
        ('KM', 'Comoros'),
        ('CG', 'Congo'),
        ('CD', 'Congo (Democratic Republic)'),
        ('CR', 'Costa Rica'),
        ('CI', 'Côte d\'Ivoire'),
        ('HR', 'Croatia'),
        ('CU', 'Cuba'),
        ('CY', 'Cyprus'),
        ('CZ', 'Czech Republic'),
        ('DK', 'Denmark'),
        ('DJ', 'Djibouti'),
        ('DM', 'Dominica'),
        ('DO', 'Dominican Republic'),
        ('EC', 'Ecuador'),
        ('EG', 'Egypt'),
        ('SV', 'El Salvador'),
        ('GQ', 'Equatorial Guinea'),
        ('ER', 'Eritrea'),
        ('EE', 'Estonia'),
        ('SZ', 'Eswatini'),
        ('ET', 'Ethiopia'),
        ('FJ', 'Fiji'),
        ('FI', 'Finland'),
        ('FR', 'France'),
        ('GA', 'Gabon'),
        ('GM', 'Gambia'),
        ('GE', 'Georgia'),
        ('DE', 'Germany'),
        ('GH', 'Ghana'),
        ('GR', 'Greece'),
        ('GD', 'Grenada'),
        ('GT', 'Guatemala'),
        ('GN', 'Guinea'),
        ('GW', 'Guinea-Bissau'),
        ('GY', 'Guyana'),
        ('HT', 'Haiti'),
        ('HN', 'Honduras'),
        ('HU', 'Hungary'),
        ('IS', 'Iceland'),
        ('IN', 'India'),
        ('ID', 'Indonesia'),
        ('IR', 'Iran'),
        ('IQ', 'Iraq'),
        ('IE', 'Ireland'),
        ('IL', 'Israel'),
        ('IT', 'Italy'),
        ('JM', 'Jamaica'),
        ('JP', 'Japan'),
        ('JO', 'Jordan'),
        ('KZ', 'Kazakhstan'),
        ('KE', 'Kenya'),
        ('KI', 'Kiribati'),
        ('KP', 'North Korea'),
        ('KR', 'South Korea'),
        ('KW', 'Kuwait'),
        ('KG', 'Kyrgyzstan'),
        ('LA', 'Laos'),
        ('LV', 'Latvia'),
        ('LB', 'Lebanon'),
        ('LS', 'Lesotho'),
        ('LR', 'Liberia'),
        ('LY', 'Libya'),
        ('LI', 'Liechtenstein'),
        ('LT', 'Lithuania'),
        ('LU', 'Luxembourg'),
        ('MG', 'Madagascar'),
        ('MW', 'Malawi'),
        ('MY', 'Malaysia'),
        ('MV', 'Maldives'),
        ('ML', 'Mali'),
        ('MT', 'Malta'),
        ('MH', 'Marshall Islands'),
        ('MR', 'Mauritania'),
        ('MU', 'Mauritius'),
        ('MX', 'Mexico'),
        ('FM', 'Micronesia'),
        ('MD', 'Moldova'),
        ('MC', 'Monaco'),
        ('MN', 'Mongolia'),
        ('ME', 'Montenegro'),
        ('MA', 'Morocco'),
        ('MZ', 'Mozambique'),
        ('MM', 'Myanmar'),
        ('NA', 'Namibia'),
        ('NR', 'Nauru'),
        ('NP', 'Nepal'),
        ('NL', 'Netherlands'),
        ('NZ', 'New Zealand'),
        ('NI', 'Nicaragua'),
        ('NE', 'Niger'),
        ('NG', 'Nigeria'),
        ('MK', 'North Macedonia'),
        ('NO', 'Norway'),
        ('OM', 'Oman'),
        ('PK', 'Pakistan'),
        ('PW', 'Palau'),
        ('PA', 'Panama'),
        ('PG', 'Papua New Guinea'),
        ('PY', 'Paraguay'),
        ('PE', 'Peru'),
        ('PH', 'Philippines'),
        ('PL', 'Poland'),
        ('PT', 'Portugal'),
        ('QA', 'Qatar'),
        ('RO', 'Romania'),
        ('RU', 'Russia'),
        ('RW', 'Rwanda'),
        ('KN', 'Saint Kitts and Nevis'),
        ('LC', 'Saint Lucia'),
        ('VC', 'Saint Vincent and the Grenadines'),
        ('WS', 'Samoa'),
        ('SM', 'San Marino'),
        ('ST', 'Sao Tome and Principe'),
        ('SA', 'Saudi Arabia'),
        ('SN', 'Senegal'),
        ('RS', 'Serbia'),
        ('SC', 'Seychelles'),
        ('SL', 'Sierra Leone'),
        ('SG', 'Singapore'),
        ('SK', 'Slovakia'),
        ('SI', 'Slovenia'),
        ('SB', 'Solomon Islands'),
        ('SO', 'Somalia'),
        ('ZA', 'South Africa'),
        ('KR', 'South Korea'),
        ('ES', 'Spain'),
        ('LK', 'Sri Lanka'),
        ('SD', 'Sudan'),
        ('SR', 'Suriname'),
        ('SZ', 'Swaziland'),
        ('SE', 'Sweden'),
        ('CH', 'Switzerland'),
        ('SY', 'Syria'),
        ('TW', 'Taiwan'),
        ('TJ', 'Tajikistan'),
        ('TZ', 'Tanzania'),
        ('TH', 'Thailand'),
        ('TG', 'Togo'),
        ('TO', 'Tonga'),
        ('TT', 'Trinidad and Tobago'),
        ('TN', 'Tunisia'),
        ('TR', 'Turkey'),
        ('TM', 'Turkmenistan'),
        ('UG', 'Uganda'),
        ('UA', 'Ukraine'),
        ('AE', 'United Arab Emirates'),
        ('GB', 'United Kingdom'),
        ('US', 'United States'),
        ('UY', 'Uruguay'),
        ('UZ', 'Uzbekistan'),
        ('VU', 'Vanuatu'),
        ('VE', 'Venezuela'),
        ('VN', 'Vietnam'),
        ('YE', 'Yemen'),
        ('ZM', 'Zambia'),
        ('ZW', 'Zimbabwe'),
    ]
    
    country = forms.ChoiceField(
        choices=COUNTRIES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    address_line1 = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Street address'}),
        label="Address Line 1"
    )
    
    address_line2 = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apt, Suite, Building (optional)'}),
        label="Address Line 2"
    )
    
    city = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    
    state_province = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'State/Province/Region'}),
        label="State/Province"
    )
    
    postal_code = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ZIP/Postal Code'}),
        label="Postal/ZIP Code"
    )
    
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'location', 
                 'address_line1', 'address_line2', 'city', 'state_province', 'postal_code', 'country', 'user_type']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City, Country'}),
            'user_type': forms.Select(attrs={'class': 'form-control'}),
        }