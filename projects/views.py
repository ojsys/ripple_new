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
import stripe
from django.conf import settings
from django.contrib import messages
from django.db import transaction
from django.db.models import Count, Sum, Avg, DurationField, Q, ExpressionWrapper, F, FloatField, DecimalField
from django.db.models.functions import Coalesce
from datetime import datetime
from decimal import Decimal
from django import forms
from .models import (Project, FundingType, InvestmentTerm, Investment, Pledge, 
                     Reward, Category, FounderProfile, InvestorProfile, HeroSlider)
from .forms import (ProjectForm, RewardForm, InvestmentTermForm, InvestmentForm, EditProfileForm,
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

##### Edit/Updates ##########

@login_required
def edit_profile(request):
    user = request.user

    # Get or create FounderProfile if user is a founder
    founder_profile = None
    if user.user_type == 'founder':
        founder_profile, created = FounderProfile.objects.get_or_create(user=user)

    if request.method == 'POST':
        user_form = EditProfileForm(request.POST, instance=user)
        founder_form = FounderProfileForm(request.POST, request.FILES, instance=founder_profile) if founder_profile else None

        if user_form.is_valid() and (founder_form is None or founder_form.is_valid()):
            user_form.save()
            if founder_form:
                founder_form.save()

            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('edit_profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        user_form = EditProfileForm(instance=user)
        founder_form = FounderProfileForm(instance=founder_profile) if founder_profile else None

    context = {
        'user_form': user_form,
        'founder_form': founder_form
    }
    return render(request, 'projects/edit_profile.html', context)


@login_required
def edit_project(request, pk):
    project = get_object_or_404(Project, pk=pk, creator=request.user)

    if request.method == 'POST':
        form = ProjectForm(request.POST, request.FILES, instance=project)
        if form.is_valid():
            form.save()
            return redirect('project_detail', pk=project.pk)
    else:
        form = ProjectForm(instance=project)

    return render(request, 'projects/edit_project.html', {'form': form, 'project': project})


######################

def home(request):
    sliders = HeroSlider.objects.filter(is_active=True)
    featured_projects = Project.objects.all()[:3]  # Replace with logic to fetch featured projects
    return render(request, 'projects/home.html', {
        'sliders': sliders,
        'featured_projects': featured_projects
        })


def project_detail(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    percent_funded = (project.amount_raised / project.funding_goal) * 100
    return render(request, 'projects/project_detail.html', {'project': project, 'percent_funded': percent_funded})


def project_list(request):
    projects = Project.objects.all().order_by('-created_at')
    
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


def make_investment(request, project_id):
    project = get_object_or_404(Project, pk=project_id)

    if request.method == 'POST':
        amount = request.POST.get('amount')
        investor = request.user

        # Save the investment as 'pending' or 'inactive' initially
        investment = Investment.objects.create(
            project=project,
            investor=investor,
            amount=amount,
            status='pending'  # or 'inactive' based on your model
        )

        messages.success(request, "Investment submitted and awaiting activation.")
        return redirect('investment_detail', pk=investment.id)

    return render(request, 'projects/make_investment.html', {'project': project})


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
                project.save()

                messages.success(request, "Investment marked as active and project updated.")
            else:
                messages.info(request, "Investment is already active.")
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

def dashboard(request):
    if not request.user.is_authenticated:
        return redirect('login')
    
    context = {}
    user = request.user
    
    # Common data for all users
    context['pledges'] = Pledge.objects.filter(backer=user).select_related('project')
    context['investments'] = Investment.objects.filter(investor=user).select_related('project')
    
    # Founder-specific data
    if user.user_type == 'founder':
        projects = Project.objects.filter(creator=user).annotate(
            calculated_percent=ExpressionWrapper(
                F('amount_raised') / F('funding_goal') * 100,
                output_field=FloatField()
            )
        )
        
        context.update({
            'created_projects': projects,
            'total_projects': projects.count(),
            'active_projects': projects.filter(deadline__gte=timezone.now()).count(),
            'total_raised': projects.aggregate(Sum('amount_raised'))['amount_raised__sum'] or 0,
            'avg_funding': projects.aggregate(Avg('calculated_percent'))['calculated_percent__avg'] or 0
        })

    # Investor-specific data
    elif user.user_type == 'investor':
        investments = context['investments']
        
        # Investment statistics
        context.update({
            'total_invested': investments.aggregate(total=Sum('amount'))['total'] or 0,
            'active_investments': investments.filter(terms__deadline__gte=timezone.now()).count(),
            'avg_return': investments.aggregate(avg=Avg('terms__equity_offered'))['avg'] or 0,
            'potential_roi': sum(
                inv.amount * (inv.terms.equity_offered / 100)
                for inv in investments.filter(status='accepted')
            ) or 0,
            'recommended_projects': get_recommended_projects(user)  # Implement this function
        })

    # Donor-specific data can be added here
    elif user.user_type == 'donor':
        # Add donor-specific context
        pass

    template_map = {
        'founder': 'dashboard/founder_dashboard.html',
        'donor': 'dashboard/donor_dashboard.html',
        'investor': 'dashboard/investor_dashboard.html',
    }
    
    return render(request, template_map.get(user.user_type, 'dashboard.html'), context)


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