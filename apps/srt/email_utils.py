"""
Email notification utilities for SRT (StartUpRipple Tokens) system.
Handles sending email notifications for token purchases, withdrawals, and other SRT events.
"""
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
import logging
from apps.core.email_templates import (
    get_base_email_template, get_info_box, get_warning_box,
    get_success_box, get_highlight_box, get_account_box, ICONS
)

logger = logging.getLogger(__name__)

# Admin email for notifications
ADMIN_EMAIL = getattr(settings, 'ADMIN_EMAIL', 'admin@startupripple.com')
ADMIN_EMAILS = getattr(settings, 'ADMIN_EMAILS', [ADMIN_EMAIL])
SITE_URL = getattr(settings, 'SITE_URL', 'https://startupripple.com')


def send_email(subject, html_content, text_content, to_emails, from_email=None):
    """
    Send an email with HTML content.

    Args:
        subject: Email subject
        html_content: HTML version of the email
        text_content: Plain text version of the email
        to_emails: List of recipient emails
        from_email: Sender email (defaults to DEFAULT_FROM_EMAIL)

    Returns:
        bool: True if email sent successfully, False otherwise
    """
    if from_email is None:
        from_email = settings.DEFAULT_FROM_EMAIL

    try:
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=from_email,
            to=to_emails if isinstance(to_emails, list) else [to_emails],
        )
        email.attach_alternative(html_content, "text/html")
        email.send()
        logger.info(f"Email sent successfully to {to_emails}: {subject}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {to_emails}: {str(e)}")
        return False


# ============================================
# TOKEN PURCHASE NOTIFICATIONS
# ============================================

def send_token_purchase_confirmation_to_user(purchase):
    """
    Send token purchase confirmation email to the user.

    Args:
        purchase: TokenPurchase instance
    """
    user = purchase.partner
    user_name = user.first_name or user.email

    subject = f"Token Purchase Confirmed - {purchase.tokens_purchased:,.2f} SRT"

    content = f'''
    <p style="margin: 0 0 25px 0; font-size: 16px; line-height: 1.7; color: #4a5568; text-align: center;">
        Hi <strong style="color: #1a1a2e;">{user_name}</strong>,
    </p>

    <p style="margin: 0 0 25px 0; font-size: 16px; line-height: 1.7; color: #4a5568; text-align: center;">
        Great news! Your token purchase has been successfully processed.
    </p>
    '''

    content += get_highlight_box("Tokens Purchased", f"{purchase.tokens_purchased:,.2f} SRT", "#0d9488")

    content += get_info_box("Purchase Details", [
        ("Reference", purchase.reference),
        ("Amount Paid", f"NGN {purchase.amount_paid:,.2f}"),
        ("Tokens Received", f"{purchase.tokens_purchased:,.2f} SRT"),
        ("Bonus Tokens", f"{purchase.bonus_tokens:,.2f} SRT"),
        ("Date", purchase.created_at.strftime('%B %d, %Y at %H:%M')),
        ("New Balance", f"{purchase.account.token_balance:,.2f} SRT"),
    ], "#0d9488")

    content += get_success_box(
        "<strong>Your tokens are ready!</strong> You can now invest in ventures or withdraw at any time."
    )

    html_content = get_base_email_template(
        title="Token Purchase Confirmed",
        subtitle="Your SRT tokens are ready to use",
        content=content,
        button_text="View Dashboard",
        button_url=f"{SITE_URL}/srt/dashboard/",
        header_color="#0d9488",
        icon=ICONS['check'],
        footer_text="Thank you for investing with StartUpRipple!"
    )

    text_content = f"""
Token Purchase Confirmed - StartUpRipple

Hi {user_name},

Your token purchase has been successfully processed!

Purchase Details:
- Reference: {purchase.reference}
- Amount Paid: NGN {purchase.amount_paid:,.2f}
- Tokens Received: {purchase.tokens_purchased:,.2f} SRT
- Bonus Tokens: {purchase.bonus_tokens:,.2f} SRT
- Date: {purchase.created_at.strftime('%B %d, %Y at %H:%M')}
- New Balance: {purchase.account.token_balance:,.2f} SRT

Your tokens are ready! You can now invest in ventures or withdraw at any time.

View your dashboard: {SITE_URL}/srt/dashboard/

Thank you for investing with StartUpRipple!
    """

    return send_email(subject, html_content, text_content, [user.email])


