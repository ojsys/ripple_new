from django.contrib.auth import login, logout
from django.contrib.auth.views import LogoutView
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_GET
from django.http import HttpResponseBadRequest
from django.utils import timezone
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
import stripe
import json
import requests
from django.conf import settings
from django.contrib import messages
from django.db import transaction
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Count, Sum, Avg, DurationField, Q, ExpressionWrapper, F, FloatField, DecimalField
from django.db.models.functions import Coalesce
from datetime import datetime
from decimal import Decimal
from django import forms
from .models import (Project, FundingType, InvestmentTerm, Investment, Pledge, SiteSettings,
                     Reward, Category, FounderProfile, InvestorProfile, HeroSlider, Testimonial, 
                     AboutPage, IncubatorAcceleratorPage, IncubatorApplication, TeamMember) 
from .forms import (ProjectForm, RewardForm, InvestmentTermForm, InvestmentForm, EditProfileForm,
                    PledgeForm, SignUpForm, BaseProfileForm, FounderProfileForm, InvestorProfileForm, InvestmentAgreementForm, IncubatorApplicationForm)


stripe.api_key = settings.STRIPE_SECRET_KEY


def site_settings(request):
    return {
        'site_settings': SiteSettings.objects.first()
    }
    
    

def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.email  # Use email as username
            user.set_password(form.cleaned_data['password'])
            user.save()
            
            # Create profile based on user type
            if user.user_type == 'founder':
                FounderProfile.objects.create(user=user)
            elif user.user_type == 'investor':
                InvestorProfile.objects.create(user=user)
                
            login(request, user)
            return redirect('dashboard')
    else:
        form = SignUpForm()
    return render(request, 'signup.html', {'form': form})


def verify_email(request, uidb64, token):
    try:
        # Decode the user id
        uid = urlsafe_base64_decode(uidb64).decode()
        user = CustomUser.objects.get(pk=uid)
        
        # Check if the token is valid
        if default_token_generator.check_token(user, token):
            # Mark user as verified
            user.is_active = True
            user.email_verified = True
            user.save()
            
            messages.success(request, "Your email has been verified successfully! You can now log in.")
            return redirect('login')
        else:
            messages.error(request, "The verification link is invalid or has expired.")
            return redirect('home')
    except Exception as e:
        messages.error(request, "An error occurred during verification. Please try again.")
        return redirect('home')

def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})


@require_GET
def user_logout(request):
    logout(request)
    return redirect('home')

##### Edit/Updates ##########

@login_required
def edit_profile(request):
    user = request.user
    
    # Initialize forms based on user type
    if user.user_type == 'founder':
        founder_profile, created = FounderProfile.objects.get_or_create(user=user)
        investor_form = None
    elif user.user_type == 'investor':
        investor_profile, created = InvestorProfile.objects.get_or_create(user=user)
        founder_form = None
    else:
        founder_form = None
        investor_form = None
    
    if request.method == 'POST':
        # Process the user form
        user_form = EditProfileForm(request.POST, instance=user)
        
        # Process profile-specific forms
        if user.user_type == 'founder':
            founder_form = FounderProfileForm(
                request.POST, 
                request.FILES, 
                instance=founder_profile
            )
            
            if user_form.is_valid() and founder_form.is_valid():
                # Save user form
                user_form.save()
                
                # Save founder profile with explicit commit
                founder_profile = founder_form.save(commit=False)
                founder_profile.user = user
                founder_profile.save()
                
                messages.success(request, 'Profile updated successfully!')
                return redirect('edit_profile')
            else:
                for field, errors in user_form.errors.items():
                    for error in errors:
                        messages.error(request, f"Error in {field}: {error}")
                
                for field, errors in founder_form.errors.items():
                    for error in errors:
                        messages.error(request, f"Error in {field}: {error}")
        
        elif user.user_type == 'investor':
            investor_form = InvestorProfileForm(
                request.POST, 
                request.FILES, 
                instance=investor_profile
            )
            
            if user_form.is_valid() and investor_form.is_valid():
                user_form.save()
                investor_profile = investor_form.save(commit=False)
                investor_profile.user = user
                investor_profile.save()
                
                messages.success(request, 'Profile updated successfully!')
                return redirect('edit_profile')
            else:
                for field, errors in user_form.errors.items():
                    for error in errors:
                        messages.error(request, f"Error in {field}: {error}")
                
                for field, errors in investor_form.errors.items():
                    for error in errors:
                        messages.error(request, f"Error in {field}: {error}")
        
        else:
            # For other user types, just save the user form
            if user_form.is_valid():
                user_form.save()
                messages.success(request, 'Profile updated successfully!')
                return redirect('edit_profile')
            else:
                for field, errors in user_form.errors.items():
                    for error in errors:
                        messages.error(request, f"Error in {field}: {error}")
    
    else:
        # GET request - initialize forms with existing data
        user_form = EditProfileForm(instance=user)
        
        if user.user_type == 'founder':
            founder_form = FounderProfileForm(instance=founder_profile)
        elif user.user_type == 'investor':
            investor_form = InvestorProfileForm(instance=investor_profile)
    
    context = {
        'user_form': user_form,
        'founder_form': founder_form if user.user_type == 'founder' else None,
        'investor_form': investor_form if user.user_type == 'investor' else None,
    }
    
    return render(request, 'projects/edit_profile.html', context)


