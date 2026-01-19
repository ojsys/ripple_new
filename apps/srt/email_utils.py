"""
Email notification utilities for SRT (StartUpRipple Tokens) system.
Handles sending email notifications for token purchases, withdrawals, and other SRT events.
"""
from django.core.mail import EmailMessage
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

# Admin email for notifications
ADMIN_EMAIL = getattr(settings, 'ADMIN_EMAIL', 'admin@startupripple.com')
ADMIN_EMAILS = getattr(settings, 'ADMIN_EMAILS', [ADMIN_EMAIL])


def get_base_email_styles():
    """Return base CSS styles for email templates"""
    return """
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; }
        .email-container { max-width: 600px; margin: 0 auto; background: #ffffff; }
        .email-header { background: linear-gradient(135deg, #0d9488 0%, #0f766e 100%); padding: 30px; text-align: center; }
        .email-header h1 { color: #ffffff; margin: 0; font-size: 24px; }
        .email-header .subtitle { color: rgba(255,255,255,0.9); font-size: 14px; margin-top: 5px; }
        .email-body { padding: 30px; }
        .greeting { font-size: 18px; color: #1e293b; margin-bottom: 20px; }
        .info-box { background: #f0fdfa; border-left: 4px solid #0d9488; padding: 20px; margin: 20px 0; border-radius: 0 8px 8px 0; }
        .info-box h3 { margin: 0 0 15px 0; color: #0f766e; font-size: 16px; }
        .info-row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #e2e8f0; }
        .info-row:last-child { border-bottom: none; }
        .info-label { color: #64748b; }
        .info-value { color: #1e293b; font-weight: 600; }
        .highlight-box { background: linear-gradient(135deg, #0d9488 0%, #0f766e 100%); color: white; padding: 20px; border-radius: 12px; text-align: center; margin: 20px 0; }
        .highlight-box .amount { font-size: 32px; font-weight: 700; }
        .highlight-box .label { font-size: 14px; opacity: 0.9; }
        .btn { display: inline-block; background: #0d9488; color: #ffffff; padding: 14px 28px; text-decoration: none; border-radius: 8px; font-weight: 600; margin: 20px 0; }
        .btn:hover { background: #0f766e; }
        .status-badge { display: inline-block; padding: 6px 14px; border-radius: 20px; font-size: 13px; font-weight: 600; }
        .status-pending { background: #fef3c7; color: #92400e; }
        .status-approved { background: #d1fae5; color: #065f46; }
        .status-completed { background: #d1fae5; color: #065f46; }
        .status-rejected { background: #fee2e2; color: #991b1b; }
        .email-footer { background: #f8fafc; padding: 20px 30px; text-align: center; border-top: 1px solid #e2e8f0; }
        .email-footer p { color: #64748b; font-size: 13px; margin: 5px 0; }
        .warning-box { background: #fef3c7; border-left: 4px solid #f59e0b; padding: 15px 20px; margin: 20px 0; border-radius: 0 8px 8px 0; }
        .warning-box p { color: #92400e; margin: 0; }
        .success-box { background: #d1fae5; border-left: 4px solid #059669; padding: 15px 20px; margin: 20px 0; border-radius: 0 8px 8px 0; }
        .success-box p { color: #065f46; margin: 0; }
    """


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
        email = EmailMessage(
            subject=subject,
            body=html_content,
            from_email=from_email,
            to=to_emails if isinstance(to_emails, list) else [to_emails],
        )
        email.content_subtype = 'html'
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
    styles = get_base_email_styles()

    subject = f"Token Purchase Confirmed - {purchase.tokens_purchased} SRT"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head><style>{styles}</style></head>
    <body>
        <div class="email-container">
            <div class="email-header">
                <h1>Token Purchase Confirmed</h1>
                <div class="subtitle">StartUpRipple Tokens (SRT)</div>
            </div>

            <div class="email-body">
                <p class="greeting">Hi {user.first_name or user.email},</p>

                <p>Great news! Your token purchase has been successfully processed. Here are the details:</p>

                <div class="highlight-box">
                    <div class="label">Tokens Purchased</div>
                    <div class="amount">{purchase.tokens_purchased:,.2f} SRT</div>
                </div>

                <div class="info-box">
                    <h3>Purchase Details</h3>
                    <table width="100%" cellpadding="0" cellspacing="0">
                        <tr class="info-row">
                            <td class="info-label">Reference</td>
                            <td class="info-value" style="text-align: right;">{purchase.reference}</td>
                        </tr>
                        <tr class="info-row">
                            <td class="info-label">Amount Paid</td>
                            <td class="info-value" style="text-align: right;">NGN {purchase.amount_paid:,.2f}</td>
                        </tr>
                        <tr class="info-row">
                            <td class="info-label">Tokens Received</td>
                            <td class="info-value" style="text-align: right;">{purchase.tokens_purchased:,.2f} SRT</td>
                        </tr>
                        <tr class="info-row">
                            <td class="info-label">Bonus Tokens</td>
                            <td class="info-value" style="text-align: right;">{purchase.bonus_tokens:,.2f} SRT</td>
                        </tr>
                        <tr class="info-row">
                            <td class="info-label">Date</td>
                            <td class="info-value" style="text-align: right;">{purchase.created_at.strftime('%B %d, %Y at %H:%M')}</td>
                        </tr>
                        <tr class="info-row">
                            <td class="info-label">New Balance</td>
                            <td class="info-value" style="text-align: right;">{purchase.account.token_balance:,.2f} SRT</td>
                        </tr>
                    </table>
                </div>

                <div class="success-box">
                    <p><strong>Your tokens are ready!</strong> You can now invest in ventures or withdraw at any time.</p>
                </div>

                <center>
                    <a href="{getattr(settings, 'SITE_URL', 'https://startupripple.com')}/srt/dashboard/" class="btn">
                        View Dashboard
                    </a>
                </center>

                <p>Thank you for investing with StartUpRipple!</p>
            </div>

            <div class="email-footer">
                <p><strong>StartUpRipple</strong></p>
                <p>Empowering African Entrepreneurs</p>
                <p style="font-size: 11px; color: #94a3b8;">This is an automated message. Please do not reply directly to this email.</p>
            </div>
        </div>
    </body>
    </html>
    """

    text_content = f"""
    Token Purchase Confirmed - StartUpRipple

    Hi {user.first_name or user.email},

    Your token purchase has been successfully processed!

    Purchase Details:
    - Reference: {purchase.reference}
    - Amount Paid: NGN {purchase.amount_paid:,.2f}
    - Tokens Received: {purchase.tokens_purchased:,.2f} SRT
    - Bonus Tokens: {purchase.bonus_tokens:,.2f} SRT
    - Date: {purchase.created_at.strftime('%B %d, %Y at %H:%M')}
    - New Balance: {purchase.account.token_balance:,.2f} SRT

    Your tokens are ready! You can now invest in ventures or withdraw at any time.

    View your dashboard: {getattr(settings, 'SITE_URL', 'https://startupripple.com')}/srt/dashboard/

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
    styles = get_base_email_styles()

    subject = f"[ADMIN] New Token Purchase - {purchase.tokens_purchased} SRT by {user.email}"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head><style>{styles}</style></head>
    <body>
        <div class="email-container">
            <div class="email-header" style="background: linear-gradient(135deg, #1e40af 0%, #1e3a8a 100%);">
                <h1>New Token Purchase</h1>
                <div class="subtitle">Admin Notification</div>
            </div>

            <div class="email-body">
                <p class="greeting">Admin Alert</p>

                <p>A new token purchase has been completed on the platform:</p>

                <div class="highlight-box" style="background: linear-gradient(135deg, #1e40af 0%, #1e3a8a 100%);">
                    <div class="label">Amount Received</div>
                    <div class="amount">NGN {purchase.amount_paid:,.2f}</div>
                </div>

                <div class="info-box" style="border-left-color: #1e40af; background: #eff6ff;">
                    <h3 style="color: #1e40af;">Purchase Details</h3>
                    <table width="100%" cellpadding="0" cellspacing="0">
                        <tr class="info-row">
                            <td class="info-label">Reference</td>
                            <td class="info-value" style="text-align: right;">{purchase.reference}</td>
                        </tr>
                        <tr class="info-row">
                            <td class="info-label">Partner</td>
                            <td class="info-value" style="text-align: right;">{user.get_full_name() or user.email}</td>
                        </tr>
                        <tr class="info-row">
                            <td class="info-label">Email</td>
                            <td class="info-value" style="text-align: right;">{user.email}</td>
                        </tr>
                        <tr class="info-row">
                            <td class="info-label">Amount Paid</td>
                            <td class="info-value" style="text-align: right;">NGN {purchase.amount_paid:,.2f}</td>
                        </tr>
                        <tr class="info-row">
                            <td class="info-label">Tokens Purchased</td>
                            <td class="info-value" style="text-align: right;">{purchase.tokens_purchased:,.2f} SRT</td>
                        </tr>
                        <tr class="info-row">
                            <td class="info-label">Bonus Tokens</td>
                            <td class="info-value" style="text-align: right;">{purchase.bonus_tokens:,.2f} SRT</td>
                        </tr>
                        <tr class="info-row">
                            <td class="info-label">Payment Method</td>
                            <td class="info-value" style="text-align: right;">{purchase.payment_method or 'Paystack'}</td>
                        </tr>
                        <tr class="info-row">
                            <td class="info-label">Payment Reference</td>
                            <td class="info-value" style="text-align: right;">{purchase.payment_reference or 'N/A'}</td>
                        </tr>
                        <tr class="info-row">
                            <td class="info-label">Date</td>
                            <td class="info-value" style="text-align: right;">{purchase.created_at.strftime('%B %d, %Y at %H:%M')}</td>
                        </tr>
                        <tr class="info-row">
                            <td class="info-label">Partner Balance</td>
                            <td class="info-value" style="text-align: right;">{purchase.account.token_balance:,.2f} SRT</td>
                        </tr>
                    </table>
                </div>

                <center>
                    <a href="{getattr(settings, 'SITE_URL', 'https://startupripple.com')}/admin/srt/tokenpurchase/" class="btn" style="background: #1e40af;">
                        View in Admin
                    </a>
                </center>
            </div>

            <div class="email-footer">
                <p><strong>StartUpRipple Admin</strong></p>
                <p style="font-size: 11px; color: #94a3b8;">This is an automated admin notification.</p>
            </div>
        </div>
    </body>
    </html>
    """

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

    View in admin: {getattr(settings, 'SITE_URL', 'https://startupripple.com')}/admin/srt/tokenpurchase/
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
    styles = get_base_email_styles()

    subject = f"Withdrawal Request Received - {withdrawal.tokens} SRT"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head><style>{styles}</style></head>
    <body>
        <div class="email-container">
            <div class="email-header">
                <h1>Withdrawal Request Received</h1>
                <div class="subtitle">StartUpRipple Tokens (SRT)</div>
            </div>

            <div class="email-body">
                <p class="greeting">Hi {user.first_name or user.email},</p>

                <p>Your withdrawal request has been received and is being processed. Here are the details:</p>

                <div class="highlight-box">
                    <div class="label">Amount to Receive</div>
                    <div class="amount">NGN {withdrawal.amount_ngn:,.2f}</div>
                </div>

                <div class="info-box">
                    <h3>Withdrawal Details</h3>
                    <table width="100%" cellpadding="0" cellspacing="0">
                        <tr class="info-row">
                            <td class="info-label">Reference</td>
                            <td class="info-value" style="text-align: right;">{withdrawal.reference}</td>
                        </tr>
                        <tr class="info-row">
                            <td class="info-label">Tokens</td>
                            <td class="info-value" style="text-align: right;">{withdrawal.tokens:,.2f} SRT</td>
                        </tr>
                        <tr class="info-row">
                            <td class="info-label">Processing Fee</td>
                            <td class="info-value" style="text-align: right;">NGN {withdrawal.fee:,.2f}</td>
                        </tr>
                        <tr class="info-row">
                            <td class="info-label">Amount to Receive</td>
                            <td class="info-value" style="text-align: right;">NGN {withdrawal.amount_ngn:,.2f}</td>
                        </tr>
                        <tr class="info-row">
                            <td class="info-label">Status</td>
                            <td class="info-value" style="text-align: right;"><span class="status-badge status-pending">Pending</span></td>
                        </tr>
                    </table>
                </div>

                <div class="info-box">
                    <h3>Bank Details</h3>
                    <table width="100%" cellpadding="0" cellspacing="0">
                        <tr class="info-row">
                            <td class="info-label">Bank</td>
                            <td class="info-value" style="text-align: right;">{withdrawal.get_bank_name_display()}</td>
                        </tr>
                        <tr class="info-row">
                            <td class="info-label">Account Number</td>
                            <td class="info-value" style="text-align: right;">{withdrawal.account_number}</td>
                        </tr>
                        <tr class="info-row">
                            <td class="info-label">Account Name</td>
                            <td class="info-value" style="text-align: right;">{withdrawal.account_name}</td>
                        </tr>
                    </table>
                </div>

                <div class="warning-box">
                    <p><strong>What happens next?</strong> Our team will review and process your withdrawal request. You'll receive an email once the payment is completed.</p>
                </div>

                <center>
                    <a href="{getattr(settings, 'SITE_URL', 'https://startupripple.com')}/srt/withdrawal/{withdrawal.reference}/" class="btn">
                        Track Withdrawal
                    </a>
                </center>
            </div>

            <div class="email-footer">
                <p><strong>StartUpRipple</strong></p>
                <p>Empowering African Entrepreneurs</p>
                <p style="font-size: 11px; color: #94a3b8;">This is an automated message. Please do not reply directly to this email.</p>
            </div>
        </div>
    </body>
    </html>
    """

    text_content = f"""
    Withdrawal Request Received - StartUpRipple

    Hi {user.first_name or user.email},

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

    Track your withdrawal: {getattr(settings, 'SITE_URL', 'https://startupripple.com')}/srt/withdrawal/{withdrawal.reference}/
    """

    return send_email(subject, html_content, text_content, [user.email])