def send_token_purchase_notification_to_admin(purchase):
    """
    Send token purchase notification to admin.

    Args:
        purchase: TokenPurchase instance
    """
    user = purchase.partner

    subject = f"[ADMIN] New Token Purchase - {purchase.tokens_purchased:,.2f} SRT by {user.email}"

    content = f'''
    <p style="margin: 0 0 25px 0; font-size: 16px; line-height: 1.7; color: #4a5568; text-align: center;">
        A new token purchase has been completed on the platform.
    </p>
    '''

    content += get_highlight_box("Amount Received", f"NGN {purchase.amount_paid:,.2f}", "#1e40af")

    content += get_info_box("Purchase Details", [
        ("Reference", purchase.reference),
        ("Partner", user.get_full_name() or user.email),
        ("Email", user.email),
        ("Amount Paid", f"NGN {purchase.amount_paid:,.2f}"),
        ("Tokens Purchased", f"{purchase.tokens_purchased:,.2f} SRT"),
        ("Bonus Tokens", f"{purchase.bonus_tokens:,.2f} SRT"),
        ("Payment Method", purchase.payment_method or 'Paystack'),
        ("Payment Reference", purchase.payment_reference or 'N/A'),
        ("Date", purchase.created_at.strftime('%B %d, %Y at %H:%M')),
        ("Partner Balance", f"{purchase.account.token_balance:,.2f} SRT"),
    ], "#1e40af")

    html_content = get_base_email_template(
        title="New Token Purchase",
        subtitle="Admin Notification",
        content=content,
        button_text="View in Admin",
        button_url=f"{SITE_URL}/admin/srt/tokenpurchase/",
        header_color="#1e40af",
        icon=ICONS['money'],
        footer_text="This is an automated admin notification."
    )

    text_content = f"""
[ADMIN] New Token Purchase - StartUpRipple

A new token purchase has been completed:

Purchase Details:
- Reference: {purchase.reference}
- Partner: {user.get_full_name() or user.email}
- Email: {user.email}
- Amount Paid: NGN {purchase.amount_paid:,.2f}
- Tokens Purchased: {purchase.tokens_purchased:,.2f} SRT
- Bonus Tokens: {purchase.bonus_tokens:,.2f} SRT
- Payment Method: {purchase.payment_method or 'Paystack'}
- Date: {purchase.created_at.strftime('%B %d, %Y at %H:%M')}

View in admin: {SITE_URL}/admin/srt/tokenpurchase/
    """

    return send_email(subject, html_content, text_content, ADMIN_EMAILS)


# ============================================
# WITHDRAWAL NOTIFICATIONS
# ============================================

