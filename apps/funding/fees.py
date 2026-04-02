"""
Fee calculations for investment transactions on the StartUpRipple platform.

Payment Processing (Local):
  1.5% + ₦100 flat fee
  ₦100 waived for transactions < ₦2,500
  Capped at ₦2,000 per transaction

Payment Processing (International):
  3.9% + ₦100 flat fee
  (No cap stated)

Platform Admin:
  2% of the gross NGN transaction amount

All monetary values are in NGN (Naira) unless stated otherwise.
"""
from decimal import Decimal, ROUND_HALF_UP

NGN_PER_USD = Decimal('1600')
NGN_PER_SRT = Decimal('2000')   # 1 SRT = ₦2,000

PAYSTACK_LOCAL_RATE     = Decimal('0.015')
PAYSTACK_INTL_RATE      = Decimal('0.039')
PAYSTACK_FLAT_FEE       = Decimal('100')
PAYSTACK_FLAT_THRESHOLD = Decimal('2500')   # ₦100 waived if amount < this
PAYSTACK_LOCAL_CAP      = Decimal('2000')   # max Paystack fee for local txns

ADMIN_RATE = Decimal('0.02')    # 2% platform admin fee


def paystack_fee_ngn(amount_ngn: Decimal, is_international: bool = False) -> Decimal:
    """
    Calculate Paystack's fee in NGN for a given transaction gross amount.
    """
    amount_ngn = Decimal(str(amount_ngn))
    if is_international:
        fee = PAYSTACK_INTL_RATE * amount_ngn + PAYSTACK_FLAT_FEE
    else:
        flat = PAYSTACK_FLAT_FEE if amount_ngn >= PAYSTACK_FLAT_THRESHOLD else Decimal('0')
        fee = PAYSTACK_LOCAL_RATE * amount_ngn + flat
        fee = min(fee, PAYSTACK_LOCAL_CAP)
    return fee.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def admin_fee_ngn(amount_ngn: Decimal) -> Decimal:
    """2% platform admin fee on the gross NGN amount."""
    return (ADMIN_RATE * Decimal(str(amount_ngn))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def total_fee_ngn(amount_ngn: Decimal, is_international: bool = False) -> Decimal:
    """Total fee = Paystack fee + admin fee."""
    return paystack_fee_ngn(amount_ngn, is_international) + admin_fee_ngn(amount_ngn)


def gross_up_ngn(net_amount_ngn: Decimal, is_international: bool = False) -> Decimal:
    """
    Calculate the total amount to charge the payer so that after Paystack
    deducts its processing fee, exactly net_amount_ngn remains.
    The payer bears the processing fee; the platform/founder is not affected.
    """
    net = Decimal(str(net_amount_ngn))

    if is_international:
        # fee = 3.9% * charged + ₦100  →  charged = (net + 100) / 0.961
        charged = (net + PAYSTACK_FLAT_FEE) / (1 - PAYSTACK_INTL_RATE)
    else:
        # First try without flat fee (applies when charged < ₦2,500)
        charged_no_flat = net / (1 - PAYSTACK_LOCAL_RATE)
        if charged_no_flat < PAYSTACK_FLAT_THRESHOLD:
            charged = charged_no_flat
        else:
            # Flat fee applies: fee = 1.5% * charged + ₦100
            charged_with_flat = (net + PAYSTACK_FLAT_FEE) / (1 - PAYSTACK_LOCAL_RATE)
            if PAYSTACK_LOCAL_RATE * charged_with_flat + PAYSTACK_FLAT_FEE > PAYSTACK_LOCAL_CAP:
                # Fee would exceed cap — just add the capped fee flat
                charged = net + PAYSTACK_LOCAL_CAP
            else:
                charged = charged_with_flat

    return charged.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def processing_fee_for_payer_ngn(net_amount_ngn: Decimal, is_international: bool = False) -> Decimal:
    """The extra amount the payer will be charged to cover the processing fee."""
    return gross_up_ngn(net_amount_ngn, is_international) - Decimal(str(net_amount_ngn))


def net_ngn(amount_ngn: Decimal, is_international: bool = False) -> Decimal:
    """Net amount founder receives after all fees, in NGN."""
    gross = Decimal(str(amount_ngn))
    return max(Decimal('0'), gross - total_fee_ngn(gross, is_international))


def net_usd(amount_ngn: Decimal, is_international: bool = False) -> Decimal:
    """Net amount founder receives after all fees, converted to USD."""
    return (net_ngn(amount_ngn, is_international) / NGN_PER_USD).quantize(
        Decimal('0.01'), rounding=ROUND_HALF_UP
    )


def investment_ngn(investment) -> Decimal:
    """
    Return the gross NGN amount for a funding.Investment record.
    Uses stored amount_ngn when available (and sensible), otherwise derives it.
    """
    if investment.amount_ngn and investment.amount_ngn > 0:
        return Decimal(str(investment.amount_ngn))
    return Decimal(str(investment.amount)) * NGN_PER_USD


def srt_investment_ngn(tokens: Decimal) -> Decimal:
    """Gross NGN value of an SRT token investment (1 SRT = ₦2,000)."""
    return Decimal(str(tokens)) * NGN_PER_SRT


def platform_fee_summary():
    """
    Compute cumulative fee totals across ALL projects on the platform.
    Used by the analytics dashboard.

    Returns a dict with the same keys as summarise_project_fees plus:
        total_transactions   – number of individual transactions processed
    """
    from apps.funding.models import Investment

    COUNTING_STATUSES = ('pending_approval', 'active', 'approved', 'completed')

    direct_investments = Investment.objects.filter(
        status__in=COUNTING_STATUSES,
    )

    try:
        from apps.srt.models import VentureInvestment
        srt_investments = VentureInvestment.objects.filter(
            status__in=('active', 'matured'),
        )
    except Exception:
        srt_investments = []

    adm_fees  = Decimal('0')
    gross_direct = Decimal('0')
    gross_srt    = Decimal('0')
    txn_count = 0

    for inv in direct_investments:
        g = investment_ngn(inv)
        gross_direct += g
        adm_fees += admin_fee_ngn(g)
        txn_count += 1

    for inv in srt_investments:
        g = srt_investment_ngn(inv.tokens_invested)
        gross_srt += g
        adm_fees += admin_fee_ngn(g)
        txn_count += 1

    gross_total = gross_direct + gross_srt
    net_total   = max(Decimal('0'), gross_total - adm_fees)

    def to_usd(ngn):
        return (ngn / NGN_PER_USD).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    return {
        'gross_direct_ngn':  gross_direct.quantize(Decimal('0.01')),
        'gross_srt_ngn':     gross_srt.quantize(Decimal('0.01')),
        'gross_total_ngn':   gross_total.quantize(Decimal('0.01')),
        'admin_fees_ngn':    adm_fees.quantize(Decimal('0.01')),
        'total_fees_ngn':    adm_fees.quantize(Decimal('0.01')),
        'net_total_ngn':     net_total.quantize(Decimal('0.01')),
        'net_total_usd':     to_usd(net_total),
        'gross_direct_usd':  to_usd(gross_direct),
        'gross_srt_usd':     to_usd(gross_srt),
        'gross_total_usd':   to_usd(gross_total),
        'admin_fees_usd':    to_usd(adm_fees),
        'total_fees_usd':    to_usd(adm_fees),
        'total_transactions': txn_count,
    }


def summarise_project_fees(project):
    """
    Compute a full fee breakdown for a project's investments.

    Returns a dict:
        gross_direct_ngn      – NGN received from direct fiat investments
        gross_srt_ngn         – NGN equivalent of SRT investments
        gross_total_ngn       – combined gross NGN
        paystack_fees_ngn     – total Paystack fees across all transactions
        admin_fees_ngn        – total admin fees across all transactions
        total_fees_ngn        – combined fees
        net_total_ngn         – gross - fees
        net_total_usd         – net converted to USD
        gross_direct_usd      – gross direct / 1600
        gross_srt_usd         – gross SRT / 1600
        gross_total_usd       – gross total / 1600
    """
    from apps.funding.models import Investment

    COUNTING_STATUSES = ('pending_approval', 'active', 'approved', 'completed')

    direct_investments = Investment.objects.filter(
        project=project,
        status__in=COUNTING_STATUSES,
    )

    # SRT investments linked to this project
    try:
        from apps.srt.models import VentureInvestment
        srt_investments = VentureInvestment.objects.filter(
            project=project,
            status__in=('active', 'matured'),
        )
    except Exception:
        srt_investments = []

    ps_fees   = Decimal('0')
    adm_fees  = Decimal('0')
    gross_direct = Decimal('0')
    gross_srt    = Decimal('0')

    for inv in direct_investments:
        g = investment_ngn(inv)
        gross_direct += g
        adm_fees += admin_fee_ngn(g)

    for inv in srt_investments:
        g = srt_investment_ngn(inv.tokens_invested)
        gross_srt += g
        adm_fees += admin_fee_ngn(g)

    gross_total = gross_direct + gross_srt
    total_fees  = adm_fees
    net_total   = max(Decimal('0'), gross_total - total_fees)

    def to_usd(ngn):
        return (ngn / NGN_PER_USD).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    return {
        'gross_direct_ngn':  gross_direct.quantize(Decimal('0.01')),
        'gross_srt_ngn':     gross_srt.quantize(Decimal('0.01')),
        'gross_total_ngn':   gross_total.quantize(Decimal('0.01')),
        'admin_fees_ngn':    adm_fees.quantize(Decimal('0.01')),
        'total_fees_ngn':    adm_fees.quantize(Decimal('0.01')),
        'net_total_ngn':     net_total.quantize(Decimal('0.01')),
        'net_total_usd':     to_usd(net_total),
        'gross_direct_usd':  to_usd(gross_direct),
        'gross_srt_usd':     to_usd(gross_srt),
        'gross_total_usd':   to_usd(gross_total),
    }
