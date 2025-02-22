from django.contrib.auth import login, logout
from django.contrib.auth.views import LogoutView
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_GET
from django.http import HttpResponseBadRequest
import stripe
from django.conf import settings
from django.db.models import Q, ExpressionWrapper, F, FloatField
from django import forms
from .models import (Project, FundingType, InvestmentTerm, Investment, Pledge, 
                     Reward, Category, FounderProfile, InvestorProfile)
from .forms import (ProjectForm, RewardForm, InvestmentTermForm, InvestmentForm, 
                    PledgeForm, SignUpForm, BaseProfileForm, FounderProfileForm, InvestorProfileForm)


stripe.api_key = settings.STRIPE_SECRET_KEY


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





def home(request):
    featured_projects = Project.objects.all()[:3]  # Replace with logic to fetch featured projects
    return render(request, 'projects/home.html', {'featured_projects': featured_projects})


def project_detail(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    percent_funded = (project.amount_raised / project.funding_goal) * 100
    return render(request, 'projects/project_detail.html', {'project': project, 'percent_funded': percent_funded})


def project_list(request):
    projects = Project.objects.all()
    
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
            project.save()
            return redirect('add_terms_rewards', project.id)
    else:
        form = ProjectForm()
    return render(request, 'projects/create_project.html', {'form': form})



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


@login_required
def make_pledge(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if request.method == 'POST':
        form = PledgeForm(request.POST, project=project)
        if form.is_valid():
            try:
                # Stripe Charge
                charge = stripe.Charge.create(
                    amount=int(form.cleaned_data['amount'] * 100),
                    currency='usd',
                    source=request.POST['stripeToken'],
                    description=f'Pledge for {project.title}'
                )
                
                # Save Pledge
                pledge = form.save(commit=False)
                pledge.project = project
                pledge.backer = request.user
                pledge.save()
                
                # Update Project
                project.amount_raised += pledge.amount
                project.save()
                
                return redirect('pledge_success', pledge.id)
                
            except stripe.error.StripeError as e:
                form.add_error(None, f'Payment error: {e.user_message}')
    
    # Render form with errors
    return render(request, 'project_detail.html', {
        'project': project,
        'pledge_form': form
    })


# Project Detail Page
def project_detail(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    context = {
        'project': project,
        'percent_funded': (project.amount_raised / project.funding_goal) * 100,
    }
    
    # Add investment/pledge forms based on funding type
    if project.funding_type.name == 'Equity':
        context['investment_form'] = InvestmentForm(terms=project.investment_terms.all())
    elif project.funding_type.name == 'Donation':
        context['pledge_form'] = PledgeForm(project=project)
    
    return render(request, 'projects/project_detail.html', context)

# Investment/Pledge Handling
@login_required
def make_investment(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if request.method == 'POST':
        form = InvestmentForm(request.POST, terms=project.investment_terms.all())
        if form.is_valid():
            investment = form.save(commit=False)
            investment.project = project
            investment.investor = request.user
            investment.save()
            project.total_investment_raised += investment.amount
            project.save()
            return redirect('project_detail', project.id)

@login_required
def make_pledge(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if request.method == 'POST':
        form = PledgeForm(request.POST, project=project)
        if form.is_valid():
            pledge = form.save(commit=False)
            pledge.project = project
            pledge.backer = request.user
            pledge.save()
            project.amount_raised += pledge.amount
            project.save()
            return redirect('project_detail', project.id)

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


def dashboard(request):
    if not request.user.is_authenticated:
        return redirect('login')
    
    context = {}
    user = request.user
    
    # Common data for all user types
    context['pledges'] = Pledge.objects.filter(backer=user).select_related('project')
    context['investments'] = Investment.objects.filter(investor=user).select_related('project')
    
    # User-type specific data
    if user.user_type == 'founder':
        context['created_projects'] = Project.objects.filter(creator=user).annotate(
            percent_funded=ExpressionWrapper(
                F('amount_raised') / F('funding_goal') * 100,
                output_field=FloatField()
            )
        )

    template_map = {
        'founder': 'dashboard/founder_dashboard.html',
        'donor': 'dashboard/donor_dashboard.html',
        'investor': 'dashboard/investor_dashboard.html',
    }
    
    return render(request, template_map.get(user.user_type, 'dashboard.html'), context)


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





