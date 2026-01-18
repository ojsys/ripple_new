"""
Core views including superadmin dashboard.
"""
import json
from datetime import timedelta
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum, Count, Avg, Q
from django.db.models.functions import TruncDate, TruncMonth
from django.utils import timezone


@staff_member_required
def analytics_dashboard(request):
    """
    Comprehensive analytics dashboard for superadmins.
    Shows statistics across all platform activities.
    """
    from apps.accounts.models import CustomUser, FounderProfile, InvestorProfile, PartnerProfile, RegistrationPayment
    from apps.projects.models import Project
    from apps.funding.models import Investment, Pledge
    from apps.srt.models import PartnerCapitalAccount, TokenPurchase, Venture, VentureInvestment, TokenWithdrawal
    from apps.incubator.models import IncubatorApplication
    from apps.cms.models import Contact, NewsletterSubscriber

    now = timezone.now()
    thirty_days_ago = now - timedelta(days=30)
    seven_days_ago = now - timedelta(days=7)

    # ============== USER STATISTICS ==============
    total_users = CustomUser.objects.count()
    users_by_type = CustomUser.objects.values('user_type').annotate(count=Count('id'))
    users_by_type_dict = {item['user_type']: item['count'] for item in users_by_type}

    new_users_30d = CustomUser.objects.filter(date_joined__gte=thirty_days_ago).count()
    new_users_7d = CustomUser.objects.filter(date_joined__gte=seven_days_ago).count()

    # User registration trend (last 30 days)
    user_registrations = (
        CustomUser.objects
        .filter(date_joined__gte=thirty_days_ago)
        .annotate(date=TruncDate('date_joined'))
        .values('date')
        .annotate(count=Count('id'))
        .order_by('date')
    )

    # ============== PROJECT STATISTICS ==============
    total_projects = Project.objects.count()
    projects_by_status = Project.objects.values('status').annotate(count=Count('id'))
    projects_by_status_dict = {item['status'] or 'pending': item['count'] for item in projects_by_status}

    active_projects = Project.objects.filter(
        status='approved',
        deadline__gte=now
    ).count()

    total_funding_goal = Project.objects.aggregate(total=Sum('funding_goal'))['total'] or 0
    total_amount_raised = Project.objects.aggregate(total=Sum('amount_raised'))['total'] or 0

    # Top funded projects
    top_projects = Project.objects.filter(
        amount_raised__gt=0
    ).order_by('-amount_raised')[:5]

    # ============== INVESTMENT STATISTICS ==============
    total_investments = Investment.objects.count()
    investments_by_status = Investment.objects.values('status').annotate(count=Count('id'))
    investments_by_status_dict = {item['status']: item['count'] for item in investments_by_status}

    # Investment status choices: active, pending, completed, failed
    total_investment_amount = Investment.objects.filter(
        status__in=['active', 'completed']
    ).aggregate(total=Sum('amount'))['total'] or 0

    investments_30d = Investment.objects.filter(created_at__gte=thirty_days_ago)
    investments_30d_count = investments_30d.count()
    investments_30d_amount = investments_30d.filter(status__in=['active', 'completed']).aggregate(total=Sum('amount'))['total'] or 0

    # Investment trend (last 30 days)
    investment_trend = (
        Investment.objects
        .filter(created_at__gte=thirty_days_ago)
        .annotate(date=TruncDate('created_at'))
        .values('date')
        .annotate(count=Count('id'), amount=Sum('amount'))
        .order_by('date')
    )

    # ============== PLEDGE/DONATION STATISTICS ==============
    total_pledges = Pledge.objects.count()
    total_pledge_amount = Pledge.objects.aggregate(total=Sum('amount'))['total'] or 0
    pledges_30d = Pledge.objects.filter(pledged_at__gte=thirty_days_ago)
    pledges_30d_count = pledges_30d.count()
    pledges_30d_amount = pledges_30d.aggregate(total=Sum('amount'))['total'] or 0

    # ============== SRT PARTNER STATISTICS ==============
    total_partners = PartnerProfile.objects.count()
    verified_partners = PartnerProfile.objects.filter(accreditation_status='verified').count()

    total_partner_capital = PartnerCapitalAccount.objects.aggregate(total=Sum('token_balance'))['total'] or 0

    # Token purchases
    successful_token_purchases = TokenPurchase.objects.filter(status='completed')
    total_tokens_purchased = successful_token_purchases.aggregate(total=Sum('tokens'))['total'] or 0
    total_token_revenue_usd = successful_token_purchases.aggregate(total=Sum('amount_usd'))['total'] or 0
    total_token_revenue_ngn = successful_token_purchases.aggregate(total=Sum('amount_ngn'))['total'] or 0

    # Investment
    srt_total_tokens_invested = VentureInvestment.objects.filter(status='active').aggregate(total=Sum('tokens_invested'))['total'] or 0
    srt_active_investment_count = VentureInvestment.objects.filter(status='active').count()
    srt_total_investment_count = VentureInvestment.objects.count()

    # Withdrawal
    successful_withdrawals = TokenWithdrawal.objects.filter(status='completed')
    srt_total_tokens_withdrawn = successful_withdrawals.aggregate(total=Sum('tokens'))['total'] or 0
    srt_total_ngn_withdrawn = successful_withdrawals.aggregate(total=Sum('amount_ngn'))['total'] or 0
    srt_pending_withdrawals = TokenWithdrawal.objects.filter(status='pending').count()

    # Ventures
    total_ventures = Venture.objects.count()
    active_ventures = Venture.objects.filter(status='active').count()

    # ============== INCUBATOR STATISTICS ==============
    total_applications = IncubatorApplication.objects.count()
    applications_by_status = IncubatorApplication.objects.values('status').annotate(count=Count('id'))
    applications_by_status_dict = {item['status']: item['count'] for item in applications_by_status}

    pending_applications = IncubatorApplication.objects.filter(status='pending').count()

    # ============== REVENUE STATISTICS ==============
    registration_revenue = RegistrationPayment.objects.filter(
        status='successful'
    ).aggregate(
        total_usd=Sum('amount_usd'),
        total_ngn=Sum('amount_ngn')
    )

    # ============== ENGAGEMENT STATISTICS ==============
    total_contacts = Contact.objects.count()
    # Contact model doesn't have is_read field, so we'll just show total
    unread_contacts = 0  # Can be updated if is_read field is added later
    newsletter_subscribers = NewsletterSubscriber.objects.count()

    # ============== RECENT ACTIVITY ==============
    recent_users = CustomUser.objects.order_by('-date_joined')[:10]
    recent_investments = Investment.objects.select_related('investor', 'project').order_by('-created_at')[:10]
    recent_pledges = Pledge.objects.select_related('backer', 'project').order_by('-pledged_at')[:10]
    recent_applications = IncubatorApplication.objects.order_by('-application_date')[:10]

    # ============== CHART DATA ==============
    # Prepare data for charts (JSON format)
    user_registration_chart = json.dumps([
        {'date': item['date'].strftime('%Y-%m-%d'), 'count': item['count']}
        for item in user_registrations
    ])

    investment_trend_chart = json.dumps([
        {'date': item['date'].strftime('%Y-%m-%d'), 'count': item['count'], 'amount': float(item['amount'] or 0)}
        for item in investment_trend
    ])

    users_by_type_chart = json.dumps([
        {'type': k or 'Unknown', 'count': v}
        for k, v in users_by_type_dict.items()
    ])

    context = {
        # User stats
        'total_users': total_users,
        'users_by_type': users_by_type_dict,
        'new_users_30d': new_users_30d,
        'new_users_7d': new_users_7d,
        'founders_count': users_by_type_dict.get('founder', 0),
        'investors_count': users_by_type_dict.get('investor', 0),
        'donors_count': users_by_type_dict.get('donor', 0),
        'partners_count': users_by_type_dict.get('partner', 0),

        # Project stats
        'total_projects': total_projects,
        'projects_by_status': projects_by_status_dict,
        'active_projects': active_projects,
        'total_funding_goal': total_funding_goal,
        'total_amount_raised': total_amount_raised,
        'top_projects': top_projects,

        # Investment stats
        'total_investments': total_investments,
        'investments_by_status': investments_by_status_dict,
        'total_investment_amount': total_investment_amount,
        'investments_30d_count': investments_30d_count,
        'investments_30d_amount': investments_30d_amount,

        # Pledge stats
        'total_pledges': total_pledges,
        'total_pledge_amount': total_pledge_amount,
        'pledges_30d_count': pledges_30d_count,
        'pledges_30d_amount': pledges_30d_amount,

        # SRT stats
        'total_partners': total_partners,
        'verified_partners': verified_partners,
        'srt_total_tokens_in_circulation': total_partner_capital,
        'srt_total_tokens_purchased': total_tokens_purchased,
        'srt_total_revenue_usd': total_token_revenue_usd,
        'srt_total_revenue_ngn': total_token_revenue_ngn,
        'srt_total_tokens_invested': srt_total_tokens_invested,
        'srt_active_investment_count': srt_active_investment_count,
        'srt_total_investment_count': srt_total_investment_count,
        'srt_total_tokens_withdrawn': srt_total_tokens_withdrawn,
        'srt_total_ngn_withdrawn': srt_total_ngn_withdrawn,
        'srt_pending_withdrawals': srt_pending_withdrawals,
        'total_ventures': total_ventures,
        'active_ventures': active_ventures,

        # Incubator stats
        'total_applications': total_applications,
        'applications_by_status': applications_by_status_dict,
        'pending_applications': pending_applications,

        # Revenue
        'registration_revenue_usd': registration_revenue['total_usd'] or 0,
        'registration_revenue_ngn': registration_revenue['total_ngn'] or 0,

        # Engagement
        'total_contacts': total_contacts,
        'unread_contacts': unread_contacts,
        'newsletter_subscribers': newsletter_subscribers,

        # Recent activity
        'recent_users': recent_users,
        'recent_investments': recent_investments,
        'recent_pledges': recent_pledges,
        'recent_applications': recent_applications,

        # Chart data
        'user_registration_chart': user_registration_chart,
        'investment_trend_chart': investment_trend_chart,
        'users_by_type_chart': users_by_type_chart,
    }

    return render(request, 'core/superadmin_dashboard.html', context)
