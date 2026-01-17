from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, Submit
from apps.accounts.models import CustomUser, FounderProfile, InvestorProfile, PartnerProfile
from ckeditor.widgets import CKEditorWidget
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth import get_user_model
from apps.accounts.signals import send_password_reset_email
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


class BaseProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'phone_number']

class FounderProfileForm(forms.ModelForm):
    class Meta:
        model = FounderProfile
        fields = ['image', 'company_name', 'industry', 'experience', 'cv', 'website', 'bio']
        widgets = {
            'experience': forms.Textarea(attrs={'rows': 4, 'class': 'form-control', 'id': 'id_experience'}),
            'company_name': forms.TextInput(attrs={'class': 'form-control'}),
            'industry': forms.TextInput(attrs={'class': 'form-control'}),
            'cv': forms.FileInput(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
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
            'investment_focus': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'preferred_industries': forms.TextInput(attrs={
                'placeholder': 'e.g., Technology, Agriculture, Healthcare',
                'class': 'form-control'
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


class PartnerProfileForm(forms.ModelForm):
    """Form for editing SRT Partner profile."""

    RISK_PROFILE_CHOICES = [
        ('conservative', 'Conservative - Lower risk, steady returns'),
        ('moderate', 'Moderate - Balanced risk and returns'),
        ('aggressive', 'Aggressive - Higher risk, potentially higher returns'),
    ]

    risk_profile = forms.ChoiceField(
        choices=RISK_PROFILE_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        required=True
    )

    class Meta:
        model = PartnerProfile
        fields = ['image', 'company_name', 'occupation', 'bio', 'risk_profile']
        widgets = {
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'company_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your company or organization name'
            }),
            'occupation': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your job title or profession'
            }),
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Tell us about yourself and your investment interests...'
            }),
        }
        labels = {
            'image': 'Profile Photo',
            'company_name': 'Company/Organization',
            'occupation': 'Occupation/Title',
            'bio': 'About Me',
            'risk_profile': 'Investment Risk Profile',
        }
        help_texts = {
            'risk_profile': 'Choose your preferred investment risk level. This helps us recommend suitable ventures.',
        }