def send_withdrawal_request_to_admin(withdrawal):
    """
    Send new withdrawal request notification to admin.

    Args:
        withdrawal: TokenWithdrawal instance
    """
    user = withdrawal.partner
    styles = get_base_email_styles()

    subject = f"[ADMIN] New Withdrawal Request - NGN {withdrawal.amount_ngn:,.2f} by {user.email}"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head><style>{styles}</style></head>
    <body>
        <div class="email-container">
            <div class="email-header" style="background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);">
                <h1>New Withdrawal Request</h1>
                <div class="subtitle">Action Required</div>
            </div>

            <div class="email-body">
                <p class="greeting">Admin Alert</p>

                <p>A new withdrawal request requires your attention:</p>

                <div class="highlight-box" style="background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);">
                    <div class="label">Amount to Pay</div>
                    <div class="amount">NGN {withdrawal.amount_ngn:,.2f}</div>
                </div>

                <div class="info-box" style="border-left-color: #dc2626; background: #fef2f2;">
                    <h3 style="color: #dc2626;">Withdrawal Details</h3>
                    <table width="100%" cellpadding="0" cellspacing="0">
                        <tr class="info-row">
                            <td class="info-label">Reference</td>
                            <td class="info-value" style="text-align: right;">{withdrawal.reference}</td>
                        </tr>
                        <tr class="info-row">
                            <td class="info-label">Partner</td>
                            <td class="info-value" style="text-align: right;">{user.get_full_name() or user.email}</td>
                        </tr>
                        <tr class="info-row">
                            <td class="info-label">Email</td>
                            <td class="info-value" style="text-align: right;">{user.email}</td>
                        </tr>
                        <tr class="info-row">
                            <td class="info-label">Tokens</td>
                            <td class="info-value" style="text-align: right;">{withdrawal.tokens:,.2f} SRT</td>
                        </tr>
                        <tr class="info-row">
                            <td class="info-label">Fee Deducted</td>
                            <td class="info-value" style="text-align: right;">NGN {withdrawal.fee:,.2f}</td>
                        </tr>
                        <tr class="info-row">
                            <td class="info-label">Amount to Pay</td>
                            <td class="info-value" style="text-align: right;">NGN {withdrawal.amount_ngn:,.2f}</td>
                        </tr>
                        <tr class="info-row">
                            <td class="info-label">Date Requested</td>
                            <td class="info-value" style="text-align: right;">{withdrawal.created_at.strftime('%B %d, %Y at %H:%M')}</td>
                        </tr>
                    </table>
                </div>

                <div class="info-box" style="border-left-color: #dc2626; background: #fef2f2;">
                    <h3 style="color: #dc2626;">Bank Details for Payment</h3>
                    <table width="100%" cellpadding="0" cellspacing="0">
                        <tr class="info-row">
                            <td class="info-label">Bank</td>
                            <td class="info-value" style="text-align: right;">{withdrawal.get_bank_name_display()}</td>
                        </tr>
                        <tr class="info-row">
                            <td class="info-label">Account Number</td>
                            <td class="info-value" style="text-align: right;"><strong>{withdrawal.account_number}</strong></td>
                        </tr>
                        <tr class="info-row">
                            <td class="info-label">Account Name</td>
                            <td class="info-value" style="text-align: right;"><strong>{withdrawal.account_name}</strong></td>
                        </tr>
                    </table>
                </div>

                <div class="warning-box">
                    <p><strong>Action Required:</strong> Please review and process this withdrawal request in the admin panel.</p>
                </div>

                <center>
                    <a href="{getattr(settings, 'SITE_URL', 'https://startupripple.com')}/admin/srt/tokenwithdrawal/{withdrawal.id}/change/" class="btn" style="background: #dc2626;">
                        Process Withdrawal
                    </a>
                </center>
            </div>

            <div class="email-footer">
                <p><strong>StartUpRipple Admin</strong></p>
                <p style="font-size: 11px; color: #94a3b8;">This is an automated admin notification.</p>
            </div>
        </div>
    </body>
    </html>
    """

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

    Process in admin: {getattr(settings, 'SITE_URL', 'https://startupripple.com')}/admin/srt/tokenwithdrawal/{withdrawal.id}/change/
    """

    return send_email(subject, html_content, text_content, ADMIN_EMAILS)


