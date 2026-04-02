from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.conf import settings
from django.urls import reverse
import requests
import uuid

from .models import Project, Category, FundingType, Reward, Update, Donation, PaymentAttempt
from .forms import ProjectForm, RewardForm, RewardFormSet, UpdateForm, DonationForm, InvestmentForm
from apps.funding.models import Investment, InvestmentTerm, InvestorEscrowBalance
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

    # Featured projects (sync funding amounts) - separate by listing type
    featured_projects = Project.objects.filter(status='approved', listing_type='project').order_by('-created_at')[:6]
    for project in featured_projects:
        project.recalculate_funding()

    # Featured ventures
    featured_ventures = Project.objects.filter(status='approved', listing_type='venture').order_by('-created_at')[:6]

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
        'featured_ventures': featured_ventures,
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
    """List all approved projects/ventures with filtering and pagination."""
    # Determine listing type: from URL path or query parameter
    if request.path.rstrip('/').endswith('ventures'):
        listing_type = 'venture'
    else:
        listing_type = request.GET.get('type', 'project')
    if listing_type not in ('project', 'venture'):
        listing_type = 'project'

    projects = Project.objects.filter(status='approved', listing_type=listing_type).order_by('-created_at')
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

    # Filter by financing type (ventures only)
    financing_type = request.GET.get('financing_type')
    if financing_type and listing_type == 'venture':
        projects = projects.filter(financing_type=financing_type)

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

    # Sync funding amounts for projects on this page
    for project in page_obj:
        project.recalculate_funding()

    context = {
        'page_obj': page_obj,
        'projects': page_obj,
        'categories': categories,
        'funding_types': funding_types,
        'current_category': category_id,
        'current_funding_type': funding_type_id,
        'current_financing_type': financing_type,
        'search_query': search_query,
        'sort_by': sort_by,
        'listing_type': listing_type,
    }
    return render(request, 'projects/project_list.html', context)


def project_detail_by_id(request, project_id):
    """Redirect legacy numeric URLs to slug-based URLs."""
    project = get_object_or_404(Project, id=project_id)
    return redirect('projects:project_detail', slug=project.slug, permanent=True)


