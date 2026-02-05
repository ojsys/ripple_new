from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.conf import settings
import requests
import uuid

from .models import Project, Category, FundingType, Reward, Update, Donation, PaymentAttempt
from .forms import ProjectForm, RewardForm, RewardFormSet, UpdateForm, DonationForm, InvestmentForm
from apps.funding.models import Investment, InvestmentTerm
from apps.cms.models import (
    HeroSlider, Testimonial, HomePage, PartnerLogo,
    SiteSettings, Announcement, NewsletterSubscriber
)


def home(request):
    """Homepage view with featured projects and CMS content."""
    # Load CMS content
    homepage = HomePage.load()
    site_settings = SiteSettings.load() if SiteSettings.objects.exists() else None

    # Get active announcements
    from django.utils import timezone
    announcements = Announcement.objects.filter(
        is_active=True,
        start_date__lte=timezone.now(),
        end_date__gte=timezone.now()
    )

    # Featured projects
    featured_projects = Project.objects.filter(status='approved').order_by('-created_at')[:6]

    # Testimonials
    testimonials = Testimonial.objects.filter(is_active=True)[:6]

    # Partner logos
    partner_logos = PartnerLogo.objects.filter(is_active=True)

    # Categories for navigation
    categories = Category.objects.all()

    # Hero sliders (if using slider instead of static hero)
    sliders = HeroSlider.objects.filter(is_active=True)

    context = {
        'homepage': homepage,
        'site_settings': site_settings,
        'announcements': announcements,
        'featured_projects': featured_projects,
        'testimonials': testimonials,
        'partner_logos': partner_logos,
        'categories': categories,
        'sliders': sliders,
        'how_it_works_steps': homepage.how_it_works_steps.all() if homepage else [],
    }
    return render(request, 'home.html', context)


def subscribe_newsletter(request):
    """Handle newsletter subscription."""
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        if email:
            try:
                NewsletterSubscriber.objects.get_or_create(email=email)
                messages.success(request, 'Thank you for subscribing to our newsletter!')
            except Exception:
                messages.error(request, 'An error occurred. Please try again.')
        else:
            messages.error(request, 'Please enter a valid email address.')
    return redirect('projects:home')


def project_list(request):
    """List all approved projects with filtering and pagination."""
    projects = Project.objects.filter(status='approved').order_by('-created_at')
    categories = Category.objects.all()
    funding_types = FundingType.objects.all()

    # Filter by category
    category_id = request.GET.get('category')
    if category_id:
        projects = projects.filter(category_id=category_id)

    # Filter by funding type
    funding_type_id = request.GET.get('funding_type')
    if funding_type_id:
        projects = projects.filter(funding_type_id=funding_type_id)

    # Search
    search_query = request.GET.get('q')
    if search_query:
        projects = projects.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(short_description__icontains=search_query)
        )

    # Sort
    sort_by = request.GET.get('sort', 'newest')
    if sort_by == 'newest':
        projects = projects.order_by('-created_at')
    elif sort_by == 'oldest':
        projects = projects.order_by('created_at')
    elif sort_by == 'most_funded':
        projects = projects.order_by('-amount_raised')
    elif sort_by == 'ending_soon':
        projects = projects.filter(deadline__gt=timezone.now()).order_by('deadline')

    # Pagination
    paginator = Paginator(projects, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'projects': page_obj,
        'categories': categories,
        'funding_types': funding_types,
        'current_category': category_id,
        'current_funding_type': funding_type_id,
        'search_query': search_query,
        'sort_by': sort_by,
    }
    return render(request, 'projects/project_list.html', context)


def project_detail(request, project_id):
    """Display project details."""
    project = get_object_or_404(Project, id=project_id)

    # Calculate percent funded
    percent_funded = project.get_percent_funded()

    # Initialize forms based on funding type
    pledge_form = None
    investment_form = None

    if project.funding_type and project.funding_type.name == 'Donation':
        pledge_form = DonationForm(project=project)
    elif project.funding_type and project.funding_type.name == 'Equity':
        investment_form = InvestmentForm(project=project)

    # Get backers count
    backers_count = project.donations.filter(status='completed').count()

    context = {
        'project': project,
        'percent_funded': percent_funded,
        'pledge_form': pledge_form,
        'investment_form': investment_form,
        'backers_count': backers_count,
    }
    return render(request, 'projects/project_detail.html', context)


