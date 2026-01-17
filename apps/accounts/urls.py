from django.urls import path
from apps.accounts import views
from django.contrib.auth import views as auth_views

app_name = 'accounts'

urlpatterns = [
    path('signup/', views.signup, name='signup'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),

    # Password reset URLs with custom templates
    path('password_reset/', 
         auth_views.PasswordResetView.as_view(
             template_name='registration/password_reset_form.html',
             email_template_name='registration/password_reset_email.html',
             subject_template_name='registration/password_reset_subject.txt',
             success_url='/accounts/password_reset/done/',
         ), 
         name='password_reset'),
    
    path('password_reset/done/', 
         auth_views.PasswordResetDoneView.as_view(
             template_name='registration/password_reset_done.html'
         ), 
         name='password_reset_done'),
    
    path('reset/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(
             template_name='registration/password_reset_confirm.html',
             success_url='/accounts/reset/done/'
         ), 
         name='password_reset_confirm'),
    
    path('reset/done/', 
         auth_views.PasswordResetCompleteView.as_view(
             template_name='registration/password_reset_complete.html'
         ), 
         name='password_reset_complete'),

    path('verify-email/<uidb64>/<token>/', views.verify_email, name='verify_email'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),
    path('complete-profile/', views.complete_profile, name='complete_profile'),
    path('registration-payment/', views.registration_payment, name='registration_payment'),
    path('initialize-registration-payment/', views.initialize_registration_payment, name='initialize_registration_payment'),
    path('registration-payment-callback/', views.registration_payment_callback, name='registration_payment_callback'),
]