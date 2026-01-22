"""
Account views for user authentication, registration, and profile management.
"""
import uuid
import logging
from datetime import timedelta

from django.shortcuts import render, redirect, get_object_or_404

logger = logging.getLogger(__name__)
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.hashers import make_password
from django.views.decorators.http import require_GET
from django.utils.http import urlsafe_base64_decode
from django.utils import timezone
from django.contrib import messages
from django.urls import reverse
from django.conf import settings
import requests

from .models import (
    CustomUser, FounderProfile, InvestorProfile, PartnerProfile,
    RegistrationPayment, PendingRegistration
)
from apps.accounts.forms import (
    SignUpForm, EditProfileForm, BaseProfileForm,
    FounderProfileForm, InvestorProfileForm, PartnerProfileForm
)
from apps.srt.models import PartnerCapitalAccount




def signup(request):
    """Handle progressive multi-step user registration."""
    logger.info(f"Signup view accessed - Method: {request.method}")

    # Handle reset request (Back button)
    if request.GET.get('reset') == '1':
        clear_registration_session(request)
        return redirect('accounts:signup')

    # Get current step from session or default to 1
    current_step = request.session.get('registration_step', 1)
    logger.info(f"Current registration step: {current_step}")

    if request.method == 'POST':
        step = request.POST.get('step', '1')
        logger.info(f"POST received for step: {step}")

        # Step 1: User type selection
        if step == '1':
            user_type = request.POST.get('user_type')
            if user_type in ['founder', 'donor', 'investor', 'partner']:
                request.session['registration_user_type'] = user_type
                request.session['registration_step'] = 2
                return redirect('accounts:signup')
            else:
                messages.error(request, "Please select an account type.")
                return redirect('accounts:signup')

        # Step 2: Personal details
        elif step == '2':
            form = SignUpForm(request.POST)
            if form.is_valid():
                user_type = request.session.get('registration_user_type')
                if not user_type:
                    request.session['registration_step'] = 1
                    return redirect('accounts:signup')

                cleaned_data = form.cleaned_data
                cleaned_data['user_type'] = user_type

                # SRT Partners don't need to pay - create account directly
                if user_type == 'partner':
                    logger.info(f"Creating SRT Partner account directly for: {cleaned_data['email']}")
                    # Clear registration session data
                    clear_registration_session(request)
                    return create_user_directly(request, cleaned_data)

                # For other user types, create pending registration and go to payment
                # Check if email already has a pending registration
                existing_pending = PendingRegistration.objects.filter(email=cleaned_data['email']).first()
                if existing_pending:
                    if existing_pending.is_expired():
                        existing_pending.delete()
                    else:
                        request.session['pending_registration_id'] = existing_pending.id
                        clear_registration_session(request)
                        return redirect('accounts:registration_payment')

                # Generate unique reference
                reference = f"reg_{uuid.uuid4().hex[:12]}"

                # Create pending registration
                pending_registration = PendingRegistration.objects.create(
                    first_name=cleaned_data['first_name'],
                    last_name=cleaned_data['last_name'],
                    email=cleaned_data['email'],
                    phone_number=cleaned_data['phone_number'],
                    user_type=user_type,
                    password_hash=make_password(cleaned_data['password']),
                    paystack_reference=reference,
                    amount_usd=0,
                    amount_ngn=0,
                    expires_at=timezone.now() + timedelta(hours=24),
                )

                # Set amounts based on user type
                pending_registration.amount_usd = pending_registration.get_registration_fee()
                pending_registration.amount_ngn = pending_registration.get_registration_fee_ngn()
                pending_registration.save()

                # Store pending registration ID in session
                request.session['pending_registration_id'] = pending_registration.id

                # Clear registration session data
                clear_registration_session(request)

                # Redirect to payment page
                return redirect('accounts:registration_payment')
            else:
                # Store form data in session for repopulation
                request.session['registration_form_data'] = request.POST
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")
                return redirect('accounts:signup')

    # GET request - show appropriate step
    form = SignUpForm()
    context = {
        'step': current_step,
        'user_type': request.session.get('registration_user_type'),
        'form_data': request.session.get('registration_form_data', {}),
        'form': form
    }

    return render(request, 'accounts/signup.html', context)


