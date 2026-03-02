from django.urls import path
from . import views

app_name = 'srt'

urlpatterns = [
    # Become a Partner (no auth required for viewing, login required for POST)
    path('become-partner/', views.become_partner, name='become_partner'),

    # Dashboard
    path('', views.partner_dashboard, name='dashboard'),
    path('dashboard/', views.partner_dashboard, name='partner_dashboard'),

    # Token Management
    path('buy-tokens/', views.buy_tokens, name='buy_tokens'),
    path('initialize-purchase/', views.initialize_token_purchase, name='initialize_purchase'),
    path('token-purchase-callback/', views.token_purchase_callback, name='token_purchase_callback'),

    # Token Withdrawal
    path('withdraw/', views.withdraw_tokens, name='withdraw_tokens'),
    path('withdrawals/', views.my_withdrawals, name='my_withdrawals'),
    path('withdrawals/export/excel/', views.export_my_withdrawals_excel, name='export_withdrawals_excel'),
    path('withdrawals/export/csv/', views.export_my_withdrawals_csv, name='export_withdrawals_csv'),
    path('withdrawal/<str:reference>/', views.withdrawal_detail, name='withdrawal_detail'),
    path('withdrawal/<str:reference>/cancel/', views.cancel_withdrawal, name='cancel_withdrawal'),

    # Ventures
    path('ventures/', views.venture_list, name='venture_list'),
    path('ventures/<slug:slug>/', views.venture_detail, name='venture_detail'),
    path('ventures/<slug:slug>/invest/', views.invest_in_venture, name='invest'),

    # Investments
    path('investments/', views.my_investments, name='my_investments'),
    path('investments/<str:reference>/', views.investment_detail, name='investment_detail'),
    path('investments/<str:reference>/modify/', views.modify_investment, name='modify_investment'),

    # Transactions
    path('transactions/', views.transaction_history, name='transaction_history'),
    path('transactions/export/excel/', views.export_my_transactions_excel, name='export_transactions_excel'),
    path('transactions/export/csv/', views.export_my_transactions_csv, name='export_transactions_csv'),

    # Profile
    path('profile/', views.partner_profile, name='partner_profile'),

    # Project SRT Investment
    path('projects/<int:project_id>/invest/', views.invest_in_project, name='invest_in_project'),

    # Venture Founder Token Withdrawals
    path('projects/<int:project_id>/venture-withdraw/', views.venture_withdraw_tokens, name='venture_withdraw_tokens'),
    path('venture-withdrawals/', views.my_venture_withdrawals, name='my_venture_withdrawals'),
    path('venture-withdrawal/<str:reference>/', views.venture_withdrawal_detail, name='venture_withdrawal_detail'),
    path('venture-withdrawal/<str:reference>/cancel/', views.cancel_venture_withdrawal, name='cancel_venture_withdrawal'),
]
