"""
Core views including superadmin analytics dashboard.
"""
import json
from datetime import timedelta, datetime
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

    # Investors: users with user_type='investor' PLUS unique SRT partners who have invested
    direct_investor_ids = set(
        Investment.objects.values_list('investor_id', flat=True).distinct()
    )
    srt_investor_ids = set(
        VentureInvestment.objects.values_list('partner_id', flat=True).distinct()
    )
    all_investor_ids = direct_investor_ids | srt_investor_ids
    total_investors_count = len(all_investor_ids)

    new_users_30d = CustomUser.objects.filter(date_joined__gte=thirty_days_ago).count()
    new_users_7d  = CustomUser.objects.filter(date_joined__gte=seven_days_ago).count()

    verified_users = CustomUser.objects.filter(email_verified=True).count() if hasattr(CustomUser, 'email_verified') else 0

    # Date range filter for user registrations chart
    reg_from_str = request.GET.get('reg_from', '')
    reg_to_str   = request.GET.get('reg_to', '')
    try:
        reg_from_date = timezone.make_aware(datetime.strptime(reg_from_str, '%Y-%m-%d')) if reg_from_str else thirty_days_ago
    except ValueError:
        reg_from_date = thirty_days_ago
    try:
        reg_to_date = timezone.make_aware(datetime.strptime(reg_to_str, '%Y-%m-%d').replace(hour=23, minute=59, second=59)) if reg_to_str else now
    except ValueError:
        reg_to_date = now

    user_registrations = (
        CustomUser.objects
        .filter(date_joined__gte=reg_from_date, date_joined__lte=reg_to_date)
        .annotate(date=TruncDate('date_joined'))
        .values('date')
        .annotate(count=Count('id'))
        .order_by('date')
    )
    reg_filtered_count = CustomUser.objects.filter(
        date_joined__gte=reg_from_date, date_joined__lte=reg_to_date
    ).count()

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
    processing_fee_ngn_total = Decimal('0')
    processing_fee_usd_total = Decimal('0')

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
        'investors_count':    total_investors_count,
        'donors_count':       users_by_type_dict.get('donor', 0),
        'partners_count':     users_by_type_dict.get('partner', 0),

        # Registration chart filter
        'reg_from':           reg_from_str or reg_from_date.strftime('%Y-%m-%d'),
        'reg_to':             reg_to_str or reg_to_date.strftime('%Y-%m-%d'),
        'reg_filtered_count': reg_filtered_count,

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
        'gross_direct_usd':             fee_data['gross_direct_usd'],
        'gross_srt_usd':                fee_data['gross_srt_usd'],
        'gross_direct_ngn':             fee_data['gross_direct_ngn'],
        'gross_srt_ngn':                fee_data['gross_srt_ngn'],

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