@login_required
def create_project(request):
    """Create a new project (for founders)."""
    if request.user.user_type != 'founder':
        messages.error(request, 'Only founders can create projects.')
        return redirect('projects:project_list')

    # Ensure funding types exist
    ensure_funding_types_exist()

    if request.method == 'POST':
        form = ProjectForm(request.POST, request.FILES)
        reward_formset = RewardFormSet(request.POST, prefix='rewards')

        if form.is_valid() and reward_formset.is_valid():
            project = form.save(commit=False)
            project.creator = request.user
            project.status = 'pending'
            project.save()

            # Save rewards
            reward_formset.instance = project
            reward_formset.save()

            messages.success(request, 'Your project has been submitted for review!')
            return redirect('projects:my_projects')
    else:
        form = ProjectForm()
        reward_formset = RewardFormSet(prefix='rewards')

    # Get all categories for the add category feature
    categories = Category.objects.all().order_by('name')

    context = {
        'form': form,
        'reward_formset': reward_formset,
        'title': 'Create Project',
        'categories': categories,
    }
    return render(request, 'projects/project_form.html', context)


@login_required
def edit_project(request, project_id):
    """Edit an existing project."""
    project = get_object_or_404(Project, id=project_id, creator=request.user)

    # Ensure funding types exist
    ensure_funding_types_exist()

    if request.method == 'POST':
        form = ProjectForm(request.POST, request.FILES, instance=project)
        reward_formset = RewardFormSet(request.POST, instance=project, prefix='rewards')

        if form.is_valid() and reward_formset.is_valid():
            form.save()
            reward_formset.save()
            messages.success(request, 'Project updated successfully!')
            return redirect('projects:project_detail', project_id=project.id)
    else:
        form = ProjectForm(instance=project)
        reward_formset = RewardFormSet(instance=project, prefix='rewards')

    # Get all categories for the add category feature
    categories = Category.objects.all().order_by('name')

    context = {
        'form': form,
        'reward_formset': reward_formset,
        'project': project,
        'title': 'Edit Project',
        'categories': categories,
    }
    return render(request, 'projects/project_form.html', context)


@login_required
def delete_project(request, project_id):
    """Delete a project."""
    project = get_object_or_404(Project, id=project_id, creator=request.user)

    if request.method == 'POST':
        project.delete()
        messages.success(request, 'Project deleted successfully.')
        return redirect('projects:my_projects')

    context = {
        'project': project,
    }
    return render(request, 'projects/project_confirm_delete.html', context)


@login_required
def my_projects(request):
    """List user's own projects."""
    projects = Project.objects.filter(creator=request.user).order_by('-created_at')

    context = {
        'projects': projects,
    }
    return render(request, 'projects/my_projects.html', context)


@login_required
def add_reward(request, project_id):
    """Add a reward to a project."""
    project = get_object_or_404(Project, id=project_id, creator=request.user)

    if request.method == 'POST':
        form = RewardForm(request.POST)
        if form.is_valid():
            reward = form.save(commit=False)
            reward.project = project
            reward.save()
            messages.success(request, 'Reward added successfully!')
            return redirect('projects:edit_project', project_id=project.id)
    else:
        form = RewardForm()

    context = {
        'form': form,
        'project': project,
    }
    return render(request, 'projects/reward_form.html', context)


@login_required
def add_update(request, project_id):
    """Post an update to a project."""
    project = get_object_or_404(Project, id=project_id, creator=request.user)

    if request.method == 'POST':
        form = UpdateForm(request.POST)
        if form.is_valid():
            update = form.save(commit=False)
            update.project = project
            update.save()
            messages.success(request, 'Update posted successfully!')
            return redirect('projects:project_detail', project_id=project.id)
    else:
        form = UpdateForm()

    context = {
        'form': form,
        'project': project,
    }
    return render(request, 'projects/update_form.html', context)


