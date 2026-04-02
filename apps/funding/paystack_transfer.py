"""
Paystack Transfer API integration for founder withdrawal payouts.

Flow:
  1. create_transfer_recipient()  – registers the founder's bank account with Paystack
  2. initiate_transfer()          – sends money to the recipient
  3. verify_transfer()            – checks transfer status (also called from webhook)
"""
import requests
from decimal import Decimal
from django.conf import settings
from django.utils import timezone

PAYSTACK_BASE = 'https://api.paystack.co'


def _headers():
    return {
        'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
        'Content-Type': 'application/json',
    }


def create_transfer_recipient(account_name, account_number, bank_code):
    """
    Register a bank account as a Paystack transfer recipient.
    Returns (recipient_code, error_message).
    """
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


def initiate_transfer(amount_ngn, recipient_code, reference, reason='Withdrawal'):
    """
    Initiate a Paystack transfer to an existing recipient.
    amount_ngn should be a Decimal or float (NOT kobo — we convert here).
    Returns (transfer_code, error_message).
    """
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


def verify_transfer(transfer_code):
    """
    Check the status of a transfer.
    Returns the Paystack status string e.g. 'success', 'failed', 'pending'.
    """
    response = requests.get(
        f'{PAYSTACK_BASE}/transfer/{transfer_code}',
        headers=_headers(),
        timeout=30,
    )
    data = response.json()
    if data.get('status') and data.get('data'):
        return data['data'].get('status', 'unknown'), None
    return None, data.get('message', 'Could not verify transfer')


def process_withdrawal(withdrawal):
    """
    Full payout flow for a FounderWithdrawalRequest:
      1. Create recipient (or reuse stored code)
      2. Initiate transfer
      3. Update withdrawal record

    Returns (success: bool, message: str).
    """
    # Step 1: get or create recipient
    if not withdrawal.paystack_recipient_code:
        if not withdrawal.bank_code:
            return False, 'Bank code is missing. Ask the founder to re-submit with bank code.'

        recipient_code, err = create_transfer_recipient(
            account_name=withdrawal.account_name,
            account_number=withdrawal.account_number,
            bank_code=withdrawal.bank_code,
        )
        if err:
            return False, f'Paystack recipient error: {err}'

        withdrawal.paystack_recipient_code = recipient_code
        withdrawal.save(update_fields=['paystack_recipient_code'])

    # Step 2: initiate transfer
    transfer_code, err = initiate_transfer(
        amount_ngn=withdrawal.amount_ngn,
        recipient_code=withdrawal.paystack_recipient_code,
        reference=withdrawal.reference,
        reason=f'StartUpRipple withdrawal — {withdrawal.project.title}',
    )
    if err:
        return False, f'Paystack transfer error: {err}'

    # Step 3: update record
    withdrawal.paystack_transfer_code = transfer_code
    withdrawal.transfer_initiated_at = timezone.now()
    withdrawal.status = 'processing'
    withdrawal.save(update_fields=[
        'paystack_transfer_code', 'transfer_initiated_at', 'status'
    ])

    return True, f'Transfer initiated. Code: {transfer_code}'
