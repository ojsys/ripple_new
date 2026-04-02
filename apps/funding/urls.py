from django.urls import path
from apps.funding import views

app_name = 'funding'

urlpatterns = [
    path('withdraw/<int:project_id>/', views.founder_withdrawal_request, name='founder_withdrawal_request'),
    path('withdrawals/', views.founder_withdrawals, name='founder_withdrawals'),
    path('withdrawals/<str:reference>/', views.founder_withdrawal_detail, name='founder_withdrawal_detail'),
    path('withdrawals/<str:reference>/cancel/', views.cancel_founder_withdrawal, name='cancel_founder_withdrawal'),
]