def send_withdrawal_request_to_user(withdrawal):
    """
    Send withdrawal request confirmation to user.

    Args:
        withdrawal: TokenWithdrawal instance
    """
    user = withdrawal.partner
    user_name = user.first_name or user.email

    subject = f"Withdrawal Request Received - {withdrawal.tokens:,.2f} SRT"

    content = f'''
    <p style="margin: 0 0 25px 0; font-size: 16px; line-height: 1.7; color: #4a5568; text-align: center;">
        Hi <strong style="color: #1a1a2e;">{user_name}</strong>,
    </p>

    <p style="margin: 0 0 25px 0; font-size: 16px; line-height: 1.7; color: #4a5568; text-align: center;">
        Your withdrawal request has been received and is being processed.
    </p>
    '''

    content += get_highlight_box("Amount to Receive", f"NGN {withdrawal.amount_ngn:,.2f}", "#0d9488")

    content += get_info_box("Withdrawal Details", [
        ("Reference", withdrawal.reference),
        ("Tokens", f"{withdrawal.tokens:,.2f} SRT"),
        ("Processing Fee", f"NGN {withdrawal.fee:,.2f}"),
        ("Amount to Receive", f"NGN {withdrawal.amount_ngn:,.2f}"),
        ("Status", "Pending"),
    ], "#0d9488")

    content += get_info_box("Bank Details", [
        ("Bank", withdrawal.get_bank_name_display()),
        ("Account Number", withdrawal.account_number),
        ("Account Name", withdrawal.account_name),
    ], "#0d9488")

    content += get_warning_box(
        "<strong>What happens next?</strong> Our team will review and process your withdrawal request. "
        "You'll receive an email once the payment is completed."
    )

    html_content = get_base_email_template(
        title="Withdrawal Request Received",
        subtitle="Your request is being processed",
        content=content,
        button_text="Track Withdrawal",
        button_url=f"{SITE_URL}/srt/withdrawal/{withdrawal.reference}/",
        header_color="#0d9488",
        icon=ICONS['bank'],
        footer_text="Thank you for using StartUpRipple!"
    )

    text_content = f"""
Withdrawal Request Received - StartUpRipple

Hi {user_name},

Your withdrawal request has been received and is being processed.

Withdrawal Details:
- Reference: {withdrawal.reference}
- Tokens: {withdrawal.tokens:,.2f} SRT
- Processing Fee: NGN {withdrawal.fee:,.2f}
- Amount to Receive: NGN {withdrawal.amount_ngn:,.2f}
- Status: Pending

Bank Details:
- Bank: {withdrawal.get_bank_name_display()}
- Account Number: {withdrawal.account_number}
- Account Name: {withdrawal.account_name}

Our team will review and process your withdrawal request. You'll receive an email once the payment is completed.

Track your withdrawal: {SITE_URL}/srt/withdrawal/{withdrawal.reference}/
    """

    return send_email(subject, html_content, text_content, [user.email])


def send_withdrawal_request_to_admin(withdrawal):
    """
    Send new withdrawal request notification to admin.

    Args:
        withdrawal: TokenWithdrawal instance
    """
    user = withdrawal.partner

    subject = f"[ADMIN] New Withdrawal Request - NGN {withdrawal.amount_ngn:,.2f} by {user.email}"

    content = f'''
    <p style="margin: 0 0 25px 0; font-size: 16px; line-height: 1.7; color: #4a5568; text-align: center;">
        A new withdrawal request requires your attention.
    </p>
    '''

    content += get_highlight_box("Amount to Pay", f"NGN {withdrawal.amount_ngn:,.2f}", "#dc2626")

    content += get_info_box("Withdrawal Details", [
        ("Reference", withdrawal.reference),
        ("Partner", user.get_full_name() or user.email),
        ("Email", user.email),
        ("Tokens", f"{withdrawal.tokens:,.2f} SRT"),
        ("Fee Deducted", f"NGN {withdrawal.fee:,.2f}"),
        ("Amount to Pay", f"NGN {withdrawal.amount_ngn:,.2f}"),
        ("Date Requested", withdrawal.created_at.strftime('%B %d, %Y at %H:%M')),
    ], "#dc2626")

    content += get_info_box("Bank Details for Payment", [
        ("Bank", withdrawal.get_bank_name_display()),
        ("Account Number", f"<strong>{withdrawal.account_number}</strong>"),
        ("Account Name", f"<strong>{withdrawal.account_name}</strong>"),
    ], "#dc2626")

    content += get_warning_box(
        "<strong>Action Required:</strong> Please review and process this withdrawal request in the admin panel."
    )

    html_content = get_base_email_template(
        title="New Withdrawal Request",
        subtitle="Action Required",
        content=content,
        button_text="Process Withdrawal",
        button_url=f"{SITE_URL}/admin/srt/tokenwithdrawal/{withdrawal.id}/change/",
        header_color="#dc2626",
        icon=ICONS['warning'],
        footer_text="This is an automated admin notification."
    )

    text_content = f"""
[ADMIN] New Withdrawal Request - Action Required

A new withdrawal request requires your attention:

Withdrawal Details:
- Reference: {withdrawal.reference}
- Partner: {user.get_full_name() or user.email}
- Email: {user.email}
- Tokens: {withdrawal.tokens:,.2f} SRT
- Fee Deducted: NGN {withdrawal.fee:,.2f}
- Amount to Pay: NGN {withdrawal.amount_ngn:,.2f}
- Date Requested: {withdrawal.created_at.strftime('%B %d, %Y at %H:%M')}

Bank Details for Payment:
- Bank: {withdrawal.get_bank_name_display()}
- Account Number: {withdrawal.account_number}
- Account Name: {withdrawal.account_name}

Process in admin: {SITE_URL}/admin/srt/tokenwithdrawal/{withdrawal.id}/change/
    """

    return send_email(subject, html_content, text_content, ADMIN_EMAILS)