@login_required
def make_pledge(request, project_id):
    """Initialize a donation/pledge to a project."""
    project = get_object_or_404(Project, id=project_id)

    # Check if project is approved
    if project.status != 'approved':
        messages.error(request, 'This project is not yet approved for funding. Please check back later.')
        return redirect('projects:project_detail', project_id=project.id)

    if project.deadline < timezone.now():
        messages.error(request, 'This project has ended.')
        return redirect('projects:project_detail', project_id=project.id)

    # Get pre-populated values from URL parameters
    initial_data = {}
    pre_amount = request.GET.get('amount')
    pre_reward = request.GET.get('reward')

    if pre_amount:
        try:
            initial_data['amount'] = float(pre_amount)
        except (ValueError, TypeError):
            pass

    if pre_reward:
        try:
            initial_data['reward'] = int(pre_reward)
        except (ValueError, TypeError):
            pass

    if request.method == 'POST':
        form = DonationForm(request.POST, project=project)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            amount_ngn = int(float(amount) * 1600)  # Convert to NGN
            reference = f"DON-{uuid.uuid4().hex[:16].upper()}"

            # Create a payment attempt (NOT a donation yet)
            payment_attempt = PaymentAttempt.objects.create(
                project=project,
                user=request.user,
                amount=amount,
                amount_ngn=amount_ngn,
                reward=form.cleaned_data.get('reward'),
                message=form.cleaned_data.get('message'),
                is_anonymous=form.cleaned_data.get('is_anonymous', False),
                paystack_reference=reference,
                status='pending'
            )

            # Initialize Paystack payment
            paystack_secret = getattr(settings, 'PAYSTACK_SECRET_KEY', '')

            # Check if Paystack key is configured
            if not paystack_secret:
                messages.error(request, 'Payment system is not configured. Please contact support.')
                payment_attempt.status = 'failed'
                payment_attempt.error_message = 'Paystack secret key not configured'
                payment_attempt.save()
                return redirect('projects:make_pledge', project_id=project.id)

            headers = {
                'Authorization': f'Bearer {paystack_secret}',
                'Content-Type': 'application/json'
            }
            data = {
                'email': request.user.email,
                'amount': amount_ngn * 100,  # Paystack uses kobo
                'reference': reference,
                'callback_url': request.build_absolute_uri('/projects/donation/callback/'),
                'metadata': {
                    'payment_attempt_id': payment_attempt.id,
                    'project_id': project.id,
                }
            }

            try:
                response = requests.post(
                    'https://api.paystack.co/transaction/initialize',
                    json=data,
                    headers=headers,
                    timeout=30
                )

                if response.status_code == 200:
                    result = response.json()
                    if result.get('status'):
                        return redirect(result['data']['authorization_url'])
                    else:
                        payment_attempt.status = 'failed'
                        payment_attempt.error_message = result.get('message', 'Unknown error')
                        payment_attempt.save()
                        messages.error(request, f'Payment error: {result.get("message", "Unknown error")}')
                else:
                    result = response.json() if response.text else {}
                    error_msg = result.get('message', f'Status {response.status_code}')
                    payment_attempt.status = 'failed'
                    payment_attempt.error_message = error_msg
                    payment_attempt.save()
                    messages.error(request, f'Payment service error: {error_msg}')

            except requests.exceptions.Timeout:
                payment_attempt.status = 'failed'
                payment_attempt.error_message = 'Payment service timed out'
                payment_attempt.save()
                messages.error(request, 'Payment service timed out. Please try again.')
            except requests.exceptions.RequestException as e:
                payment_attempt.status = 'failed'
                payment_attempt.error_message = str(e)
                payment_attempt.save()
                messages.error(request, f'Connection error. Please try again.')
    else:
        form = DonationForm(project=project, initial=initial_data)

    # Get selected reward info for display
    selected_reward = None
    if pre_reward:
        try:
            selected_reward = Reward.objects.get(id=pre_reward, project=project)
        except Reward.DoesNotExist:
            pass

    context = {
        'form': form,
        'project': project,
        'selected_reward': selected_reward,
        'pre_amount': pre_amount,
    }
    return render(request, 'projects/make_pledge.html', context)