@staff_member_required
def srt_analytics(request):
    """
    Dedicated analytics page for the SRT (StartUpRipple Token) economy.

    Surfaces a complete picture of token activity: supply purchased, tokens in
    circulation, amounts invested, returns owed, withdrawals paid out, fees
    collected, plus per-partner and per-venture breakdowns and time-series
    charts.
    """
    from apps.accounts.models import PartnerProfile
    from apps.srt.models import (
        PartnerCapitalAccount, TokenPurchase, TokenPackage, Venture,
        VentureInvestment, SRTTransaction, TokenWithdrawal, VentureTokenWithdrawal,
    )
    from apps.projects.models import Project

    now = timezone.now()
    thirty_days_ago = now - timedelta(days=30)

    # ------------------------------------------------------------------
    # TOKEN SUPPLY & CIRCULATION  (authoritative source: capital accounts)
    #
    # Every token credit/debit flows through PartnerCapitalAccount, so these
    # fields — not the TokenPurchase payment log — are the source of truth for
    # token *quantities*. The invariant the page relies on:
    #     issued (purchased + earned) − withdrawn = balance (in circulation)
    #     balance = available + locked
    # total_tokens_purchased already includes package bonus tokens.
    # ------------------------------------------------------------------
    account_totals = PartnerCapitalAccount.objects.aggregate(
        balance=Sum('token_balance'),
        locked=Sum('locked_tokens'),
        invested=Sum('total_tokens_invested'),
        earned=Sum('total_tokens_earned'),
        purchased=Sum('total_tokens_purchased'),
        count=Count('id'),
    )
    total_tokens_purchased = account_totals['purchased'] or Decimal('0')   # lifetime, incl. bonus
    total_tokens_earned    = account_totals['earned'] or Decimal('0')      # returns / referral bonuses
    total_tokens_issued    = total_tokens_purchased + total_tokens_earned  # everything ever credited
    tokens_in_circulation  = account_totals['balance'] or Decimal('0')     # still held = issued − withdrawn
    tokens_locked          = account_totals['locked'] or Decimal('0')
    tokens_available       = tokens_in_circulation - tokens_locked
    total_accounts         = account_totals['count'] or 0
    funded_accounts        = PartnerCapitalAccount.objects.filter(token_balance__gt=0).count()

    # Payment flow — money actually collected via paid token purchases (Paystack).
    # Tokens may also be issued without a payment (admin grants / migrations), so
    # these revenue figures cover only purchases made through the payment flow.
    paid_purchases = TokenPurchase.objects.filter(status='successful')
    paid_totals = paid_purchases.aggregate(
        ngn=Sum('amount_ngn'), usd=Sum('amount_usd'), count=Count('id'),
    )
    total_purchase_ngn     = paid_totals['ngn'] or Decimal('0')
    total_purchase_usd     = paid_totals['usd'] or Decimal('0')
    paid_purchase_count    = paid_totals['count'] or 0
    pending_purchase_count = TokenPurchase.objects.filter(status__in=['pending', 'processing']).count()
    failed_purchase_count  = TokenPurchase.objects.filter(status='failed').count()

    total_partners    = PartnerProfile.objects.count()
    verified_partners = PartnerProfile.objects.filter(accreditation_status='verified').count()

    # ------------------------------------------------------------------
    # INVESTMENTS  (tokens deployed into ventures / projects)
    # ------------------------------------------------------------------
    invest_all = VentureInvestment.objects.aggregate(
        tokens=Sum('tokens_invested'),
        expected=Sum('expected_return'),
        count=Count('id'),
    )
    total_tokens_invested   = invest_all['tokens'] or Decimal('0')
    total_expected_return   = invest_all['expected'] or Decimal('0')
    total_investment_count  = invest_all['count'] or 0
    total_expected_interest = total_expected_return - total_tokens_invested

    active_invest = VentureInvestment.objects.filter(status='active').aggregate(
        tokens=Sum('tokens_invested'), count=Count('id'),
    )
    active_invested_tokens = active_invest['tokens'] or Decimal('0')
    active_investment_count = active_invest['count'] or 0

    matured_invest = VentureInvestment.objects.filter(status='matured').aggregate(
        tokens=Sum('tokens_invested'), actual=Sum('actual_return'), count=Count('id'),
    )
    matured_tokens = matured_invest['tokens'] or Decimal('0')
    matured_actual_return = matured_invest['actual'] or Decimal('0')
    matured_count = matured_invest['count'] or 0

    unique_investors = VentureInvestment.objects.values('partner_id').distinct().count()
    avg_investment_size = (total_tokens_invested / total_investment_count) if total_investment_count else Decimal('0')

    investments_by_status = {
        item['status']: {'count': item['c'], 'tokens': item['t'] or 0}
        for item in VentureInvestment.objects.values('status').annotate(
            c=Count('id'), t=Sum('tokens_invested')
        )
    }

    # ------------------------------------------------------------------
    # PARTNER WITHDRAWALS  (tokens cashed out to NGN)
    # ------------------------------------------------------------------
    completed_wd = TokenWithdrawal.objects.filter(status='completed').aggregate(
        tokens=Sum('tokens'), ngn=Sum('amount_ngn'), fee=Sum('fee'), count=Count('id'),
    )
    wd_completed_tokens = completed_wd['tokens'] or Decimal('0')
    wd_completed_ngn    = completed_wd['ngn'] or Decimal('0')
    wd_fees_collected   = completed_wd['fee'] or Decimal('0')
    wd_completed_count  = completed_wd['count'] or 0

    pending_wd = TokenWithdrawal.objects.filter(status__in=['pending', 'approved', 'processing']).aggregate(
        tokens=Sum('tokens'), ngn=Sum('amount_ngn'), count=Count('id'),
    )
    wd_pending_tokens = pending_wd['tokens'] or Decimal('0')
    wd_pending_count  = pending_wd['count'] or 0

    # ------------------------------------------------------------------
    # VENTURE-FOUNDER WITHDRAWALS  (founders cashing out raised SRT)
    # ------------------------------------------------------------------
    vtw_completed = VentureTokenWithdrawal.objects.filter(status='completed').aggregate(
        tokens=Sum('tokens'), ngn=Sum('amount_ngn'), fee=Sum('fee'), count=Count('id'),
    )
    vtw_completed_tokens = vtw_completed['tokens'] or Decimal('0')
    vtw_completed_ngn    = vtw_completed['ngn'] or Decimal('0')
    vtw_fees             = vtw_completed['fee'] or Decimal('0')
    vtw_pending_count    = VentureTokenWithdrawal.objects.filter(
        status__in=['pending', 'approved', 'processing']
    ).count()

    # ------------------------------------------------------------------
    # VENTURES / PROJECTS RAISING SRT
    # ------------------------------------------------------------------
    project_srt = Project.objects.filter(srt_amount_raised__gt=0).aggregate(
        raised=Sum('srt_amount_raised'), count=Count('id'),
    )
    total_srt_raised_projects = project_srt['raised'] or Decimal('0')
    projects_raising_srt = project_srt['count'] or 0

    legacy_ventures_total = Venture.objects.count()
    legacy_ventures_by_status = {
        item['status']: item['c']
        for item in Venture.objects.values('status').annotate(c=Count('id'))
    }
    legacy_raised = Venture.objects.aggregate(t=Sum('amount_raised'))['t'] or Decimal('0')

    # ------------------------------------------------------------------
    # TOP TABLES
    # ------------------------------------------------------------------
    top_partners = PartnerCapitalAccount.objects.select_related('partner').order_by('-token_balance')[:10]

    top_projects_srt = (
        Project.objects.filter(srt_amount_raised__gt=0)
        .order_by('-srt_amount_raised')[:10]
    )

    recent_transactions = SRTTransaction.objects.select_related(
        'account__partner', 'venture', 'project'
    ).order_by('-created_at')[:15]

    recent_purchases = TokenPurchase.objects.select_related('partner', 'package').order_by('-created_at')[:8]

    # ------------------------------------------------------------------
    # CHART DATA
    # ------------------------------------------------------------------
    # Paid token purchases (tokens credited via payment) over last 30 days
    purchase_series = (
        paid_purchases.filter(created_at__gte=thirty_days_ago)
        .annotate(date=TruncDate('created_at'))
        .values('date')
        .annotate(tokens=Sum('tokens'), bonus=Sum('bonus_tokens'))
        .order_by('date')
    )
    purchase_chart = json.dumps([
        {'date': i['date'].strftime('%Y-%m-%d'),
         'tokens': float((i['tokens'] or 0) + (i['bonus'] or 0))}
        for i in purchase_series
    ])

    # Investments over last 30 days
    investment_series = (
        VentureInvestment.objects.filter(created_at__gte=thirty_days_ago)
        .annotate(date=TruncDate('created_at'))
        .values('date')
        .annotate(tokens=Sum('tokens_invested'))
        .order_by('date')
    )
    investment_chart = json.dumps([
        {'date': i['date'].strftime('%Y-%m-%d'), 'tokens': float(i['tokens'] or 0)}
        for i in investment_series
    ])

    # Token flow distribution (where the tokens are)
    flow_chart = json.dumps([
        {'label': 'Available (idle)', 'value': float(max(tokens_available, Decimal('0')))},
        {'label': 'Locked in investments', 'value': float(tokens_locked)},
        {'label': 'Withdrawn (cashed out)', 'value': float(wd_completed_tokens + vtw_completed_tokens)},
    ])

    # Transaction type breakdown (absolute token volume)
    tx_type_series = (
        SRTTransaction.objects.values('transaction_type')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    tx_type_chart = json.dumps([
        {'type': dict(SRTTransaction.TRANSACTION_TYPES).get(i['transaction_type'], i['transaction_type']),
         'count': i['count']}
        for i in tx_type_series
    ])

    # Monthly token purchase revenue (last 6 months)
    monthly_purchase_series = (
        paid_purchases.filter(created_at__gte=now - timedelta(days=180))
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(ngn=Sum('amount_ngn'), usd=Sum('amount_usd'), count=Count('id'))
        .order_by('month')
    )
    monthly_purchase_chart = json.dumps([
        {'month': i['month'].strftime('%b %Y'),
         'ngn': float(i['ngn'] or 0), 'usd': float(i['usd'] or 0), 'count': i['count']}
        for i in monthly_purchase_series
    ])

    context = {
        # Supply / purchases
        'total_tokens_purchased':   total_tokens_purchased,
        'total_tokens_issued':      total_tokens_issued,
        'total_purchase_ngn':       total_purchase_ngn,
        'total_purchase_usd':       total_purchase_usd,
        'paid_purchase_count':      paid_purchase_count,
        'pending_purchase_count':   pending_purchase_count,
        'failed_purchase_count':    failed_purchase_count,

        # Circulation
        'tokens_in_circulation':    tokens_in_circulation,
        'tokens_locked':            tokens_locked,
        'tokens_available':         tokens_available,
        'total_tokens_earned':      total_tokens_earned,
        'total_accounts':           total_accounts,
        'funded_accounts':          funded_accounts,
        'total_partners':           total_partners,
        'verified_partners':        verified_partners,

        # Investments
        'total_tokens_invested':    total_tokens_invested,
        'total_expected_return':    total_expected_return,
        'total_expected_interest':  total_expected_interest,
        'total_investment_count':   total_investment_count,
        'active_invested_tokens':   active_invested_tokens,
        'active_investment_count':  active_investment_count,
        'matured_tokens':           matured_tokens,
        'matured_actual_return':    matured_actual_return,
        'matured_count':            matured_count,
        'unique_investors':         unique_investors,
        'avg_investment_size':      avg_investment_size,
        'investments_by_status':    investments_by_status,

        # Partner withdrawals
        'wd_completed_tokens':      wd_completed_tokens,
        'wd_completed_ngn':         wd_completed_ngn,
        'wd_fees_collected':        wd_fees_collected,
        'wd_completed_count':       wd_completed_count,
        'wd_pending_tokens':        wd_pending_tokens,
        'wd_pending_count':         wd_pending_count,

        # Venture-founder withdrawals
        'vtw_completed_tokens':     vtw_completed_tokens,
        'vtw_completed_ngn':        vtw_completed_ngn,
        'vtw_fees':                 vtw_fees,
        'vtw_pending_count':        vtw_pending_count,

        # Ventures / projects
        'total_srt_raised_projects': total_srt_raised_projects,
        'projects_raising_srt':     projects_raising_srt,
        'legacy_ventures_total':    legacy_ventures_total,
        'legacy_ventures_by_status': legacy_ventures_by_status,
        'legacy_raised':            legacy_raised,

        # Tables
        'top_partners':             top_partners,
        'top_projects_srt':         top_projects_srt,
        'recent_transactions':      recent_transactions,
        'recent_purchases':         recent_purchases,

        # Charts
        'purchase_chart':           purchase_chart,
        'investment_chart':         investment_chart,
        'flow_chart':               flow_chart,
        'tx_type_chart':            tx_type_chart,
        'monthly_purchase_chart':   monthly_purchase_chart,
    }

    return render(request, 'core/srt_analytics.html', context)