def send_withdrawal_approved_to_user(withdrawal):
    """
    Send withdrawal approved notification to user.

    Args:
        withdrawal: TokenWithdrawal instance
    """
    user = withdrawal.partner
    styles = get_base_email_styles()

    subject = f"Withdrawal Approved - {withdrawal.reference}"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head><style>{styles}</style></head>
    <body>
        <div class="email-container">
            <div class="email-header">
                <h1>Withdrawal Approved</h1>
                <div class="subtitle">StartUpRipple Tokens (SRT)</div>
            </div>

            <div class="email-body">
                <p class="greeting">Hi {user.first_name or user.email},</p>

                <p>Great news! Your withdrawal request has been approved and is being processed for payment.</p>

                <div class="highlight-box">
                    <div class="label">Amount to Receive</div>
                    <div class="amount">NGN {withdrawal.amount_ngn:,.2f}</div>
                </div>

                <div class="info-box">
                    <h3>Withdrawal Details</h3>
                    <table width="100%" cellpadding="0" cellspacing="0">
                        <tr class="info-row">
                            <td class="info-label">Reference</td>
                            <td class="info-value" style="text-align: right;">{withdrawal.reference}</td>
                        </tr>
                        <tr class="info-row">
                            <td class="info-label">Status</td>
                            <td class="info-value" style="text-align: right;"><span class="status-badge status-approved">Approved</span></td>
                        </tr>
                        <tr class="info-row">
                            <td class="info-label">Bank</td>
                            <td class="info-value" style="text-align: right;">{withdrawal.get_bank_name_display()}</td>
                        </tr>
                        <tr class="info-row">
                            <td class="info-label">Account</td>
                            <td class="info-value" style="text-align: right;">{withdrawal.account_number}</td>
                        </tr>
                    </table>
                </div>

                <div class="success-box">
                    <p><strong>Payment is on the way!</strong> You'll receive another email once the payment has been completed.</p>
                </div>

                <center>
                    <a href="{getattr(settings, 'SITE_URL', 'https://startupripple.com')}/srt/withdrawal/{withdrawal.reference}/" class="btn">
                        Track Withdrawal
                    </a>
                </center>
            </div>

            <div class="email-footer">
                <p><strong>StartUpRipple</strong></p>
                <p>Empowering African Entrepreneurs</p>
            </div>
        </div>
    </body>
    </html>
    """

    text_content = f"""
    Withdrawal Approved - StartUpRipple

    Hi {user.first_name or user.email},

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
    styles = get_base_email_styles()

    subject = f"Withdrawal Completed - NGN {withdrawal.amount_ngn:,.2f} Sent!"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head><style>{styles}</style></head>
    <body>
        <div class="email-container">
            <div class="email-header" style="background: linear-gradient(135deg, #059669 0%, #047857 100%);">
                <h1>Withdrawal Completed!</h1>
                <div class="subtitle">Payment Successful</div>
            </div>

            <div class="email-body">
                <p class="greeting">Hi {user.first_name or user.email},</p>

                <p>Your withdrawal has been completed! The funds have been sent to your bank account.</p>

                <div class="highlight-box" style="background: linear-gradient(135deg, #059669 0%, #047857 100%);">
                    <div class="label">Amount Sent</div>
                    <div class="amount">NGN {withdrawal.amount_ngn:,.2f}</div>
                </div>

                <div class="info-box">
                    <h3>Payment Details</h3>
                    <table width="100%" cellpadding="0" cellspacing="0">
                        <tr class="info-row">
                            <td class="info-label">Reference</td>
                            <td class="info-value" style="text-align: right;">{withdrawal.reference}</td>
                        </tr>
                        <tr class="info-row">
                            <td class="info-label">Status</td>
                            <td class="info-value" style="text-align: right;"><span class="status-badge status-completed">Completed</span></td>
                        </tr>
                        <tr class="info-row">
                            <td class="info-label">Tokens Withdrawn</td>
                            <td class="info-value" style="text-align: right;">{withdrawal.tokens:,.2f} SRT</td>
                        </tr>
                        <tr class="info-row">
                            <td class="info-label">Amount Sent</td>
                            <td class="info-value" style="text-align: right;">NGN {withdrawal.amount_ngn:,.2f}</td>
                        </tr>
                        <tr class="info-row">
                            <td class="info-label">Bank</td>
                            <td class="info-value" style="text-align: right;">{withdrawal.get_bank_name_display()}</td>
                        </tr>
                        <tr class="info-row">
                            <td class="info-label">Account</td>
                            <td class="info-value" style="text-align: right;">{withdrawal.account_number}</td>
                        </tr>
                        <tr class="info-row">
                            <td class="info-label">Completed On</td>
                            <td class="info-value" style="text-align: right;">{withdrawal.completed_at.strftime('%B %d, %Y at %H:%M') if withdrawal.completed_at else 'N/A'}</td>
                        </tr>
                        {f'<tr class="info-row"><td class="info-label">Payment Reference</td><td class="info-value" style="text-align: right;">{withdrawal.payment_reference}</td></tr>' if withdrawal.payment_reference else ''}
                    </table>
                </div>

                <div class="success-box">
                    <p><strong>Funds sent successfully!</strong> Please allow 1-24 hours for the funds to reflect in your bank account depending on your bank.</p>
                </div>

                <center>
                    <a href="{getattr(settings, 'SITE_URL', 'https://startupripple.com')}/srt/dashboard/" class="btn" style="background: #059669;">
                        Go to Dashboard
                    </a>
                </center>

                <p>Thank you for being a StartUpRipple partner!</p>
            </div>

            <div class="email-footer">
                <p><strong>StartUpRipple</strong></p>
                <p>Empowering African Entrepreneurs</p>
            </div>
        </div>
    </body>
    </html>
    """

    text_content = f"""
    Withdrawal Completed - StartUpRipple

    Hi {user.first_name or user.email},

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
    styles = get_base_email_styles()

    subject = f"Withdrawal Request Declined - {withdrawal.reference}"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head><style>{styles}</style></head>
    <body>
        <div class="email-container">
            <div class="email-header" style="background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);">
                <h1>Withdrawal Declined</h1>
                <div class="subtitle">Request Not Approved</div>
            </div>

            <div class="email-body">
                <p class="greeting">Hi {user.first_name or user.email},</p>

                <p>We regret to inform you that your withdrawal request has been declined.</p>

                <div class="info-box" style="border-left-color: #dc2626; background: #fef2f2;">
                    <h3 style="color: #dc2626;">Withdrawal Details</h3>
                    <table width="100%" cellpadding="0" cellspacing="0">
                        <tr class="info-row">
                            <td class="info-label">Reference</td>
                            <td class="info-value" style="text-align: right;">{withdrawal.reference}</td>
                        </tr>
                        <tr class="info-row">
                            <td class="info-label">Tokens</td>
                            <td class="info-value" style="text-align: right;">{withdrawal.tokens:,.2f} SRT</td>
                        </tr>
                        <tr class="info-row">
                            <td class="info-label">Amount</td>
                            <td class="info-value" style="text-align: right;">NGN {withdrawal.amount_ngn:,.2f}</td>
                        </tr>
                        <tr class="info-row">
                            <td class="info-label">Status</td>
                            <td class="info-value" style="text-align: right;"><span class="status-badge status-rejected">Rejected</span></td>
                        </tr>
                    </table>
                </div>

                {f'<div class="warning-box"><p><strong>Reason:</strong> {withdrawal.admin_notes}</p></div>' if withdrawal.admin_notes else ''}

                <p><strong>Your tokens have been returned</strong> to your account balance. You can submit a new withdrawal request after addressing any issues.</p>

                <p>If you have any questions, please contact our support team.</p>

                <center>
                    <a href="{getattr(settings, 'SITE_URL', 'https://startupripple.com')}/srt/withdraw/" class="btn" style="background: #dc2626;">
                        Submit New Request
                    </a>
                </center>
            </div>

            <div class="email-footer">
                <p><strong>StartUpRipple</strong></p>
                <p>Empowering African Entrepreneurs</p>
            </div>
        </div>
    </body>
    </html>
    """

    text_content = f"""
    Withdrawal Declined - StartUpRipple

    Hi {user.first_name or user.email},

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