def send_withdrawal_approved_to_user(withdrawal):
    """
    Send withdrawal approved notification to user.

    Args:
        withdrawal: TokenWithdrawal instance
    """
    user = withdrawal.partner
    user_name = user.first_name or user.email

    subject = f"Withdrawal Approved - {withdrawal.reference}"

    content = f'''
    <p style="margin: 0 0 25px 0; font-size: 16px; line-height: 1.7; color: #4a5568; text-align: center;">
        Hi <strong style="color: #1a1a2e;">{user_name}</strong>,
    </p>

    <p style="margin: 0 0 25px 0; font-size: 16px; line-height: 1.7; color: #4a5568; text-align: center;">
        Great news! Your withdrawal request has been approved and is being processed for payment.
    </p>
    '''

    content += get_highlight_box("Amount to Receive", f"NGN {withdrawal.amount_ngn:,.2f}", "#059669")

    content += get_info_box("Withdrawal Details", [
        ("Reference", withdrawal.reference),
        ("Status", '<span style="color: #059669; font-weight: 600;">Approved</span>'),
        ("Bank", withdrawal.get_bank_name_display()),
        ("Account", withdrawal.account_number),
    ], "#059669")

    content += get_success_box(
        "<strong>Payment is on the way!</strong> You'll receive another email once the payment has been completed."
    )

    html_content = get_base_email_template(
        title="Withdrawal Approved",
        subtitle="Your payment is being processed",
        content=content,
        button_text="Track Withdrawal",
        button_url=f"{SITE_URL}/srt/withdrawal/{withdrawal.reference}/",
        header_color="#059669",
        icon=ICONS['thumbs_up'],
        footer_text="Thank you for using StartUpRipple!"
    )

    text_content = f"""
Withdrawal Approved - StartUpRipple

Hi {user_name},

Great news! Your withdrawal request has been approved.

Details:
- Reference: {withdrawal.reference}
- Amount: NGN {withdrawal.amount_ngn:,.2f}
- Bank: {withdrawal.get_bank_name_display()}
- Account: {withdrawal.account_number}

Payment is being processed. You'll receive another email once completed.
    """

    return send_email(subject, html_content, text_content, [user.email])


def send_withdrawal_completed_to_user(withdrawal):
    """
    Send withdrawal completed notification to user.

    Args:
        withdrawal: TokenWithdrawal instance
    """
    user = withdrawal.partner
    user_name = user.first_name or user.email

    subject = f"Withdrawal Completed - NGN {withdrawal.amount_ngn:,.2f} Sent!"

    content = f'''
    <p style="margin: 0 0 25px 0; font-size: 16px; line-height: 1.7; color: #4a5568; text-align: center;">
        Hi <strong style="color: #1a1a2e;">{user_name}</strong>,
    </p>

    <p style="margin: 0 0 25px 0; font-size: 16px; line-height: 1.7; color: #4a5568; text-align: center;">
        Your withdrawal has been completed! The funds have been sent to your bank account.
    </p>
    '''

    content += get_highlight_box("Amount Sent", f"NGN {withdrawal.amount_ngn:,.2f}", "#059669")

    rows = [
        ("Reference", withdrawal.reference),
        ("Status", '<span style="color: #059669; font-weight: 600;">Completed</span>'),
        ("Tokens Withdrawn", f"{withdrawal.tokens:,.2f} SRT"),
        ("Amount Sent", f"NGN {withdrawal.amount_ngn:,.2f}"),
        ("Bank", withdrawal.get_bank_name_display()),
        ("Account", withdrawal.account_number),
    ]
    if withdrawal.completed_at:
        rows.append(("Completed On", withdrawal.completed_at.strftime('%B %d, %Y at %H:%M')))
    if withdrawal.payment_reference:
        rows.append(("Payment Reference", withdrawal.payment_reference))

    content += get_info_box("Payment Details", rows, "#059669")

    content += get_success_box(
        "<strong>Funds sent successfully!</strong> Please allow 1-24 hours for the funds to reflect "
        "in your bank account depending on your bank."
    )

    html_content = get_base_email_template(
        title="Withdrawal Completed!",
        subtitle="Payment Successful",
        content=content,
        button_text="Go to Dashboard",
        button_url=f"{SITE_URL}/srt/dashboard/",
        header_color="#059669",
        icon=ICONS['celebrate'],
        footer_text="Thank you for being a StartUpRipple partner!"
    )

    text_content = f"""
Withdrawal Completed - StartUpRipple

Hi {user_name},

Your withdrawal has been completed! The funds have been sent to your bank account.

Payment Details:
- Reference: {withdrawal.reference}
- Tokens Withdrawn: {withdrawal.tokens:,.2f} SRT
- Amount Sent: NGN {withdrawal.amount_ngn:,.2f}
- Bank: {withdrawal.get_bank_name_display()}
- Account: {withdrawal.account_number}
- Completed On: {withdrawal.completed_at.strftime('%B %d, %Y at %H:%M') if withdrawal.completed_at else 'N/A'}

Please allow 1-24 hours for the funds to reflect in your bank account.

Thank you for being a StartUpRipple partner!
    """

    return send_email(subject, html_content, text_content, [user.email])