def clear_registration_session(request):
    """Clear registration-related session data."""
    keys_to_clear = ['registration_step', 'registration_user_type', 'registration_form_data']
    for key in keys_to_clear:
        if key in request.session:
            del request.session[key]


def create_user_directly(request, cleaned_data):
    """Create user account directly without payment (for SRT Partners)."""
    logger.info(f"create_user_directly called for: {cleaned_data.get('email')}")
    try:
        # Create the user
        user = CustomUser.objects.create(
            username=cleaned_data['email'],
            email=cleaned_data['email'],
            first_name=cleaned_data['first_name'],
            last_name=cleaned_data['last_name'],
            phone_number=cleaned_data['phone_number'],
            user_type=cleaned_data['user_type'],
            is_active=True,
            registration_fee_paid=True,  # No fee required for partners
        )
        user.set_password(cleaned_data['password'])
        user.save()

        # Create partner profile
        partner_profile = PartnerProfile.objects.create(
            user=user,
            partner_id=f"SRT-{uuid.uuid4().hex[:8].upper()}",
            accreditation_status='pending',
        )

        # Create capital account
        PartnerCapitalAccount.objects.create(
            partner=user,
            token_balance=0
        )

        # Log the user in
        login(request, user)
        logger.info(f"SRT Partner account created and logged in: {user.email}")

        messages.success(request, f"Welcome to StartUpRipple, {user.first_name}! Your SRT Partner account has been created.")
        return redirect('srt:dashboard')

    except Exception as e:
        logger.error(f"Error creating SRT Partner account: {str(e)}", exc_info=True)
        messages.error(request, f"Error creating account: {str(e)}")
        return redirect('accounts:signup')


def verify_email(request, uidb64, token):
    """Verify user email from verification link."""
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = CustomUser.objects.get(pk=uid)

        if default_token_generator.check_token(user, token):
            user.is_active = True
            user.email_verified = True
            user.save()

            messages.success(request, "Your email has been verified successfully! You can now log in.")
            return redirect('accounts:login')
        else:
            messages.error(request, "The verification link is invalid or has expired.")
            return redirect('projects:home')
    except Exception as e:
        messages.error(request, "An error occurred during verification. Please try again.")
        return redirect('projects:home')


def user_login(request):
    """Handle user login."""
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('projects:home')
    else:
        form = AuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})


@require_GET
def user_logout(request):
    """Handle user logout."""
    logout(request)
    return redirect('projects:home')


