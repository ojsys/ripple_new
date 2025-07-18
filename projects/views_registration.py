# Registration Payment Views
import uuid
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login
from django.urls import reverse
from django.conf import settings
import requests
from .models import CustomUser, RegistrationPayment, PendingRegistration, FounderProfile, InvestorProfile


def registration_payment(request):
    """Display registration payment page"""
    if 'pending_registration_id' not in request.session:
        messages.error(request, "No pending registration found. Please start registration again.")
        return redirect('signup')
    
    try:
        pending_registration = PendingRegistration.objects.get(id=request.session['pending_registration_id'])
        
        # Check if registration has expired
        if pending_registration.is_expired():
            pending_registration.delete()
            del request.session['pending_registration_id']
            messages.error(request, "Registration session expired. Please start registration again.")
            return redirect('signup')
        
        # Check if payment already successful
        if pending_registration.payment_status == 'successful':
            messages.info(request, "Registration fee already paid.")
            return redirect('login')
        
        context = {
            'pending_registration': pending_registration,
            'fee_usd': pending_registration.amount_usd,
            'fee_ngn': pending_registration.amount_ngn,
            'paystack_public_key': settings.PAYSTACK_PUBLIC_KEY,
        }
        
        return render(request, 'registration_payment.html', context)
    except PendingRegistration.DoesNotExist:
        messages.error(request, "Invalid registration session. Please start registration again.")
        return redirect('signup')


def initialize_registration_payment(request):
    """Initialize registration payment with Paystack"""
    if request.method == 'POST' and 'pending_registration_id' in request.session:
        try:
            pending_registration = PendingRegistration.objects.get(id=request.session['pending_registration_id'])
            
            # Check if registration has expired
            if pending_registration.is_expired():
                pending_registration.delete()
                del request.session['pending_registration_id']
                messages.error(request, "Registration session expired. Please start registration again.")
                return redirect('signup')
            
            # Check if payment already initiated
            if pending_registration.payment_status != 'pending':
                messages.error(request, "Registration payment already initiated.")
                return redirect('registration_payment')
            
            # Initialize payment with Paystack
            url = "https://api.paystack.co/transaction/initialize"
            headers = {
                'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
                'Content-Type': 'application/json',
            }
            
            data = {
                'email': pending_registration.email,
                'amount': int(pending_registration.amount_ngn * 100),  # Paystack expects amount in kobo
                'reference': pending_registration.paystack_reference,
                'callback_url': request.build_absolute_uri(reverse('registration_payment_callback')),
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
            
            # If we reach here, payment initialization failed
            messages.error(request, "Payment initialization failed. Please try again.")
            return redirect('registration_payment')
            
        except PendingRegistration.DoesNotExist:
            messages.error(request, "Invalid registration session.")
            return redirect('signup')
        except Exception as e:
            messages.error(request, f"Error initializing payment: {str(e)}")
            return redirect('registration_payment')
    
    return redirect('signup')


def registration_payment_callback(request):
    """Handle payment callback from Paystack"""
    reference = request.GET.get('reference')
    if not reference:
        messages.error(request, "Invalid payment reference.")
        return redirect('signup')
    
    try:
        # Get pending registration record
        pending_registration = PendingRegistration.objects.get(paystack_reference=reference)
        
        # Check if registration has expired
        if pending_registration.is_expired():
            pending_registration.delete()
            messages.error(request, "Registration session expired. Please start registration again.")
            return redirect('signup')
        
        # Verify payment with Paystack
        url = f"https://api.paystack.co/transaction/verify/{reference}"
        headers = {
            'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
        }
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            response_data = response.json()
            if response_data['status'] and response_data['data']['status'] == 'success':
                # Payment successful - NOW CREATE THE USER
                pending_registration.payment_status = 'successful'
                pending_registration.save()
                
                # Create the actual user account
                user = CustomUser.objects.create(
                    username=pending_registration.email,
                    email=pending_registration.email,
                    first_name=pending_registration.first_name,
                    last_name=pending_registration.last_name,
                    phone_number=pending_registration.phone_number,
                    user_type=pending_registration.user_type,
                    password=pending_registration.password_hash,  # Already hashed
                    is_active=True,
                    registration_fee_paid=True,
                    email_verified=True,  # Consider email verified after payment
                )
                
                # Create profile based on user type
                if user.user_type == 'founder':
                    FounderProfile.objects.create(user=user)
                elif user.user_type == 'investor':
                    InvestorProfile.objects.create(user=user)
                
                # Create registration payment record for admin tracking
                RegistrationPayment.objects.create(
                    user=user,
                    amount_usd=pending_registration.amount_usd,
                    amount_ngn=pending_registration.amount_ngn,
                    paystack_reference=reference,
                    status='successful'
                )
                
                # Clean up - delete pending registration
                pending_registration.delete()
                
                # Clear session
                if 'pending_registration_id' in request.session:
                    del request.session['pending_registration_id']
                
                # Log user in
                login(request, user)
                
                messages.success(
                    request,
                    f"Registration fee paid successfully! Welcome to StartUpRipple, {user.get_full_name()}!"
                )
                
                return redirect('dashboard')
            else:
                # Payment failed
                pending_registration.payment_status = 'failed'
                pending_registration.save()
                messages.error(request, "Payment verification failed. Please try again.")
                return redirect('registration_payment')
        else:
            # API call failed
            messages.error(request, "Payment verification failed. Please try again.")
            return redirect('registration_payment')
            
    except PendingRegistration.DoesNotExist:
        messages.error(request, "Invalid payment reference.")
        return redirect('signup')
    except Exception as e:
        messages.error(request, f"Error processing payment: {str(e)}")
        return redirect('registration_payment')