def edit_project(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    
    # Check if user is the creator of the project
    if request.user != project.creator:
        messages.error(request, "You don't have permission to edit this project.")
        return redirect('project_detail', project_id=project.id)
    
    if request.method == 'POST':
        form = ProjectForm(request.POST, request.FILES, instance=project)
        if form.is_valid():
            form.save()
            messages.success(request, "Project updated successfully!")
            # Change this line from pk to project_id
            return redirect('project_detail', project_id=project.id)
    else:
        form = ProjectForm(instance=project)
    
    return render(request, 'projects/edit_project.html', {
        'form': form,
        'project': project
    })


######################

def home(request):
    sliders = HeroSlider.objects.filter(is_active=True)
    featured_projects = Project.objects.filter(status='approved').annotate(
        percent_funded=ExpressionWrapper(
            (F('amount_raised') * 100.0) / F('funding_goal'),
            output_field=FloatField()
        )
    )[:3]  # Get first 3 projects with funding percentage calculated
    # Get active testimonials
    testimonials = Testimonial.objects.filter(is_active=True)[:3]

    return render(request, 'projects/home.html', {
        'sliders': sliders,
        'featured_projects': featured_projects,
        'testimonials': testimonials
    })
    

def project_list(request):
    # Only show approved projects to regular users
    if request.user.is_staff or request.user.is_superuser:
        projects = Project.objects.all().order_by('-created_at')
    else:
        projects = Project.objects.filter(status='approved').order_by('-created_at')
    
    projects = projects.annotate(
        percent_funded=ExpressionWrapper(
            (F('amount_raised') * 100.0) / F('funding_goal'),
            output_field=FloatField()
        )
    )
    
    # Search
    search_query = request.GET.get('q')
    if search_query:
        projects = projects.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Filters
    category = request.GET.get('category')
    if category:
        projects = projects.filter(category__name=category)
    
    funding_type = request.GET.get('funding_type')
    if funding_type:
        projects = projects.filter(funding_type__name=funding_type)
    
    sort = request.GET.get('sort')
    if sort == 'newest':
        projects = projects.order_by('-created_at')
    elif sort == 'ending_soon':
        projects = projects.order_by('deadline')
    
    return render(request, 'projects/project_list.html', {
        'projects': projects,
        'categories': Category.objects.all(),
        'funding_types': FundingType.objects.all()
    })



# Project Creation view

@login_required
def create_project(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST, request.FILES)
        if form.is_valid():
            project = form.save(commit=False)
            project.creator = request.user
            project.status = 'pending'  # Set initial status to pending
            project.save()
            
            # Save many-to-many relationships
            form.save_m2m()
            
            messages.success(request, "Your project has been submitted for approval. You'll be notified once it's reviewed.")
            return redirect('add_terms_rewards', project.id)
    else:
        form = ProjectForm()
    return render(request, 'projects/create_project.html', {'form': form})


@login_required
def delete_project(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    
    # Check if the user is the creator of the project
    if request.user != project.creator:
        messages.error(request, "You don't have permission to delete this project.")
        return redirect('project_detail', project_id=project_id)
    
    if request.method == 'POST':
        # Store the project title for the success message
        project_title = project.title
        
        # Delete the project
        project.delete()
        
        messages.success(request, f"Project '{project_title}' has been deleted successfully.")
        return redirect('project_list')
    
    return render(request, 'projects/delete_project.html', {'project': project})


@login_required
def add_terms_rewards(request, project_id):
    project = get_object_or_404(Project, id=project_id, creator=request.user)
    
    if not project.funding_type:
        return HttpResponseBadRequest("Project has no funding type set")
    
    funding_type_name = project.funding_type.name.lower()
    
    # Map valid funding types to formset classes
    FORMSET_MAP = {
        'donation': (Reward, RewardForm),
        'equity': (InvestmentTerm, InvestmentTermForm)
    }
    
    if funding_type_name not in FORMSET_MAP:
        valid_types = ', '.join(FORMSET_MAP.keys())
        return HttpResponseBadRequest(f"Invalid project type. Valid types: {valid_types}")
    
    model_class, form_class = FORMSET_MAP[funding_type_name]
    formset_class = forms.inlineformset_factory(
        Project, model_class, form=form_class, extra=1
    )

    # Handle form submission
    if request.method == 'POST':
        formset = formset_class(request.POST, instance=project)
        if formset.is_valid():
            formset.save()
            return redirect('project_detail', project.id)
    else:
        formset = formset_class(instance=project)

    return render(request, 'add_terms_rewards.html', {
        'formset': formset,
        'project': project,
        'funding_type': funding_type_name
    })



# Project Detail Page

def project_detail(request, project_id):
    project = get_object_or_404(
        Project.objects.prefetch_related('investment_terms', 'rewards'),
        id=project_id
    )
    investment_terms = project.investment_terms.first()
    context = {
        'project': project,
        'percent_funded': project.get_percent_funded(),
        'terms': investment_terms,
    }

    if project.funding_type.name == 'Equity':
        if investment_terms:
            context['investment_form'] = InvestmentForm(
                terms=investment_terms,
                project=project
            )
        else:
            # For projects without terms, only pass the project
            context['investment_form'] = InvestmentForm(project=project)
    elif project.funding_type.name == 'Donation':
        context['pledge_form'] = PledgeForm(project=project)

    return render(request, 'projects/project_detail.html', context)


# Admin Approval
@login_required
def admin_project_approval(request):
    # Check if user is admin
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('home')
    
    # Get pending projects
    pending_projects = Project.objects.filter(status='pending').order_by('-created_at')
    
    return render(request, 'projects/admin_project_approval.html', {
        'pending_projects': pending_projects
    })

@login_required
def approve_project(request, project_id):
    # Check if user is admin
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, "You don't have permission to perform this action.")
        return redirect('home')
    
    project = get_object_or_404(Project, id=project_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        admin_notes = request.POST.get('admin_notes', '')
        
        if action == 'approve':
            project.status = 'approved'
            project.admin_notes = admin_notes
            project.save()
            
            # Notify the creator via email
            from .signals import send_project_approval_email
            send_project_approval_email(project)

            # Notify the creator
            messages.success(request, f"Project '{project.title}' has been approved.")
            
        elif action == 'reject':
            project.status = 'rejected'
            project.admin_notes = admin_notes
            project.save()
            
            # Notify the creator
            messages.success(request, f"Project '{project.title}' has been rejected.")
            
            # Notify the creator via email
            from .signals import send_project_rejection_email
            send_project_rejection_email(project)
            
        return redirect('admin_project_approval')
    
    return render(request, 'projects/approve_project.html', {
        'project': project
    })


# Investment Management (Founder)
@login_required
def manage_investments(request, project_id):
    project = get_object_or_404(Project, id=project_id, creator=request.user)
    investments = project.investments.filter(status='pending')
    return render(request, 'manage_investments.html', {'project': project, 'investments': investments})

@login_required
def update_investment_status(request, investment_id, status):
    investment = get_object_or_404(Investment, id=investment_id, project__creator=request.user)
    investment.status = status
    investment.save()
    return redirect('manage_investments', investment.project.id)


@login_required
def make_pledge(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    
    if request.method == 'POST':
        form = PledgeForm(request.POST, project=project)
        if form.is_valid():
            # Create pledge and save to DB first to get an ID
            pledge = form.save(commit=False)
            pledge.project = project
            pledge.backer = request.user
            pledge.save()  # Save immediately to get an ID
            
            # Convert USD to NGN (using a conversion rate of approximately 1 USD = 1600 NGN)
            # You may want to use a real-time conversion API in production
            usd_amount = float(pledge.amount)  # Convert Decimal to float
            ngn_amount = usd_amount * 1600  # Conversion rate
            
            # Initialize Paystack transaction (in kobo - smallest NGN unit)
            amount_in_kobo = int(ngn_amount * 100)  # Convert NGN to kobo
            
            headers = {
                "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
                "Content-Type": "application/json"
            }
            
            # Build callback URL with pledge ID
            callback_url = request.build_absolute_uri(
                reverse('pledge_payment_callback')
            ) + f"?pledge_id={pledge.id}"
            
            # Ensure all values are JSON serializable
            data = {
                "amount": amount_in_kobo,
                "email": request.user.email,
                "callback_url": callback_url,
                "currency": "NGN",  # Explicitly set currency to NGN
                "metadata": {
                    "pledge_id": str(pledge.id),  # Convert to string to be safe
                    "project_id": str(project.id),
                    "reward_id": str(pledge.reward.id) if pledge.reward else None,
                    "usd_amount": usd_amount,  # Already converted to float
                    "custom_fields": [
                        {
                            "display_name": "Project Name",
                            "variable_name": "project_name",
                            "value": project.title
                        }
                    ]
                }
            }
            
            # Initialize transaction
            url = "https://api.paystack.co/transaction/initialize"
            response = requests.post(url, headers=headers, data=json.dumps(data))
            
            if response.status_code == 200:
                response_data = response.json()
                # Redirect to Paystack payment page
                return redirect(response_data['data']['authorization_url'])
            else:
                # Handle error
                messages.error(request, "Payment initialization failed. Please try again.")
                pledge.delete()  # Remove the pledge since payment failed
                return redirect('project_detail', project_id=project.id)
    else:
        form = PledgeForm(project=project)
    
    return render(request, 'projects/pledge_form.html', {'form': form, 'project': project})


@login_required
def pledge_payment_callback(request):
    reference = request.GET.get('reference')
    pledge_id = request.GET.get('pledge_id')
    
    # Check if pledge_id is None or invalid
    if not pledge_id or pledge_id == 'None':
        # Handle the case where pledge_id is missing
        messages.warning(
            request, 
            "Payment was processed, but we couldn't find your pledge details. Please contact support."
        )
        # Redirect to a safe location
        return redirect('project_list')
    
    # Verify transaction
    url = f"https://api.paystack.co/transaction/verify/{reference}"
    headers = {"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"}
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        response_data = response.json()
        
        if response_data['data']['status'] == 'success':
            try:
                # Payment successful
                pledge = get_object_or_404(Pledge, id=pledge_id)
                project = pledge.project
                
                # Update project's amount_raised
                project.amount_raised += pledge.amount
                project.save()
                
                # Send confirmation email
                from .signals import send_pledge_confirmation_after_payment
                send_pledge_confirmation_after_payment(pledge)

                # Add success message
                messages.success(
                    request, 
                    f"Thank you for your generous donation of ${pledge.amount}! "
                    f"Your support helps make this project a reality."
                )
                
                return redirect('project_detail', project_id=project.id)
            except Exception as e:
                # Log the error for debugging
                print(f"Error processing pledge: {str(e)}")
                messages.error(
                    request,
                    "Your payment was successful, but we encountered an error updating your pledge. "
                    "Please contact support with reference: " + reference
                )
                return redirect('project_list')
        else:
            # Payment failed
            messages.error(request, "Payment verification failed. Please try again.")
            return redirect('project_list')
    else:
        # API call failed
        messages.error(request, "Payment verification failed. Please try again.")
        return redirect('project_list')


def about_page_view(request):
    try:
        content = AboutPage.objects.latest('last_updated')
    except AboutPage.DoesNotExist:
        content = None

    # Fetch all team members (you can order them however you want)
    team = TeamMember.objects.all().order_by('position')  # or 'id' or 'name'

    return render(request, 'about_page.html', {
        'content': content,
        'team': team,
    })

def incubator_accelerator_page_view(request):
    try:
        # Similar to AboutPage, fetch the single or latest IncubatorAcceleratorPage entry.
        content = IncubatorAcceleratorPage.objects.latest('last_updated')
    except IncubatorAcceleratorPage.DoesNotExist:
        content = None
    return render(request, 'incubator_accelerator_page.html', {'content': content})



def incubator_application_view(request):
    if request.method == 'POST':
        form = IncubatorApplicationForm(request.POST, request.FILES) 
        if form.is_valid():
            application = form.save(commit=False)

            # Optional: Link to logged-in user if model has a user FK
            # if request.user.is_authenticated:
            #     application.applicant_user = request.user

            application.save()
            messages.success(request, 'Your application has been submitted successfully!')
            return redirect('application_thank_you')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = IncubatorApplicationForm()

    return render(request, 'incubator_application_form.html', {'form': form})


def application_thank_you(request):
    return render(request, 'thank_you.html')


@login_required
def investment_proposal(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    terms = project.investment_terms.first()

    if not terms:
        messages.error(request, "No investment terms available for this project.")
        return redirect('project_detail', project_id=project.id)

    if request.method == 'POST':
        form = InvestmentForm(request.POST, terms=terms, project=project)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            agreement_form = InvestmentAgreementForm(user=request.user)
            
            return render(request, 'projects/investment_proposal.html', {
                'form': agreement_form,
                'project': project,
                'terms': terms,
                'amount': amount
            })
        else:
            messages.error(request, f"Form errors: {form.errors}")
            return redirect('project_detail', project_id=project.id)
    else:
        # If accessed directly, redirect to project detail
        return redirect('project_detail', project_id=project.id)

@login_required
def process_investment(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    terms = project.investment_terms.first()

    if not terms:
        messages.error(request, "No investment terms available for this project.")
        return redirect('project_detail', project_id=project.id)

    if request.method == 'POST':
        agreement_form = InvestmentAgreementForm(request.POST, user=request.user)
        
        if agreement_form.is_valid():
            try:
                amount = Decimal(request.POST.get('amount', 0))
                
                # Convert all values to Decimal to ensure consistent types
                funding_goal = Decimal(str(project.funding_goal))
                equity_offered = Decimal(str(terms.equity_offered))
                
                # Calculate percentages using consistent Decimal types
                investment_percentage = (amount / funding_goal) * Decimal('100.0')
                equity_percentage = (amount / funding_goal) * equity_offered
                
                # Calculate remaining available equity
                total_invested = project.investments.filter(status__in=['active', 'pending']).aggregate(
                    total=Coalesce(Sum('equity_percentage'), Decimal('0'))
                )['total'] or Decimal('0')
                
                available_equity = equity_offered - total_invested
                
                # Check if there's enough equity available
                if equity_percentage > available_equity:
                    messages.error(
                        request, 
                        f"Your investment would exceed the available equity. Maximum available: {available_equity:.2f}%"
                    )
                    return redirect('project_detail', project_id=project.id)
                
                with transaction.atomic():
                    # Create the investment with equity percentage
                    investment = Investment(
                        project=project,
                        investor=request.user,
                        terms=terms,
                        amount=amount,
                        equity_percentage=equity_percentage,
                        status='pending'
                    )
                    investment.save()
                    
                    # Convert USD to NGN - use float for API compatibility
                    usd_amount = float(amount)
                    ngn_amount = usd_amount * 1600
                    
                    # Initialize Paystack transaction
                    amount_in_kobo = int(ngn_amount * 100)
                    
                    headers = {
                        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
                        "Content-Type": "application/json"
                    }
                    
                    # Convert Decimal values to float for JSON serialization
                    investment_percentage_float = float(investment_percentage)
                    equity_percentage_float = float(equity_percentage)
                    equity_offered_float = float(equity_offered)
                    
                    data = {
                        "amount": amount_in_kobo,
                        "email": request.user.email,
                        "callback_url": request.build_absolute_uri(
                            reverse('investment_payment_callback')
                        ) + f"?investment_id={investment.id}",
                        "currency": "NGN",
                        "metadata": {
                            "investment_id": str(investment.id),
                            "project_id": str(project.id),
                            "usd_amount": usd_amount,
                            "equity_percentage": investment_percentage_float,  # Convert to float
                            "custom_fields": [
                                {
                                    "display_name": "Project Name",
                                    "variable_name": "project_name",
                                    "value": project.title
                                },
                                {
                                    "display_name": "Equity Offered",
                                    "variable_name": "equity_offered",
                                    "value": f"{investment_percentage_float:.2f}% of {equity_offered_float:.2f}%"
                                }
                            ]
                        }
                    }
                    
                    # Initialize transaction
                    url = "https://api.paystack.co/transaction/initialize"
                    response = requests.post(url, headers=headers, data=json.dumps(data))
                    
                    if response.status_code == 200:
                        response_data = response.json()
                        # Redirect to Paystack payment page
                        return redirect(response_data['data']['authorization_url'])
                    else:
                        # Handle error
                        messages.error(request, "Payment initialization failed. Please try again.")
                        investment.delete()
                        return redirect('project_detail', project_id=project.id)
            except Exception as e:
                messages.error(request, f"Error processing investment: {str(e)}")
                return redirect('project_detail', project_id=project.id)
        else:
            # If agreement form is invalid, show the form again
            amount = request.POST.get('amount', 0)
            return render(request, 'projects/investment_proposal.html', {
                'form': agreement_form,
                'project': project,
                'terms': terms,
                'amount': amount
            })
    else:
        # If accessed directly, redirect to project detail
        return redirect('project_detail', project_id=project.id)


@login_required
def make_investment(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    terms = project.investment_terms.first()

    if not terms:
        messages.error(request, "No investment terms available for this project.")
        return redirect('project_detail', project_id=project.id)

    if request.method == 'POST':
        # Check if this is coming from the proposal page
        if 'agree_to_terms' in request.POST and 'electronic_signature' in request.POST:
            # Create a form with all the data
            form_data = request.POST.copy()
            form = InvestmentForm(form_data, terms=terms, project=project)
            form.instance.investor = request.user
            
            if form.is_valid():
                try:
                    with transaction.atomic():
                        investment = form.save(commit=False)
                        investment.project = project
                        investment.investor = request.user
                        investment.terms = terms
                        investment.status = 'pending'
                        investment.save()
                        
                        # Convert USD to NGN (using a conversion rate of approximately 1 USD = 1600 NGN)
                        usd_amount = float(investment.amount)  # Convert Decimal to float
                        ngn_amount = usd_amount * 1600  # Conversion rate
                        
                        # Initialize Paystack transaction (in kobo - smallest NGN unit)
                        amount_in_kobo = int(ngn_amount * 100)  # Convert NGN to kobo
                        
                        headers = {
                            "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
                            "Content-Type": "application/json"
                        }
                        
                        data = {
                            "amount": amount_in_kobo,
                            "email": request.user.email,
                            "callback_url": request.build_absolute_uri(
                                reverse('investment_payment_callback')
                            ) + f"?investment_id={investment.id}",
                            "currency": "NGN",  # Explicitly set currency to NGN
                            "metadata": {
                                "investment_id": str(investment.id),  # Convert to string
                                "project_id": str(project.id),
                                "usd_amount": usd_amount,  # Already converted to float
                                "custom_fields": [
                                    {
                                        "display_name": "Project Name",
                                        "variable_name": "project_name",
                                        "value": project.title
                                    },
                                    {
                                        "display_name": "Equity Offered",
                                        "variable_name": "equity_offered",
                                        "value": f"{terms.equity_offered}%"
                                    }
                                ]
                            }
                        }
                        
                        # Initialize transaction
                        url = "https://api.paystack.co/transaction/initialize"
                        response = requests.post(url, headers=headers, data=json.dumps(data))
                        
                        if response.status_code == 200:
                            response_data = response.json()
                            # Redirect to Paystack payment page
                            return redirect(response_data['data']['authorization_url'])
                        else:
                            # Handle error
                            messages.error(request, "Payment initialization failed. Please try again.")
                            investment.delete()  # Remove the investment since payment failed
                            return redirect('project_detail', project_id=project.id)
                except Exception as e:
                    messages.error(request, f"Error processing investment: {str(e)}")
                    return redirect('project_detail', project_id=project.id)
            else:
                messages.error(request, f"Form errors: {form.errors}")
                return render(request, 'projects/investment_proposal.html', {
                    'form': form,
                    'project': project,
                    'terms': terms,
                    'amount': form_data.get('amount')
                })
        else:
            # This is the initial form from project detail
            return redirect('investment_proposal', project_id=project.id)
    else:
        # GET request - show the initial form
        form = InvestmentForm(terms=terms, project=project)
        return render(request, 'projects/investment_detail.html', {'form': form, 'project': project})






def activate_investment(request, investment_id):
    investment = get_object_or_404(Investment, pk=investment_id)

    if investment.status != 'active':
        with transaction.atomic():
            # Lock investment for safe update
            investment = Investment.objects.select_for_update().get(pk=investment_id)

            if investment.status != 'active':
                investment.status = 'active'
                investment.save()

                # Update project's amount_raised ONLY when activating
                project = investment.project
                project.amount_raised += investment.amount
                
                # Update available equity if equity_percentage exists
                if hasattr(investment, 'equity_percentage'):
                    # You might need to add an available_equity field to your Project model
                    # or calculate it on the fly when needed
                    project.save()
                else:
                    project.save()

                messages.success(request, "Investment marked as active and project updated.")
            else:
                messages.info(request, "Investment is already active.")
            if not investment.id:
                messages.error(request, "Investment ID is missing. Cannot proceed.")
                return redirect('project_detail', project_id=investment.project.id)
    else:
        messages.info(request, "Investment is already active.")

    return redirect('investment_detail', pk=investment.id)



class MyInvestmentsView(LoginRequiredMixin, ListView):
    model = Investment
    template_name = 'projects/my_investments.html'  # Create this template
    context_object_name = 'investments'

    def get_queryset(self):
        # Fetch investments made by the logged-in user
        return Investment.objects.filter(investor=self.request.user)


class InvestmentDetailView(LoginRequiredMixin, DetailView):
    model = Investment
    template_name = 'projects/investment_detail.html'
    context_object_name = 'investment'

    def get_object(self):
        investment_id = self.kwargs.get('pk')
        return get_object_or_404(Investment, pk=investment_id)
#################################

@login_required
def dashboard(request):
    user = request.user
    now = timezone.now()
    
    # Common context data
    context = {
        'now': now,
    }
    
    # Founder-specific data
    if user.user_type == 'founder':
        # Show all projects to the creator, regardless of status
        created_projects = Project.objects.filter(creator=user).annotate(
            percent_funded=ExpressionWrapper(
                (F('amount_raised') * 100.0) / F('funding_goal'),
                output_field=FloatField()
            )
        )
        
        # Count pending projects
        pending_projects = created_projects.filter(status='pending').count()
        
        # Only count approved projects in the active projects count
        active_projects = created_projects.filter(
            status='approved',
            deadline__gte=now
        ).count()
        
        total_projects = created_projects.count()
        total_raised = created_projects.aggregate(Sum('amount_raised'))['amount_raised__sum'] or 0
        
        # Calculate average funding percentage
        funded_projects = created_projects.filter(amount_raised__gt=0)
        if funded_projects.exists():
            avg_funding = funded_projects.aggregate(
                avg=Avg('percent_funded')
            )['avg'] or 0
        else:
            avg_funding = 0
        
        context.update({
            'created_projects': created_projects,
            'total_projects': total_projects,
            'active_projects': active_projects,
            'pending_projects': pending_projects,
            'total_raised': total_raised,
            'avg_funding': avg_funding,
        })
    
    # Get user's pledges
    pledges = Pledge.objects.filter(backer=user).select_related('project', 'reward')
    context['pledges'] = pledges
    
    # Get user's investments with equity percentage calculation
    investments = Investment.objects.filter(investor=user).select_related('project', 'terms')
    
    # Ensure each investment has the correct equity percentage
    for investment in investments:
        if not investment.equity_percentage:
            # Calculate if not already set
            funding_percentage = (investment.amount / investment.project.funding_goal) * 100
            investment.equity_percentage = (funding_percentage / 100) * investment.terms.equity_offered
            investment.save()
    
    context['investments'] = investments
    
    # Recommended projects for investors
    if user.user_type == 'investor':
        # Get investor's preferred industries if available
        preferred_industries = []
        if hasattr(user, 'investorprofile') and user.investorprofile.preferred_industries:
            preferred_industries = user.investorprofile.preferred_industries.split(',')
            preferred_industries = [industry.strip() for industry in preferred_industries]
        
        # Get projects that match investor's preferences
        recommended_projects = Project.objects.filter(
            deadline__gte=now
        ).exclude(
            investments__investor=user
        ).annotate(
            percent_funded=ExpressionWrapper(
                (F('amount_raised') * 100.0) / F('funding_goal'),
                output_field=FloatField()
            )
        ).order_by('-created_at')[:6]
        
        context['recommended_projects'] = recommended_projects
    
    return render(request, 'dashboard.html', context)


def get_recommended_projects(user):
    # Implementation from previous investor_dashboard view
    try:
        investor_profile = InvestorProfile.objects.get(user=user)
        preferred_industries = investor_profile.preferred_industries.split(',')
    except InvestorProfile.DoesNotExist:
        preferred_industries = []
    
    recommended_projects = Project.objects.filter(
        funding_type__name='Equity',
        deadline__gte=timezone.now(),
        investment_terms__isnull=False
    ).exclude(
        investments__investor=user
    ).annotate(
        num_investors=Count('investments')
    ).select_related('category').distinct()
    
    if preferred_industries:
        recommended_projects = recommended_projects.filter(
            Q(category__name__in=preferred_industries) |
            Q(title__icontains=preferred_industries[0])
        )[:6]
    else:
        recommended_projects = recommended_projects[:6]
    
    return recommended_projects



def complete_profile(request):
    if not request.user.is_authenticated:
        return redirect('login')
    
    user = request.user
    profile_forms = {
        'founder': FounderProfileForm,
        'investor': InvestorProfileForm,
    }
    
    if request.method == 'POST':
        base_form = BaseProfileForm(request.POST, instance=user)
        specific_form = None
        
        if user.user_type in profile_forms:
            specific_form = profile_forms[user.user_type](
                request.POST, 
                instance=user.founderprofile if user.user_type == 'founder' else user.investorprofile
            )
        
        if base_form.is_valid() and (specific_form.is_valid() if specific_form else True):
            base_form.save()
            if specific_form:
                specific_form.save()
            user.profile_completed = True
            user.save()
            return redirect('dashboard')
    else:
        base_form = BaseProfileForm(instance=user)
        specific_form = None
        if user.user_type in profile_forms:
            try:
                instance = user.founderprofile if user.user_type == 'founder' else user.investorprofile
            except:
                instance = None
            specific_form = profile_forms[user.user_type](instance=instance)

    return render(request, 'projects/complete_profile.html', {
        'base_form': base_form,
        'specific_form': specific_form,
        'user_type': user.user_type
    })



def founder_dashboard(request):
    if not request.user.is_authenticated or not request.user.is_founder:
        return redirect('login')
    
    founder = request.user
    projects = Project.objects.filter(creator=founder).annotate(
        calculated_percent=ExpressionWrapper(
            F('amount_raised') / F('funding_goal') * 100,
            output_field=FloatField()
        ),
        days_remaining=ExpressionWrapper(
            F('deadline') - timezone.now(),
            output_field=DurationField()
        )
    ).order_by('-created_at')
    
    try:
        profile = founder.founderprofile
    except FounderProfile.DoesNotExist:
        profile = None
    
    # Project statistics
    total_projects = projects.count()
    active_projects = projects.filter(deadline__gte=timezone.now()).count()
    total_raised = projects.aggregate(Sum('amount_raised'))['amount_raised__sum'] or 0
    avg_funding = projects.aggregate(Avg('percent_funded'))['percent_funded__avg'] or 0
    
    # Recent activity
    recent_pledges = Pledge.objects.filter(
        project__in=projects
    ).select_related('project', 'backer').order_by('-pledged_at')[:5]
    
    recent_investments = Investment.objects.filter(
        project__in=projects
    ).select_related('project', 'investor').order_by('-created_at')[:5]

    context = {
        'founder': founder,
        'profile': profile,
        'projects': projects,
        'total_projects': total_projects,
        'active_projects': active_projects,
        'total_raised': total_raised,
        'avg_funding': avg_funding,
        'recent_pledges': recent_pledges,
        'recent_investments': recent_investments,
    }
    return render(request, 'dashboard/founder_dashboard.html', context)



@login_required
def investor_dashboard(request):
    if not request.user.is_authenticated or request.user.user_type != 'investor':
        return redirect('login')
    
    investor = request.user
    investments = Investment.objects.filter(investor=investor).select_related(
        'project', 'terms'
    ).order_by('-created_at')
    
    # Calculate statistics
    total_invested = investments.aggregate(total=Sum('amount'))['total'] or 0
    active_investments = investments.filter(terms__deadline__gte=timezone.now()).count()
    
    # Average equity percentage from investments
    avg_return = investments.aggregate(avg_equity=Avg('terms__equity_offered'))['avg_equity'] or 0
    
    # Calculate potential ROI (simplified example)
    potential_roi = sum(
        investment.amount * (investment.terms.equity_offered / 100)
        for investment in investments.filter(status='accepted')
    ) or 0

    # Get recommended projects
    try:
        investor_profile = InvestorProfile.objects.get(user=investor)
        preferred_industries = investor_profile.preferred_industries.split(',')
    except InvestorProfile.DoesNotExist:
        preferred_industries = []
    
    recommended_projects = Project.objects.filter(
        funding_type__name='Equity',
        deadline__gte=timezone.now(),
        investment_terms__isnull=False
    ).exclude(
        investments__investor=investor
    ).annotate(
        num_investors=Count('investments')
    ).select_related('category').distinct()
    
    if preferred_industries:
        recommended_projects = recommended_projects.filter(
            Q(category__name__in=preferred_industries) |
            Q(title__icontains=preferred_industries[0])
        )[:6]
    else:
        recommended_projects = recommended_projects[:6]

    context = {
        'total_invested': total_invested,
        'active_investments': active_investments,
        'avg_return': avg_return,
        'potential_roi': potential_roi,
        'investments': investments,
        'recommended_projects': recommended_projects,
        'investor_profile': investor_profile if 'investor_profile' in locals() else None,
    }
    
    return render(request, 'dashboard/investor_dashboard.html', context)


@login_required
def investment_payment_callback(request):
    reference = request.GET.get('reference')
    investment_id = request.GET.get('investment_id')
    
    # Check if investment_id is None or invalid
    if not investment_id or investment_id == 'None':
        # Handle the case where investment_id is missing
        messages.warning(
            request, 
            "Payment was processed, but we couldn't find your investment details. Please contact support."
        )
        # Redirect to a safe location
        return redirect('project_list')
    
    # Verify transaction
    url = f"https://api.paystack.co/transaction/verify/{reference}"
    headers = {"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"}
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        response_data = response.json()
        
        if response_data['data']['status'] == 'success':
            try:
                # Payment successful
                investment = get_object_or_404(Investment, id=investment_id)
                
                # Update investment status
                investment.status = 'active'
                investment.save()
                
                # Update project's amount_raised
                project = investment.project
                project.amount_raised += investment.amount
                project.save()
                
                # Send confirmation email
                from .signals import notify_founder_new_investment_after_payment
                notify_founder_new_investment_after_payment(investment)

                # Add success message
                messages.success(
                    request, 
                    f"Your investment of ${investment.amount} was successful! "
                    f"You now own {investment.terms.equity_offered}% equity in this project."
                )
                
                return redirect('project_detail', project_id=project.id)
            except Exception as e:
                # Log the error for debugging
                print(f"Error processing investment: {str(e)}")
                messages.error(
                    request,
                    "Your payment was successful, but we encountered an error updating your investment. "
                    "Please contact support with reference: " + reference
                )
                return redirect('project_list')
        else:
            # Payment failed
            messages.error(request, "Payment verification failed. Please try again.")
            return redirect('project_list')
    else:
        # API call failed
        messages.error(request, "Payment verification failed. Please try again.")
        return redirect('project_list')