@login_required
def edit_profile(request):
    """Edit user profile based on user type."""
    user = request.user

    # Initialize profile based on user type
    founder_form = None
    investor_form = None
    partner_form = None

    if user.user_type == 'founder':
        founder_profile, created = FounderProfile.objects.get_or_create(user=user)
    elif user.user_type == 'investor':
        investor_profile, created = InvestorProfile.objects.get_or_create(user=user)
    elif user.user_type == 'partner':
        partner_profile, created = PartnerProfile.objects.get_or_create(user=user)

    if request.method == 'POST':
        user_form = EditProfileForm(request.POST, instance=user)

        if user.user_type == 'founder':
            founder_form = FounderProfileForm(
                request.POST,
                request.FILES,
                instance=founder_profile
            )

            if user_form.is_valid() and founder_form.is_valid():
                user_form.save()
                founder_profile = founder_form.save(commit=False)
                founder_profile.user = user
                founder_profile.save()
                messages.success(request, 'Profile updated successfully!')
                return redirect('accounts:edit_profile')
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
                return redirect('accounts:edit_profile')
            else:
                for field, errors in user_form.errors.items():
                    for error in errors:
                        messages.error(request, f"Error in {field}: {error}")
                for field, errors in investor_form.errors.items():
                    for error in errors:
                        messages.error(request, f"Error in {field}: {error}")

        elif user.user_type == 'partner':
            partner_form = PartnerProfileForm(
                request.POST,
                request.FILES,
                instance=partner_profile
            )

            if user_form.is_valid() and partner_form.is_valid():
                user_form.save()
                partner_profile = partner_form.save(commit=False)
                partner_profile.user = user
                partner_profile.save()
                messages.success(request, 'Profile updated successfully!')
                return redirect('accounts:edit_profile')
            else:
                for field, errors in user_form.errors.items():
                    for error in errors:
                        messages.error(request, f"Error in {field}: {error}")
                for field, errors in partner_form.errors.items():
                    for error in errors:
                        messages.error(request, f"Error in {field}: {error}")
        else:
            if user_form.is_valid():
                user_form.save()
                messages.success(request, 'Profile updated successfully!')
                return redirect('accounts:edit_profile')
            else:
                for field, errors in user_form.errors.items():
                    for error in errors:
                        messages.error(request, f"Error in {field}: {error}")
    else:
        user_form = EditProfileForm(instance=user)
        if user.user_type == 'founder':
            founder_form = FounderProfileForm(instance=founder_profile)
        elif user.user_type == 'investor':
            investor_form = InvestorProfileForm(instance=investor_profile)
        elif user.user_type == 'partner':
            partner_form = PartnerProfileForm(instance=partner_profile)

    context = {
        'user_form': user_form,
        'founder_form': founder_form if user.user_type == 'founder' else None,
        'investor_form': investor_form if user.user_type == 'investor' else None,
        'partner_form': partner_form if user.user_type == 'partner' else None,
    }

    return render(request, 'accounts/edit_profile.html', context)


def complete_profile(request):
    """Complete profile after registration."""
    if not request.user.is_authenticated:
        return redirect('accounts:login')

    user = request.user
    profile_forms = {
        'founder': FounderProfileForm,
        'investor': InvestorProfileForm,
    }

    if request.method == 'POST':
        base_form = BaseProfileForm(request.POST, instance=user)
        specific_form = None

        if user.user_type in profile_forms:
            try:
                instance = user.founderprofile if user.user_type == 'founder' else user.investorprofile
            except:
                instance = None
            specific_form = profile_forms[user.user_type](request.POST, instance=instance)

        if base_form.is_valid() and (specific_form.is_valid() if specific_form else True):
            base_form.save()
            if specific_form:
                profile = specific_form.save(commit=False)
                profile.user = user
                profile.save()
            user.profile_completed = True
            user.save()
            return redirect('accounts:dashboard')
    else:
        base_form = BaseProfileForm(instance=user)
        specific_form = None
        if user.user_type in profile_forms:
            try:
                instance = user.founderprofile if user.user_type == 'founder' else user.investorprofile
            except:
                instance = None
            specific_form = profile_forms[user.user_type](instance=instance)

    return render(request, 'accounts/complete_profile.html', {
        'base_form': base_form,
        'specific_form': specific_form,
        'user_type': user.user_type
    })


@login_required
def dashboard(request):
    """
    Main dashboard view that routes users to appropriate dashboard based on user type.
    Partners are redirected to SRT dashboard, others see the general dashboard.
    """
    user = request.user

    # Redirect partners to SRT dashboard
    if user.user_type == 'partner':
        return redirect('srt:dashboard')

    # For founders, investors, and donors - show the general dashboard
    from apps.projects.models import Project
    from apps.funding.models import Investment, Pledge
    from django.utils import timezone

    context = {
        'user': user,
        'now': timezone.now(),
    }

    if user.user_type == 'founder':
        # Founder-specific context
        created_projects = Project.objects.filter(creator=user).order_by('-created_at')
        context.update({
            'created_projects': created_projects,
            'total_projects': created_projects.count(),
            'active_projects': created_projects.filter(deadline__gte=timezone.now()).count(),
            'total_raised': sum(p.amount_raised for p in created_projects),
            'avg_funding': sum(p.get_percent_funded() for p in created_projects) / created_projects.count() if created_projects.count() > 0 else 0,
        })

    if user.user_type in ['investor', 'donor']:
        # Get investments for investors
        investments = Investment.objects.filter(investor=user).select_related('project', 'terms').order_by('-created_at')
        context['investments'] = investments

    if user.user_type == 'donor':
        # Get pledges for donors
        pledges = Pledge.objects.filter(backer=user).select_related('project', 'reward').order_by('-pledged_at')
        context['pledges'] = pledges

    # Recommended projects for investors
    if user.user_type == 'investor':
        recommended_projects = Project.objects.filter(
            status='approved',
            deadline__gte=timezone.now()
        ).exclude(creator=user).order_by('-created_at')[:6]
        context['recommended_projects'] = recommended_projects

    return render(request, 'dashboard.html', context)