def send_withdrawal_rejected_to_user(withdrawal):
    """
    Send withdrawal rejected notification to user.

    Args:
        withdrawal: TokenWithdrawal instance
    """
    user = withdrawal.partner
    user_name = user.first_name or user.email

    subject = f"Withdrawal Request Declined - {withdrawal.reference}"

    content = f'''
    <p style="margin: 0 0 25px 0; font-size: 16px; line-height: 1.7; color: #4a5568; text-align: center;">
        Hi <strong style="color: #1a1a2e;">{user_name}</strong>,
    </p>

    <p style="margin: 0 0 25px 0; font-size: 16px; line-height: 1.7; color: #4a5568; text-align: center;">
        We regret to inform you that your withdrawal request has been declined.
    </p>
    '''

    content += get_info_box("Withdrawal Details", [
        ("Reference", withdrawal.reference),
        ("Tokens", f"{withdrawal.tokens:,.2f} SRT"),
        ("Amount", f"NGN {withdrawal.amount_ngn:,.2f}"),
        ("Status", '<span style="color: #dc2626; font-weight: 600;">Rejected</span>'),
    ], "#dc2626")

    if withdrawal.admin_notes:
        content += get_warning_box(f"<strong>Reason:</strong> {withdrawal.admin_notes}")

    content += f'''
    <p style="margin: 25px 0; font-size: 16px; line-height: 1.7; color: #4a5568; text-align: center;">
        <strong>Your tokens have been returned</strong> to your account balance. You can submit a new withdrawal request after addressing any issues.
    </p>

    <p style="margin: 0 0 25px 0; font-size: 14px; line-height: 1.6; color: #718096; text-align: center;">
        If you have any questions, please contact our support team.
    </p>
    '''

    html_content = get_base_email_template(
        title="Withdrawal Declined",
        subtitle="Request Not Approved",
        content=content,
        button_text="Submit New Request",
        button_url=f"{SITE_URL}/srt/withdraw/",
        header_color="#dc2626",
        icon=ICONS['warning'],
        footer_text="If you need assistance, please contact support."
    )

    text_content = f"""
Withdrawal Declined - StartUpRipple

Hi {user_name},

We regret to inform you that your withdrawal request has been declined.

Details:
- Reference: {withdrawal.reference}
- Tokens: {withdrawal.tokens:,.2f} SRT
- Amount: NGN {withdrawal.amount_ngn:,.2f}

{'Reason: ' + withdrawal.admin_notes if withdrawal.admin_notes else ''}

Your tokens have been returned to your account balance. You can submit a new withdrawal request after addressing any issues.

If you have any questions, please contact our support team.
    """

    return send_email(subject, html_content, text_content, [user.email])