def donation_callback(request):
    """Handle Paystack callback for donations."""
    reference = request.GET.get('reference')

    if not reference:
        messages.error(request, 'Invalid payment reference.')
        return redirect('projects:project_list')

    # Find the payment attempt
    try:
        payment_attempt = PaymentAttempt.objects.get(paystack_reference=reference)
    except PaymentAttempt.DoesNotExist:
        # Fallback: check if there's a legacy Donation record
        try:
            donation = Donation.objects.get(paystack_reference=reference)
            if donation.status == 'completed':
                messages.success(request, 'This donation was already processed.')
                return redirect('projects:project_detail', project_id=donation.project.id)
        except Donation.DoesNotExist:
            pass
        messages.error(request, 'Payment reference not found.')
        return redirect('projects:project_list')

    # Verify payment with Paystack
    paystack_secret = getattr(settings, 'PAYSTACK_SECRET_KEY', '')
    headers = {'Authorization': f'Bearer {paystack_secret}'}

    try:
        response = requests.get(
            f'https://api.paystack.co/transaction/verify/{reference}',
            headers=headers,
            timeout=30
        )
    except requests.exceptions.RequestException:
        # Network error during verification - keep as pending so it can be retried
        messages.error(request, 'Could not verify payment. If you were charged, please contact support.')
        return redirect('projects:project_detail', project_id=payment_attempt.project.id)

    if response.status_code == 200:
        result = response.json()
        if result.get('status') and result['data']['status'] == 'success':
            # Payment was successful - create the actual Donation record
            if payment_attempt.status != 'success':
                donation = Donation.objects.create(
                    project=payment_attempt.project,
                    donor=payment_attempt.user,
                    amount=payment_attempt.amount,
                    amount_ngn=payment_attempt.amount_ngn,
                    reward=payment_attempt.reward,
                    message=payment_attempt.message,
                    is_anonymous=payment_attempt.is_anonymous,
                    paystack_reference=reference,
                    status='completed'
                )

                # Link the payment attempt to the donation
                payment_attempt.status = 'success'
                payment_attempt.donation = donation
                payment_attempt.save()

                # Recalculate project funding from all completed donations
                payment_attempt.project.recalculate_funding()

            messages.success(request, 'Thank you for your donation!')
            return redirect('projects:project_detail', project_id=payment_attempt.project.id)
        else:
            # Payment failed at Paystack
            payment_attempt.status = 'failed'
            payment_attempt.error_message = result['data'].get('gateway_response', 'Payment was not successful')
            payment_attempt.save()
            messages.error(request, 'Payment was not successful. No charges have been applied.')
            return redirect('projects:project_detail', project_id=payment_attempt.project.id)

    messages.error(request, 'Payment verification failed. If you were charged, please contact support.')
    return redirect('projects:project_detail', project_id=payment_attempt.project.id)


@login_required
def investment_proposal(request, project_id):
    """Submit an investment for an equity project."""
    project = get_object_or_404(Project, id=project_id)

    # Check if project is approved
    if project.status != 'approved':
        messages.error(request, 'This project is not yet approved for investment. Please check back later.')
        return redirect('projects:project_detail', project_id=project.id)

    if request.user.user_type != 'investor':
        messages.error(request, 'Only investors can submit investments.')
        return redirect('projects:project_detail', project_id=project.id)

    if request.method == 'POST':
        form = InvestmentForm(request.POST, project=project)
        if form.is_valid():
            investment = form.save(commit=False)
            investment.project = project
            investment.investor = request.user
            investment.status = 'pending'
            investment.save()
            messages.success(request, 'Your investment has been submitted!')
            return redirect('projects:project_detail', project_id=project.id)
    else:
        form = InvestmentForm(project=project)

    context = {
        'form': form,
        'project': project,
    }
    return render(request, 'projects/investment_form.html', context)


@login_required
def my_donations(request):
    """View user's completed donations."""
    donations = Donation.objects.filter(donor=request.user, status='completed').order_by('-created_at')

    context = {
        'donations': donations,
    }
    return render(request, 'projects/my_donations.html', context)


@login_required
def my_investments(request):
    """View user's investments."""
    investments = Investment.objects.filter(investor=request.user).order_by('-created_at')

    context = {
        'investments': investments,
    }
    return render(request, 'projects/my_investments.html', context)


def about_page(request):
    """About page - redirect to CMS about page."""
    return redirect('cms:about_page')


@login_required
def create_category(request):
    """Create a new category via AJAX (for founders)."""
    if request.method == 'POST' and request.user.user_type == 'founder':
        import json
        try:
            data = json.loads(request.body)
            name = data.get('name', '').strip()

            if not name:
                return JsonResponse({'success': False, 'error': 'Category name is required'})

            if len(name) > 100:
                return JsonResponse({'success': False, 'error': 'Category name must be 100 characters or less'})

            # Check if category already exists (case-insensitive)
            existing = Category.objects.filter(name__iexact=name).first()
            if existing:
                return JsonResponse({
                    'success': True,
                    'category': {'id': existing.id, 'name': existing.name},
                    'message': 'Category already exists'
                })

            # Create new category
            category = Category.objects.create(name=name)
            return JsonResponse({
                'success': True,
                'category': {'id': category.id, 'name': category.name},
                'message': 'Category created successfully'
            })
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid request data'})

    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)


def ensure_funding_types_exist():
    """Ensure default funding types exist in the database."""
    default_funding_types = [
        {'name': 'Donation', 'description': 'Charitable donations with no equity'},
        {'name': 'Equity', 'description': 'Investment in exchange for company shares'},
        {'name': 'Reward', 'description': 'Contribution in exchange for rewards/perks'},
        {'name': 'Debt', 'description': 'Loan-based funding with interest'},
    ]

    for ft_data in default_funding_types:
        FundingType.objects.get_or_create(
            name=ft_data['name'],
            defaults={'description': ft_data['description']}
        )