# Registration Payment Views
def registration_payment(request):
    """Display registration payment page."""
    if 'pending_registration_id' not in request.session:
        messages.error(request, "No pending registration found. Please start registration again.")
        return redirect('accounts:signup')

    try:
        pending_registration = PendingRegistration.objects.get(id=request.session['pending_registration_id'])

        if pending_registration.is_expired():
            pending_registration.delete()
            del request.session['pending_registration_id']
            messages.error(request, "Registration session expired. Please start registration again.")
            return redirect('accounts:signup')

        if pending_registration.payment_status == 'successful':
            messages.info(request, "Registration fee already paid.")
            return redirect('accounts:login')

        context = {
            'pending_registration': pending_registration,
            'fee_usd': pending_registration.amount_usd,
            'fee_ngn': pending_registration.amount_ngn,
            'paystack_public_key': settings.PAYSTACK_PUBLIC_KEY,
        }

        return render(request, 'accounts/registration_payment.html', context)
    except PendingRegistration.DoesNotExist:
        messages.error(request, "Invalid registration session. Please start registration again.")
        return redirect('accounts:signup')


def initialize_registration_payment(request):
    """Initialize registration payment with Paystack."""
    if request.method == 'POST' and 'pending_registration_id' in request.session:
        try:
            pending_registration = PendingRegistration.objects.get(id=request.session['pending_registration_id'])

            if pending_registration.is_expired():
                pending_registration.delete()
                del request.session['pending_registration_id']
                messages.error(request, "Registration session expired. Please start registration again.")
                return redirect('accounts:signup')

            if pending_registration.payment_status != 'pending':
                messages.error(request, "Registration payment already initiated.")
                return redirect('accounts:registration_payment')

            # Generate a new unique reference to avoid duplicates
            new_reference = f"reg_{uuid.uuid4().hex[:12]}"
            pending_registration.paystack_reference = new_reference
            pending_registration.save()

            # Initialize payment with Paystack
            url = "https://api.paystack.co/transaction/initialize"
            headers = {
                'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
                'Content-Type': 'application/json',
            }

            data = {
                'email': pending_registration.email,
                'amount': int(pending_registration.amount_ngn * 100),
                'reference': pending_registration.paystack_reference,
                'callback_url': request.build_absolute_uri(reverse('accounts:registration_payment_callback')),
                'metadata': {
                    'pending_registration_id': pending_registration.id,
                    'payment_type': 'registration_fee',
                    'user_type': pending_registration.user_type,
                }
            }

            response = requests.post(url, headers=headers, json=data)

            if response.status_code == 200:
                response_data = response.json()
                if response_data['status']:
                    authorization_url = response_data['data']['authorization_url']
                    return redirect(authorization_url)
                else:
                    # Log the actual error from Paystack
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Paystack error: {response_data.get('message', 'Unknown error')}")
                    messages.error(request, f"Payment failed: {response_data.get('message', 'Unknown error')}")
                    return redirect('accounts:registration_payment')
            else:
                # Log HTTP error
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Paystack HTTP error {response.status_code}: {response.text}")
                messages.error(request, f"Payment service error. Status: {response.status_code}")
            return redirect('accounts:registration_payment')

        except PendingRegistration.DoesNotExist:
            messages.error(request, "Invalid registration session.")
            return redirect('accounts:signup')
        except Exception as e:
            messages.error(request, f"Error initializing payment: {str(e)}")
            return redirect('accounts:registration_payment')

    return redirect('accounts:signup')


