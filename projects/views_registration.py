# Registration Payment Views
import uuid
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login
from django.urls import reverse
from django.conf import settings
import requests
from .models import CustomUser, RegistrationPayment


def registration_payment(request):
    """Display registration payment page"""
    if 'pending_user_id' not in request.session:
        messages.error(request, "No pending registration found. Please start registration again.")
        return redirect('signup')
    
    try:
        user = CustomUser.objects.get(id=request.session['pending_user_id'])
        if user.registration_fee_paid:
            messages.info(request, "Registration fee already paid.")
            return redirect('login')
        
        # Calculate fee amounts
        fee_usd = user.get_registration_fee()
        fee_ngn = user.get_registration_fee_ngn()
        
        context = {
            'user': user,
            'fee_usd': fee_usd,
            'fee_ngn': fee_ngn,
            'paystack_public_key': settings.PAYSTACK_PUBLIC_KEY,
        }
        
        return render(request, 'registration_payment.html', context)
    except CustomUser.DoesNotExist:
        messages.error(request, "Invalid registration session. Please start registration again.")
        return redirect('signup')


def initialize_registration_payment(request):
    """Initialize registration payment with Paystack"""
    if request.method == 'POST' and 'pending_user_id' in request.session:
        try:
            user = CustomUser.objects.get(id=request.session['pending_user_id'])
            
            # Check if payment already exists
            if RegistrationPayment.objects.filter(user=user).exists():
                messages.error(request, "Registration payment already initiated.")
                return redirect('registration_payment')
            
            # Generate unique reference
            reference = f"reg_{user.id}_{uuid.uuid4().hex[:8]}"
            
            # Create payment record
            payment = RegistrationPayment.objects.create(
                user=user,
                amount_usd=user.get_registration_fee(),
                amount_ngn=user.get_registration_fee_ngn(),
                paystack_reference=reference,
                status='pending'
            )
            
            # Initialize payment with Paystack
            url = "https://api.paystack.co/transaction/initialize"
            headers = {
                'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
                'Content-Type': 'application/json',
            }
            
            data = {
                'email': user.email,
                'amount': int(payment.amount_ngn * 100),  # Paystack expects amount in kobo
                'reference': reference,
                'callback_url': request.build_absolute_uri(reverse('registration_payment_callback')),
                'metadata': {
                    'user_id': user.id,
                    'payment_type': 'registration_fee',
                    'user_type': user.user_type,
                }
            }
            
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 200:
                response_data = response.json()
                if response_data['status']:
                    authorization_url = response_data['data']['authorization_url']
                    return redirect(authorization_url)
            
            # If we reach here, payment initialization failed
            payment.delete()
            messages.error(request, "Payment initialization failed. Please try again.")
            return redirect('registration_payment')
            
        except CustomUser.DoesNotExist:
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
        # Get payment record
        payment = RegistrationPayment.objects.get(paystack_reference=reference)
        
        # Verify payment with Paystack
        url = f"https://api.paystack.co/transaction/verify/{reference}"
        headers = {
            'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
        }
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            response_data = response.json()
            if response_data['status'] and response_data['data']['status'] == 'success':
                # Payment successful
                payment.status = 'successful'
                payment.save()
                
                # Activate user account
                user = payment.user
                user.is_active = True
                user.registration_fee_paid = True
                user.save()
                
                # Clear session
                if 'pending_user_id' in request.session:
                    del request.session['pending_user_id']
                
                # Log user in
                login(request, user)
                
                messages.success(
                    request,
                    f"Registration fee paid successfully! Welcome to StartUpRipple, {user.get_full_name()}!"
                )
                
                return redirect('dashboard')
            else:
                # Payment failed
                payment.status = 'failed'
                payment.save()
                messages.error(request, "Payment verification failed. Please try again.")
                return redirect('registration_payment')
        else:
            # API call failed
            messages.error(request, "Payment verification failed. Please try again.")
            return redirect('registration_payment')
            
    except RegistrationPayment.DoesNotExist:
        messages.error(request, "Invalid payment reference.")
        return redirect('signup')
    except Exception as e:
        messages.error(request, f"Error processing payment: {str(e)}")
        return redirect('registration_payment')