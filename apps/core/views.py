"""
Core views including superadmin analytics dashboard.
"""
import json
from datetime import timedelta
from decimal import Decimal
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum, Count, Avg, Q
from django.db.models.functions import TruncDate, TruncMonth
from django.utils import timezone


@staff_member_required
def analytics_dashboard(request):
    """
    Comprehensive analytics dashboard for superadmins.
    Shows statistics across all platform activities including platform revenue.
    """
    from apps.accounts.models import CustomUser, FounderProfile, InvestorProfile, PartnerProfile, RegistrationPayment
    from apps.projects.models import Project
    from apps.funding.models import Investment, Pledge, FounderWithdrawalRequest
    from apps.funding.fees import platform_fee_summary
    from apps.srt.models import PartnerCapitalAccount, TokenPurchase, Venture, VentureInvestment, TokenWithdrawal, VentureTokenWithdrawal
    from apps.incubator.models import IncubatorApplication
    from apps.cms.models import Contact, NewsletterSubscriber

    now = timezone.now()
    thirty_days_ago = now - timedelta(days=30)
    seven_days_ago  = now - timedelta(days=7)

    # ============================================================
    # USER STATISTICS
    # ============================================================
    total_users      = CustomUser.objects.count()
    users_by_type    = CustomUser.objects.values('user_type').annotate(count=Count('id'))
    users_by_type_dict = {item['user_type']: item['count'] for item in users_by_type}

    new_users_30d = CustomUser.objects.filter(date_joined__gte=thirty_days_ago).count()
    new_users_7d  = CustomUser.objects.filter(date_joined__gte=seven_days_ago).count()

    verified_users = CustomUser.objects.filter(email_verified=True).count() if hasattr(CustomUser, 'email_verified') else 0

    user_registrations = (
        CustomUser.objects
        .filter(date_joined__gte=thirty_days_ago)
        .annotate(date=TruncDate('date_joined'))
        .values('date')
        .annotate(count=Count('id'))
        .order_by('date')
    )

    # ============================================================
    # PROJECT / VENTURE STATISTICS
    # ============================================================
    total_projects   = Project.objects.count()
    total_ventures_projects = Project.objects.filter(listing_type='venture').count()
    total_regular_projects  = Project.objects.filter(listing_type='project').count()

    projects_by_status     = Project.objects.values('status').annotate(count=Count('id'))
    projects_by_status_dict = {item['status'] or 'pending': item['count'] for item in projects_by_status}

    active_projects  = Project.objects.filter(status='approved', deadline__gte=now).count()
    active_ventures  = Project.objects.filter(listing_type='venture', status='approved', deadline__gte=now).count()

    total_funding_goal   = Project.objects.aggregate(total=Sum('funding_goal'))['total'] or 0
    total_amount_raised  = Project.objects.aggregate(total=Sum('amount_raised'))['total'] or 0
    total_investment_raised = Project.objects.aggregate(total=Sum('total_investment_raised'))['total'] or 0
    total_srt_raised     = Project.objects.aggregate(total=Sum('srt_amount_raised'))['total'] or 0

    top_projects = Project.objects.filter(amount_raised__gt=0).order_by('-amount_raised')[:5]

    # ============================================================
    # DIRECT INVESTMENT STATISTICS  (funding.Investment)
    # ============================================================
    COUNTING_STATUSES = ('pending_approval', 'active', 'approved', 'completed')

    total_investments = Investment.objects.count()
    investments_by_status = Investment.objects.values('status').annotate(count=Count('id'))
    investments_by_status_dict = {item['status']: item['count'] for item in investments_by_status}

    total_investment_amount = Investment.objects.filter(
        status__in=COUNTING_STATUSES
    ).aggregate(total=Sum('amount'))['total'] or 0

    investments_30d_count  = Investment.objects.filter(created_at__gte=thirty_days_ago).count()
    investments_30d_amount = Investment.objects.filter(
        created_at__gte=thirty_days_ago, status__in=COUNTING_STATUSES
    ).aggregate(total=Sum('amount'))['total'] or 0

    investment_trend = (
        Investment.objects
        .filter(created_at__gte=thirty_days_ago)
        .annotate(date=TruncDate('created_at'))
        .values('date')
        .annotate(count=Count('id'), amount=Sum('amount'))
        .order_by('date')
    )

    recent_investments = Investment.objects.select_related('investor', 'project').order_by('-created_at')[:10]

    # ============================================================
    # PLEDGE / DONATION STATISTICS
    # ============================================================
    total_pledges       = Pledge.objects.count()
    total_pledge_amount = Pledge.objects.aggregate(total=Sum('amount'))['total'] or 0
    pledges_30d_count   = Pledge.objects.filter(pledged_at__gte=thirty_days_ago).count()
    pledges_30d_amount  = Pledge.objects.filter(
        pledged_at__gte=thirty_days_ago
    ).aggregate(total=Sum('amount'))['total'] or 0

    # ============================================================
    # SRT / PARTNER STATISTICS
    # ============================================================
    total_partners    = PartnerProfile.objects.count()
    verified_partners = PartnerProfile.objects.filter(accreditation_status='verified').count()
    total_partner_capital = PartnerCapitalAccount.objects.aggregate(total=Sum('token_balance'))['total'] or 0

    successful_token_purchases  = TokenPurchase.objects.filter(status='completed')
    total_tokens_purchased      = successful_token_purchases.aggregate(total=Sum('tokens'))['total'] or 0
    total_token_revenue_usd     = successful_token_purchases.aggregate(total=Sum('amount_usd'))['total'] or 0
    total_token_revenue_ngn     = successful_token_purchases.aggregate(total=Sum('amount_ngn'))['total'] or 0

    srt_total_tokens_invested   = VentureInvestment.objects.filter(status='active').aggregate(total=Sum('tokens_invested'))['total'] or 0
    srt_active_investment_count = VentureInvestment.objects.filter(status='active').count()
    srt_total_investment_count  = VentureInvestment.objects.count()

    # SRT Partner withdrawals
    srt_completed_withdrawals   = TokenWithdrawal.objects.filter(status='completed')
    srt_total_tokens_withdrawn  = srt_completed_withdrawals.aggregate(total=Sum('tokens'))['total'] or 0
    srt_total_ngn_withdrawn     = srt_completed_withdrawals.aggregate(total=Sum('amount_ngn'))['total'] or 0
    srt_pending_withdrawals     = TokenWithdrawal.objects.filter(status='pending').count()

    # Legacy Venture model
    total_ventures_legacy = Venture.objects.count()
    active_ventures_legacy = Venture.objects.filter(status='active').count()

    # ============================================================
    # FOUNDER WITHDRAWAL REQUESTS
    # ============================================================
    fwr_stats = FounderWithdrawalRequest.objects.aggregate(
        pending_count   = Count('id', filter=Q(status='pending')),
        approved_count  = Count('id', filter=Q(status='approved')),
        processing_count= Count('id', filter=Q(status='processing')),
        completed_count = Count('id', filter=Q(status='completed')),
        rejected_count  = Count('id', filter=Q(status='rejected')),
        total_requested = Sum('amount_usd'),
        total_paid_out  = Sum('amount_usd', filter=Q(status='completed')),
        total_pending_amount = Sum('amount_usd', filter=Q(status__in=['pending','approved','processing'])),
    )
    fwr_pending_action = (fwr_stats['pending_count'] or 0) + (fwr_stats['approved_count'] or 0)

    # Venture SRT withdrawals (VentureTokenWithdrawal)
    vtw_pending = VentureTokenWithdrawal.objects.filter(status='pending').count()
    vtw_completed_ngn = VentureTokenWithdrawal.objects.filter(
        status='completed'
    ).aggregate(total=Sum('amount_ngn'))['total'] or 0

    recent_founder_withdrawals = FounderWithdrawalRequest.objects.select_related(
        'founder', 'project'
    ).order_by('-created_at')[:8]

    # ============================================================
    # PLATFORM REVENUE  (registration fees + 2% admin fee)
    # ============================================================
    registration_revenue = RegistrationPayment.objects.filter(
        status='successful'
    ).aggregate(
        total_usd=Sum('amount_usd'),
        total_ngn=Sum('amount_ngn'),
        count=Count('id'),
    )
    reg_revenue_usd = registration_revenue['total_usd'] or Decimal('0')
    reg_revenue_ngn = registration_revenue['total_ngn'] or Decimal('0')
    reg_count       = registration_revenue['count'] or 0

    # Admin fee (2%) across all investment transactions
    fee_data = platform_fee_summary()
    admin_fee_ngn_total     = fee_data['admin_fees_ngn']
    admin_fee_usd_total     = fee_data['admin_fees_usd']
    processing_fee_ngn_total = fee_data['paystack_fees_ngn']
    processing_fee_usd_total = fee_data['paystack_fees_usd']

    # Total platform revenue = registration fees + admin fees from investments
    total_platform_revenue_ngn = admin_fee_ngn_total + Decimal(str(reg_revenue_ngn))
    total_platform_revenue_usd = admin_fee_usd_total + Decimal(str(reg_revenue_usd))

    # Monthly revenue trend (last 6 months) via registration payments as proxy
    monthly_reg_revenue = (
        RegistrationPayment.objects
        .filter(status='successful', created_at__gte=now - timedelta(days=180))
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(total_usd=Sum('amount_usd'), count=Count('id'))
        .order_by('month')
    )

    # ============================================================
    # INCUBATOR STATISTICS
    # ============================================================
    total_applications = IncubatorApplication.objects.count()
    applications_by_status = IncubatorApplication.objects.values('status').annotate(count=Count('id'))
    applications_by_status_dict = {item['status']: item['count'] for item in applications_by_status}
    pending_applications = IncubatorApplication.objects.filter(status='pending').count()

    # ============================================================
    # ENGAGEMENT
    # ============================================================
    total_contacts        = Contact.objects.count()
    newsletter_subscribers = NewsletterSubscriber.objects.count()
    unread_contacts       = 0

    # ============================================================
    # RECENT ACTIVITY
    # ============================================================
    recent_users        = CustomUser.objects.order_by('-date_joined')[:10]
    recent_pledges      = Pledge.objects.select_related('backer', 'project').order_by('-pledged_at')[:10]
    recent_applications = IncubatorApplication.objects.order_by('-application_date')[:10]

    # ============================================================
    # CHART DATA  (JSON)
    # ============================================================
    user_registration_chart = json.dumps([
        {'date': item['date'].strftime('%Y-%m-%d'), 'count': item['count']}
        for item in user_registrations
    ])

    investment_trend_chart = json.dumps([
        {
            'date': item['date'].strftime('%Y-%m-%d'),
            'count': item['count'],
            'amount': float(item['amount'] or 0),
        }
        for item in investment_trend
    ])

    users_by_type_chart = json.dumps([
        {'type': k or 'Unknown', 'count': v}
        for k, v in users_by_type_dict.items()
    ])

    monthly_revenue_chart = json.dumps([
        {
            'month': item['month'].strftime('%b %Y'),
            'usd': float(item['total_usd'] or 0),
            'count': item['count'],
        }
        for item in monthly_reg_revenue
    ])

    # ============================================================
    # CONTEXT
    # ============================================================
    context = {
        # Users
        'total_users':        total_users,
        'users_by_type':      users_by_type_dict,
        'new_users_30d':      new_users_30d,
        'new_users_7d':       new_users_7d,
        'founders_count':     users_by_type_dict.get('founder', 0),
        'investors_count':    users_by_type_dict.get('investor', 0),
        'donors_count':       users_by_type_dict.get('donor', 0),
        'partners_count':     users_by_type_dict.get('partner', 0),

        # Projects
        'total_projects':           total_projects,
        'total_ventures_projects':  total_ventures_projects,
        'total_regular_projects':   total_regular_projects,
        'projects_by_status':       projects_by_status_dict,
        'active_projects':          active_projects,
        'active_ventures':          active_ventures,
        'total_funding_goal':       total_funding_goal,
        'total_amount_raised':      total_amount_raised,
        'total_investment_raised':  total_investment_raised,
        'total_srt_raised':         total_srt_raised,
        'top_projects':             top_projects,

        # Investments
        'total_investments':         total_investments,
        'investments_by_status':     investments_by_status_dict,
        'total_investment_amount':   total_investment_amount,
        'investments_30d_count':     investments_30d_count,
        'investments_30d_amount':    investments_30d_amount,
        'recent_investments':        recent_investments,

        # Pledges
        'total_pledges':       total_pledges,
        'total_pledge_amount': total_pledge_amount,
        'pledges_30d_count':   pledges_30d_count,
        'pledges_30d_amount':  pledges_30d_amount,

        # SRT
        'total_partners':               total_partners,
        'verified_partners':            verified_partners,
        'srt_total_tokens_in_circulation': total_partner_capital,
        'srt_total_tokens_purchased':   total_tokens_purchased,
        'srt_total_revenue_usd':        total_token_revenue_usd,
        'srt_total_revenue_ngn':        total_token_revenue_ngn,
        'srt_total_tokens_invested':    srt_total_tokens_invested,
        'srt_active_investment_count':  srt_active_investment_count,
        'srt_total_investment_count':   srt_total_investment_count,
        'srt_total_tokens_withdrawn':   srt_total_tokens_withdrawn,
        'srt_total_ngn_withdrawn':      srt_total_ngn_withdrawn,
        'srt_pending_withdrawals':      srt_pending_withdrawals,
        'total_ventures_legacy':        total_ventures_legacy,
        'total_tokens_purchased':       total_tokens_purchased,

        # Founder withdrawals
        'fwr_pending_count':      fwr_stats['pending_count'] or 0,
        'fwr_approved_count':     fwr_stats['approved_count'] or 0,
        'fwr_processing_count':   fwr_stats['processing_count'] or 0,
        'fwr_completed_count':    fwr_stats['completed_count'] or 0,
        'fwr_rejected_count':     fwr_stats['rejected_count'] or 0,
        'fwr_total_requested':    fwr_stats['total_requested'] or 0,
        'fwr_total_paid_out':     fwr_stats['total_paid_out'] or 0,
        'fwr_total_pending_amount': fwr_stats['total_pending_amount'] or 0,
        'fwr_pending_action':     fwr_pending_action,
        'vtw_pending':            vtw_pending,
        'vtw_completed_ngn':      vtw_completed_ngn,
        'recent_founder_withdrawals': recent_founder_withdrawals,

        # Platform revenue
        'reg_revenue_usd':              reg_revenue_usd,
        'reg_revenue_ngn':              reg_revenue_ngn,
        'reg_count':                    reg_count,
        'admin_fee_ngn_total':          admin_fee_ngn_total,
        'admin_fee_usd_total':          admin_fee_usd_total,
        'processing_fee_ngn_total':     processing_fee_ngn_total,
        'processing_fee_usd_total':     processing_fee_usd_total,
        'total_platform_revenue_ngn':   total_platform_revenue_ngn,
        'total_platform_revenue_usd':   total_platform_revenue_usd,
        'fee_transactions':             fee_data['total_transactions'],
        'gross_investment_ngn':         fee_data['gross_total_ngn'],
        'gross_investment_usd':         fee_data['gross_total_usd'],

        # Incubator
        'total_applications':        total_applications,
        'applications_by_status':    applications_by_status_dict,
        'pending_applications':      pending_applications,

        # Engagement
        'total_contacts':         total_contacts,
        'unread_contacts':        unread_contacts,
        'newsletter_subscribers': newsletter_subscribers,

        # Recent activity
        'recent_users':        recent_users,
        'recent_pledges':      recent_pledges,
        'recent_applications': recent_applications,

        # Charts
        'user_registration_chart': user_registration_chart,
        'investment_trend_chart':  investment_trend_chart,
        'users_by_type_chart':     users_by_type_chart,
        'monthly_revenue_chart':   monthly_revenue_chart,
    }

    return render(request, 'core/superadmin_dashboard.html', context)