def registration_payment_callback(request):
    """Handle payment callback from Paystack."""
    reference = request.GET.get('reference')
    logger.info(f"Payment callback received with reference: {reference}")

    if not reference:
        logger.warning("Payment callback received without reference")
        messages.error(request, "Invalid payment reference.")
        return redirect('accounts:signup')

    try:
        pending_registration = PendingRegistration.objects.get(paystack_reference=reference)

        if pending_registration.is_expired():
            pending_registration.delete()
            messages.error(request, "Registration session expired. Please start registration again.")
            return redirect('accounts:signup')

        # Verify payment with Paystack
        url = f"https://api.paystack.co/transaction/verify/{reference}"
        headers = {
            'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
        }

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            response_data = response.json()
            logger.info(f"Paystack verification response: {response_data.get('status')}, payment status: {response_data.get('data', {}).get('status')}")

            if response_data['status'] and response_data['data']['status'] == 'success':
                pending_registration.payment_status = 'successful'
                pending_registration.save()
                logger.info(f"Payment verified for: {pending_registration.email}")

                # Create the actual user account
                user = CustomUser.objects.create(
                    username=pending_registration.email,
                    email=pending_registration.email,
                    first_name=pending_registration.first_name,
                    last_name=pending_registration.last_name,
                    phone_number=pending_registration.phone_number,
                    user_type=pending_registration.user_type,
                    password=pending_registration.password_hash,
                    is_active=True,
                    registration_fee_paid=True,
                    email_verified=True,
                )

                # Create profile based on user type
                if user.user_type == 'founder':
                    FounderProfile.objects.create(user=user)
                elif user.user_type == 'investor':
                    InvestorProfile.objects.create(user=user)
                elif user.user_type == 'partner':
                    # Generate unique partner ID
                    import random
                    partner_id = f"SRT-{random.randint(1000, 9999)}"
                    while PartnerProfile.objects.filter(partner_id=partner_id).exists():
                        partner_id = f"SRT-{random.randint(1000, 9999)}"
                    PartnerProfile.objects.create(user=user, partner_id=partner_id)
                    PartnerCapitalAccount.objects.create(partner=user, token_balance=0)

                # Create registration payment record
                RegistrationPayment.objects.create(
                    user=user,
                    amount_usd=pending_registration.amount_usd,
                    amount_ngn=pending_registration.amount_ngn,
                    paystack_reference=reference,
                    status='successful'
                )

                # Clean up
                pending_registration.delete()

                if 'pending_registration_id' in request.session:
                    del request.session['pending_registration_id']

                login(request, user)
                logger.info(f"User created and logged in after payment: {user.email}, type: {user.user_type}")

                messages.success(
                    request,
                    f"Registration fee paid successfully! Welcome to StartUpRipple, {user.get_full_name()}!"
                )

                return redirect('accounts:dashboard')
            else:
                pending_registration.payment_status = 'failed'
                pending_registration.save()
                logger.warning(f"Payment verification failed for {pending_registration.email}: {response_data}")
                messages.error(request, "Payment verification failed. Please try again.")
                return redirect('accounts:registration_payment')
        else:
            logger.error(f"Paystack API error: {response.status_code} - {response.text}")
            messages.error(request, "Payment verification failed. Please try again.")
            return redirect('accounts:registration_payment')

    except PendingRegistration.DoesNotExist:
        logger.warning(f"PendingRegistration not found for reference: {reference}")
        messages.error(request, "Invalid payment reference.")
        return redirect('accounts:signup')
    except Exception as e:
        logger.error(f"Error processing payment callback: {str(e)}", exc_info=True)
        messages.error(request, f"Error processing payment: {str(e)}")
        return redirect('accounts:registration_payment')
