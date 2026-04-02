"""
Paystack Transfer API integration for founder withdrawal payouts.

Flow:
  1. fetch_banks()               – list of Nigerian banks from Paystack (cached 24h)
  2. resolve_account()           – verify account number and return account name
  3. create_transfer_recipient() – register bank account with Paystack
  4. initiate_transfer()         – send money to the recipient
  5. verify_transfer()           – check transfer status
  6. process_withdrawal()        – full end-to-end payout for a withdrawal record
"""
import requests
from decimal import Decimal
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

PAYSTACK_BASE = 'https://api.paystack.co'
BANKS_CACHE_KEY = 'paystack_ngn_banks'
BANKS_CACHE_TTL = 60 * 60 * 24  # 24 hours


def _headers():
    return {
        'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
        'Content-Type': 'application/json',
    }


def fetch_banks():
    """
    Return list of Nigerian banks from Paystack as (code, name) tuples.
    Cached for 24 hours to avoid repeated API calls.
    """
    cached = cache.get(BANKS_CACHE_KEY)
    if cached is not None:
        return cached

    try:
        response = requests.get(
            f'{PAYSTACK_BASE}/bank',
            params={'currency': 'NGN', 'per_page': 200, 'use_cursor': False},
            headers=_headers(),
            timeout=15,
        )
        data = response.json()
        if data.get('status') and data.get('data'):
            banks = sorted(
                [(b['code'], b['name']) for b in data['data']],
                key=lambda x: x[1]
            )
            cache.set(BANKS_CACHE_KEY, banks, BANKS_CACHE_TTL)
            return banks
    except Exception:
        pass

    return []


def resolve_account(account_number, bank_code):
    """
    Verify a bank account number and return the registered account name.
    Returns (account_name, error_message).
    """
    try:
        response = requests.get(
            f'{PAYSTACK_BASE}/bank/resolve',
            params={'account_number': account_number, 'bank_code': bank_code},
            headers=_headers(),
            timeout=15,
        )
        data = response.json()
        if data.get('status') and data.get('data'):
            return data['data'].get('account_name', ''), None
        return None, data.get('message', 'Could not resolve account')
    except Exception as e:
        return None, str(e)


def create_transfer_recipient(account_name, account_number, bank_code):
    """
    Register a bank account as a Paystack transfer recipient.
    Returns (recipient_code, error_message).
    """
    try:
        response = requests.post(
            f'{PAYSTACK_BASE}/transferrecipient',
            json={
                'type': 'nuban',
                'name': account_name,
                'account_number': account_number,
                'bank_code': bank_code,
                'currency': 'NGN',
            },
            headers=_headers(),
            timeout=30,
        )
        data = response.json()
        if data.get('status') and data.get('data'):
            return data['data']['recipient_code'], None
        return None, data.get('message', 'Failed to create transfer recipient')
    except Exception as e:
        return None, str(e)


def initiate_transfer(amount_ngn, recipient_code, reference, reason='Withdrawal'):
    """
    Initiate a Paystack transfer to an existing recipient.
    Returns (transfer_code, error_message).
    """
    try:
        amount_kobo = int(Decimal(str(amount_ngn)) * 100)
        response = requests.post(
            f'{PAYSTACK_BASE}/transfer',
            json={
                'source': 'balance',
                'amount': amount_kobo,
                'recipient': recipient_code,
                'reason': reason,
                'reference': reference,
            },
            headers=_headers(),
            timeout=30,
        )
        data = response.json()
        if data.get('status') and data.get('data'):
            return data['data'].get('transfer_code', ''), None
        return None, data.get('message', 'Failed to initiate transfer')
    except Exception as e:
        return None, str(e)


def verify_transfer(transfer_code):
    """
    Check the status of a Paystack transfer.
    Returns (status_string, error_message).
    """
    try:
        response = requests.get(
            f'{PAYSTACK_BASE}/transfer/{transfer_code}',
            headers=_headers(),
            timeout=15,
        )
        data = response.json()
        if data.get('status') and data.get('data'):
            return data['data'].get('status', 'unknown'), None
        return None, data.get('message', 'Could not verify transfer')
    except Exception as e:
        return None, str(e)


def get_bank_code(bank_name):
    """
    Look up the Paystack bank code for a given bank name.
    Returns the code string, or None if not found.
    """
    banks = fetch_banks()
    name_lower = bank_name.strip().lower()
    for code, name in banks:
        if name.lower() == name_lower:
            return code
    # Partial match fallback
    for code, name in banks:
        if name_lower in name.lower() or name.lower() in name_lower:
            return code
    return None


def process_withdrawal(withdrawal):
    """
    Full payout flow for a FounderWithdrawalRequest:
      1. Resolve bank code from bank name if not already stored
      2. Create Paystack transfer recipient (or reuse stored code)
      3. Initiate transfer
      4. Update withdrawal record

    Returns (success: bool, message: str).
    """
    # Step 1: ensure we have a bank code
    if not withdrawal.bank_code:
        code = get_bank_code(withdrawal.bank_name)
        if not code:
            return False, (
                f'Could not find Paystack bank code for "{withdrawal.bank_name}". '
                'Please update the bank name to match Paystack exactly, or enter the code manually.'
            )
        withdrawal.bank_code = code
        withdrawal.save(update_fields=['bank_code'])

    # Step 2: get or create recipient
    if not withdrawal.paystack_recipient_code:
        recipient_code, err = create_transfer_recipient(
            account_name=withdrawal.account_name,
            account_number=withdrawal.account_number,
            bank_code=withdrawal.bank_code,
        )
        if err:
            return False, f'Paystack recipient error: {err}'
        withdrawal.paystack_recipient_code = recipient_code
        withdrawal.save(update_fields=['paystack_recipient_code'])

    # Step 3: initiate transfer
    transfer_code, err = initiate_transfer(
        amount_ngn=withdrawal.amount_ngn,
        recipient_code=withdrawal.paystack_recipient_code,
        reference=withdrawal.reference,
        reason=f'StartUpRipple withdrawal — {withdrawal.project.title}',
    )
    if err:
        return False, f'Paystack transfer error: {err}'

    # Step 4: update record
    withdrawal.paystack_transfer_code = transfer_code
    withdrawal.transfer_initiated_at = timezone.now()
    withdrawal.status = 'processing'
    withdrawal.save(update_fields=[
        'paystack_transfer_code', 'transfer_initiated_at', 'status'
    ])

    return True, f'Transfer initiated. Code: {transfer_code}'
