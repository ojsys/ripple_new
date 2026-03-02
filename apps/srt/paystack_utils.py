"""
Paystack Transfer Utility for SRT Withdrawals

Handles automatic bank transfers when admin approves a withdrawal.
Flow:
  1. create_transfer_recipient()  → Paystack recipient code
  2. initiate_transfer()          → Paystack transfer code
  3. Webhook: transfer.success    → complete withdrawal
             transfer.failed     → revert to 'approved' so admin can retry
"""

import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


# Paystack bank codes for all banks in TokenWithdrawal.ALL_BANK_CHOICES
PAYSTACK_BANK_CODES = {
    # Commercial Banks
    'access':             '044',
    'citibank':           '023',
    'ecobank':            '050',
    'fidelity':           '070',
    'first':              '011',
    'fcmb':               '214',
    'globus':             '00103',
    'gtbank':             '058',
    'heritage':           '030',
    'keystone':           '082',
    'optimus':            '107',
    'polaris':            '076',
    'providus':           '101',
    'stanbic':            '221',
    'standard_chartered': '068',
    'sterling':           '232',
    'suntrust':           '100',
    'titan':              '102',
    'union':              '032',
    'uba':                '033',
    'unity':              '215',
    'wema':               '035',
    'zenith':             '057',
    # Non-Interest (Islamic) Banks
    'jaiz':               '301',
    'taj':                '302',
    'lotus':              '303',
    # Payment Service Banks
    '9psb':               '120001',
    'hope_psb':           '120002',
    'kuda':               '50211',
    'money_master':       '120003',
    'moniepoint':         '50515',
    'opay':               '999992',
    'palmpay':            '999991',
    'paga':               '100002',
    # Microfinance Banks
    'ab_mfb':             '51204',
    'accion_mfb':         '602',
    'aella_mfb':          '50131',
    'alat_mfb':           '035A',
    'branch_mfb':         '50718',
    'carbon':             '565',
    'eyowo':              '50126',
    'fairmoney':          '51318',
    'flutterwave':        '110012',
    'gomoney':            '100022',
    'lapo_mfb':           '50017',
    'mint_mfb':           '50304',
    'moniepoint':         '50515',
    'npf_mfb':            '070001',
    'parallex_mfb':       '526',
    'piggyvest':          '100033',
    'renmoney':           '50200',
    'rubies_mfb':         '125',
    'safe_haven_mfb':     '51113',
    'sparkle_mfb':        '51310',
    'vfd_mfb':            '566',
    'zedvance_mfb':       '100034',
}


def get_bank_code(bank_name_key):
    """Return the Paystack bank code for a given bank choice key, or None."""
    return PAYSTACK_BANK_CODES.get(bank_name_key)


def create_transfer_recipient(bank_code, account_number, account_name):
    """
    Register a bank account as a Paystack transfer recipient.
    Returns (recipient_code, error_message).
    """
    url = 'https://api.paystack.co/transferrecipient'
    headers = {
        'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
        'Content-Type': 'application/json',
    }
    payload = {
        'type': 'nuban',
        'name': account_name,
        'account_number': account_number,
        'bank_code': bank_code,
        'currency': 'NGN',
    }
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=30)
        data = resp.json()
        if data.get('status') and data.get('data', {}).get('recipient_code'):
            return data['data']['recipient_code'], None
        return None, data.get('message', 'Failed to create transfer recipient')
    except Exception as exc:
        logger.exception("Paystack create_transfer_recipient failed: %s", exc)
        return None, str(exc)


def initiate_transfer(amount_ngn, recipient_code, reason, reference):
    """
    Initiate a Paystack NGN transfer.
    amount_ngn  – amount in Naira (will be converted to kobo).
    Returns (transfer_code, error_message).
    """
    url = 'https://api.paystack.co/transfer'
    headers = {
        'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
        'Content-Type': 'application/json',
    }
    amount_kobo = int(float(amount_ngn) * 100)
    payload = {
        'source': 'balance',
        'amount': amount_kobo,
        'recipient': recipient_code,
        'reason': reason,
        'reference': reference,
    }
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=30)
        data = resp.json()
        if data.get('status'):
            transfer_code = data.get('data', {}).get('transfer_code', reference)
            return transfer_code, None
        return None, data.get('message', 'Transfer initiation failed')
    except Exception as exc:
        logger.exception("Paystack initiate_transfer failed: %s", exc)
        return None, str(exc)


def initiate_withdrawal_transfer(withdrawal):
    """
    Full transfer flow for a withdrawal (TokenWithdrawal or VentureTokenWithdrawal):
      1. Resolve Paystack bank code from withdrawal.bank_name
      2. Create transfer recipient
      3. Initiate transfer

    Returns (success: bool, transfer_code: str | None, error: str | None).
    On success the caller should set withdrawal.status = 'processing'
    and withdrawal.payment_reference = transfer_code.
    """
    bank_code = get_bank_code(withdrawal.bank_name)
    if not bank_code:
        return False, None, (
            f"Bank '{withdrawal.get_bank_name_display()}' has no Paystack code configured. "
            "Please process this transfer manually."
        )

    recipient_code, error = create_transfer_recipient(
        bank_code=bank_code,
        account_number=withdrawal.account_number,
        account_name=withdrawal.account_name,
    )
    if error:
        return False, None, f"Recipient creation failed: {error}"

    transfer_code, error = initiate_transfer(
        amount_ngn=withdrawal.amount_ngn,
        recipient_code=recipient_code,
        reason=f"StartUpRipple payout – {withdrawal.reference}",
        reference=withdrawal.reference,
    )
    if error:
        return False, None, f"Transfer initiation failed: {error}"

    return True, transfer_code, None