def project_detail(request, slug):
    """Display project details."""
    project = get_object_or_404(Project, slug=slug)

    # Sync amount_raised from actual completed donations
    project.recalculate_funding()

    # Calculate percent funded (now uses the accurate amount_raised)
    percent_funded = project.get_percent_funded()

    # Initialize forms based on listing type and funding type
    pledge_form = None
    investment_form = None

    if project.is_venture:
        # Ventures always show investment form
        investment_form = InvestmentForm(project=project)
    elif project.funding_type and project.funding_type.name == 'Equity':
        investment_form = InvestmentForm(project=project)
    else:
        # Projects default to donation form
        pledge_form = DonationForm(project=project)

    # Get unique backers count
    backers_count = project.get_backers_count()

    # Fetch SRT account for any authenticated user viewing a venture
    # (founders, investors, partners — anyone with tokens can invest)
    srt_account = None
    if request.user.is_authenticated and project.is_venture:
        from apps.srt.views import get_or_create_capital_account
        srt_account = get_or_create_capital_account(request.user)

    context = {
        'project': project,
        'percent_funded': percent_funded,
        'pledge_form': pledge_form,
        'investment_form': investment_form,
        'backers_count': backers_count,
        'srt_account': srt_account,
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
            return redirect('projects:project_detail', slug=project.slug)
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
    """List user's own projects and ventures."""
    all_listings = list(Project.objects.filter(creator=request.user).order_by('-created_at'))

    # Sync funding amounts
    for project in all_listings:
        project.recalculate_funding()

    # Separate into projects and ventures
    projects = [p for p in all_listings if p.listing_type == 'project']
    ventures = [p for p in all_listings if p.listing_type == 'venture']

    context = {
        'projects': projects,
        'ventures': ventures,
        'all_listings': all_listings,
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
            return redirect('projects:project_detail', slug=project.slug)
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
        return redirect('projects:project_detail', slug=project.slug)

    if project.deadline < timezone.now():
        messages.error(request, 'This project has ended.')
        return redirect('projects:project_detail', slug=project.slug)

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
            from apps.funding.fees import gross_up_ngn
            from decimal import Decimal as _D
            amount = form.cleaned_data['amount']
            amount_ngn = int(float(amount) * 1600)  # Convert to NGN
            # Gross up so payer covers the processing fee
            charged_ngn = int(gross_up_ngn(_D(amount_ngn)))
            reference = f"DON-{uuid.uuid4().hex[:16].upper()}"

            # Create a payment attempt (NOT a donation yet)
            payment_attempt = PaymentAttempt.objects.create(
                project=project,
                user=request.user,
                amount=amount,
                amount_ngn=amount_ngn,  # net donation amount
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
                'amount': charged_ngn * 100,  # grossed-up amount in kobo
                'reference': reference,
                'callback_url': request.build_absolute_uri(reverse('projects:donation_callback')),
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

                is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
                if response.status_code == 200:
                    result = response.json()
                    if result.get('status'):
                        if is_ajax:
                            from django.http import JsonResponse as _JR
                            return _JR({
                                'access_code': result['data']['access_code'],
                                'reference': reference,
                            })
                        return redirect(result['data']['authorization_url'])
                    else:
                        payment_attempt.status = 'failed'
                        payment_attempt.error_message = result.get('message', 'Unknown error')
                        payment_attempt.save()
                        err = result.get('message', 'Unknown error')
                        if is_ajax:
                            from django.http import JsonResponse as _JR
                            return _JR({'error': err}, status=400)
                        messages.error(request, f'Payment error: {err}')
                else:
                    result = response.json() if response.text else {}
                    error_msg = result.get('message', f'Status {response.status_code}')
                    payment_attempt.status = 'failed'
                    payment_attempt.error_message = error_msg
                    payment_attempt.save()
                    if is_ajax:
                        from django.http import JsonResponse as _JR
                        return _JR({'error': error_msg}, status=400)
                    messages.error(request, f'Payment service error: {error_msg}')

            except requests.exceptions.Timeout:
                payment_attempt.status = 'failed'
                payment_attempt.error_message = 'Payment service timed out'
                payment_attempt.save()
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    from django.http import JsonResponse as _JR
                    return _JR({'error': 'Payment service timed out. Please try again.'}, status=500)
                messages.error(request, 'Payment service timed out. Please try again.')
            except requests.exceptions.RequestException as e:
                payment_attempt.status = 'failed'
                payment_attempt.error_message = str(e)
                payment_attempt.save()
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    from django.http import JsonResponse as _JR
                    return _JR({'error': 'Connection error. Please try again.'}, status=500)
                messages.error(request, 'Connection error. Please try again.')
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
                return redirect('projects:project_detail', slug=donation.project.slug)
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
        return redirect('projects:project_detail', slug=payment_attempt.project.slug)

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
            return redirect('projects:project_detail', slug=payment_attempt.project.slug)
        else:
            # Payment failed at Paystack
            payment_attempt.status = 'failed'
            payment_attempt.error_message = result['data'].get('gateway_response', 'Payment was not successful')
            payment_attempt.save()
            messages.error(request, 'Payment was not successful. No charges have been applied.')
            return redirect('projects:project_detail', slug=payment_attempt.project.slug)

    messages.error(request, 'Payment verification failed. If you were charged, please contact support.')
    return redirect('projects:project_detail', slug=payment_attempt.project.slug)


@login_required
def investment_proposal(request, project_id):
    """Collect investment amount and initiate Paystack payment."""
    project = get_object_or_404(Project, id=project_id)

    if project.status != 'approved':
        messages.error(request, 'This project is not yet approved for investment. Please check back later.')
        return redirect('projects:project_detail', slug=project.slug)

    if request.method == 'POST':
        form = InvestmentForm(request.POST, project=project)
        if form.is_valid():
            from apps.funding.fees import gross_up_ngn
            from decimal import Decimal as _D
            amount = form.cleaned_data['amount']
            amount_ngn = int(float(amount) * 1600)
            # Gross up so payer covers the processing fee
            charged_ngn = int(gross_up_ngn(_D(amount_ngn)))
            reference = f"INVEST-{uuid.uuid4().hex[:14].upper()}"

            investment = form.save(commit=False)
            investment.project = project
            investment.investor = request.user
            investment.status = 'pending_payment'
            investment.payment_status = 'unpaid'
            investment.amount_ngn = amount_ngn  # net investment amount
            investment.paystack_reference = reference
            investment.save()

            paystack_secret = getattr(settings, 'PAYSTACK_SECRET_KEY', '')
            if not paystack_secret:
                messages.error(request, 'Payment system is not configured. Please contact support.')
                investment.delete()
                return redirect('projects:investment_proposal', project_id=project.id)

            headers = {
                'Authorization': f'Bearer {paystack_secret}',
                'Content-Type': 'application/json',
            }
            data = {
                'email': request.user.email,
                'amount': charged_ngn * 100,  # grossed-up amount in kobo
                'reference': reference,
                'callback_url': request.build_absolute_uri(reverse('projects:investment_payment_callback')),
                'metadata': {
                    'investment_id': investment.id,
                    'project_id': project.id,
                    'payment_type': 'investment',
                },
            }

            try:
                response = requests.post(
                    'https://api.paystack.co/transaction/initialize',
                    json=data,
                    headers=headers,
                    timeout=30,
                )
                is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
                if response.status_code == 200:
                    result = response.json()
                    if result.get('status'):
                        if is_ajax:
                            from django.http import JsonResponse as _JR
                            return _JR({
                                'access_code': result['data']['access_code'],
                                'reference': reference,
                            })
                        return redirect(result['data']['authorization_url'])
                    else:
                        investment.status = 'failed'
                        investment.save()
                        err = result.get('message', 'Unknown error')
                        if is_ajax:
                            from django.http import JsonResponse as _JR
                            return _JR({'error': err}, status=400)
                        messages.error(request, f'Payment error: {err}')
                else:
                    investment.status = 'failed'
                    investment.save()
                    result = response.json() if response.text else {}
                    err = result.get('message', f'Status {response.status_code}')
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        from django.http import JsonResponse as _JR
                        return _JR({'error': err}, status=400)
                    messages.error(request, f'Payment service error: {err}')
            except requests.exceptions.Timeout:
                investment.status = 'failed'
                investment.save()
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    from django.http import JsonResponse as _JR
                    return _JR({'error': 'Payment service timed out. Please try again.'}, status=500)
                messages.error(request, 'Payment service timed out. Please try again.')
            except requests.exceptions.RequestException:
                investment.status = 'failed'
                investment.save()
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    from django.http import JsonResponse as _JR
                    return _JR({'error': 'Connection error. Please try again.'}, status=500)
                messages.error(request, 'Connection error. Please try again.')
    else:
        form = InvestmentForm(project=project)

    escrow = InvestorEscrowBalance.objects.filter(investor=request.user).first()

    context = {
        'form': form,
        'project': project,
        'escrow': escrow,
    }
    return render(request, 'projects/investment_form.html', context)


def investment_payment_callback(request):
    """Handle Paystack callback after investor completes payment."""
    reference = request.GET.get('reference')

    if not reference:
        messages.error(request, 'Invalid payment reference.')
        return redirect('projects:project_list')

    try:
        investment = Investment.objects.get(paystack_reference=reference)
    except Investment.DoesNotExist:
        messages.error(request, 'Investment record not found.')
        return redirect('projects:project_list')

    # Avoid re-processing
    if investment.status != 'pending_payment':
        messages.info(request, 'This payment has already been processed.')
        return redirect('projects:project_detail', slug=investment.project.slug)

    paystack_secret = getattr(settings, 'PAYSTACK_SECRET_KEY', '')
    headers = {'Authorization': f'Bearer {paystack_secret}'}

    try:
        response = requests.get(
            f'https://api.paystack.co/transaction/verify/{reference}',
            headers=headers,
            timeout=30,
        )
    except requests.exceptions.RequestException:
        messages.error(request, 'Could not verify payment. If you were charged, please contact support.')
        return redirect('projects:project_detail', slug=investment.project.slug)

    if response.status_code == 200:
        result = response.json()
        if result.get('status') and result['data']['status'] == 'success':
            investment.status = 'pending_approval'
            investment.payment_status = 'paid'
            investment.save()
            messages.success(
                request,
                'Payment successful! Your investment is now pending approval from the venture founder. '
                'You will be notified once they respond.'
            )
        else:
            investment.status = 'failed'
            investment.save()
            messages.error(request, 'Payment was not successful. No charges have been applied.')
    else:
        messages.error(request, 'Payment verification failed. If you were charged, please contact support.')

    return redirect('projects:project_detail', slug=investment.project.slug)


@login_required
def pending_investments(request):
    """Founder view: list pending investments across all their ventures."""
    my_ventures = Project.objects.filter(creator=request.user, listing_type='venture')
    pending = Investment.objects.filter(
        project__in=my_ventures,
        status='pending_approval',
    ).select_related('investor', 'project').order_by('-created_at')

    context = {
        'pending_investments': pending,
    }
    return render(request, 'projects/pending_investments.html', context)


@login_required
def approve_investment(request, investment_id):
    """Founder approves a pending investment — funds will be released to founder."""
    investment = get_object_or_404(Investment, id=investment_id)

    if request.user != investment.project.creator:
        messages.error(request, 'You are not authorized to approve this investment.')
        return redirect('projects:project_detail', slug=investment.project.slug)

    if investment.status != 'pending_approval':
        messages.error(request, 'This investment is not pending approval.')
        return redirect('projects:pending_investments')

    if request.method == 'POST':
        investment.status = 'approved'
        investment.is_counted = True
        investment.save()  # triggers project amount_raised update via model save()
        messages.success(
            request,
            f'Investment of ${investment.amount} approved. Our team will arrange the fund transfer to your account.'
        )

    return redirect('projects:pending_investments')


@login_required
def reject_investment(request, investment_id):
    """Founder rejects a pending investment — funds held in investor's pool."""
    investment = get_object_or_404(Investment, id=investment_id)

    if request.user != investment.project.creator:
        messages.error(request, 'You are not authorized to reject this investment.')
        return redirect('projects:project_detail', slug=investment.project.slug)

    if investment.status != 'pending_approval':
        messages.error(request, 'This investment cannot be rejected.')
        return redirect('projects:pending_investments')

    if request.method == 'POST':
        investment.status = 'rejected'
        investment.save()

        escrow, _ = InvestorEscrowBalance.objects.get_or_create(investor=investment.investor)
        escrow.credit(investment.amount)

        messages.success(
            request,
            f'Investment rejected. ${investment.amount} has been credited to the investor\'s pool for reuse or refund.'
        )

    return redirect('projects:pending_investments')


@login_required
def request_investment_refund(request, investment_id):
    """Investor requests a refund of a rejected investment via Paystack."""
    investment = get_object_or_404(Investment, id=investment_id, investor=request.user)

    if investment.status != 'rejected':
        messages.error(request, 'Only rejected investments can be refunded.')
        return redirect('projects:my_investments')

    if request.method == 'POST':
        paystack_secret = getattr(settings, 'PAYSTACK_SECRET_KEY', '')
        headers = {
            'Authorization': f'Bearer {paystack_secret}',
            'Content-Type': 'application/json',
        }
        data = {
            'transaction': investment.paystack_reference,
            'amount': investment.amount_ngn * 100,  # kobo
        }

        try:
            response = requests.post(
                'https://api.paystack.co/refund',
                json=data,
                headers=headers,
                timeout=30,
            )
            if response.status_code in (200, 201):
                result = response.json()
                if result.get('status'):
                    investment.status = 'refund_requested'
                    investment.payment_status = 'refund_requested'
                    investment.save()

                    try:
                        escrow = InvestorEscrowBalance.objects.get(investor=request.user)
                        escrow.debit(investment.amount)
                    except (InvestorEscrowBalance.DoesNotExist, ValueError):
                        pass

                    messages.success(
                        request,
                        'Refund initiated. You should receive your funds within 5–10 business days.'
                    )
                else:
                    messages.error(request, f'Refund error: {result.get("message", "Unknown error")}')
            else:
                messages.error(request, 'Could not initiate refund. Please contact support.')
        except requests.exceptions.RequestException:
            messages.error(request, 'Connection error. Please contact support to process your refund.')

    return redirect('projects:my_investments')


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
    """View user's investments — only show payment-confirmed records."""
    investments = Investment.objects.filter(
        investor=request.user,
        payment_status='paid',
    ).order_by('-created_at')
    escrow = InvestorEscrowBalance.objects.filter(investor=request.user).first()

    context = {
        'investments': investments,
        'escrow': escrow,
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
