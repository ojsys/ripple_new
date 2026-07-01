"""
Reconcile pending SRT token purchases against Paystack.

Because the agency's Paystack account has a single, shared webhook URL that this
app cannot point to, token purchases can be left as 'pending' when the buyer
never returns to the callback URL (e.g. closes the tab after paying).

This command queries Paystack's transaction/verify endpoint for each unsettled
purchase and:
  - success  → mark successful and credit the partner's tokens (+ emails)
  - failed / abandoned (older than --stale-minutes) → mark failed
  - anything else → leave untouched for the next run

Intended to run on a cron, e.g. every 5 minutes:
    */5 * * * * /path/to/env/bin/python /path/to/manage.py reconcile_token_purchases
"""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.srt.models import TokenPurchase
from apps.srt.paystack_utils import verify_transaction
from apps.srt.email_utils import (
    send_token_purchase_confirmation_to_user,
    send_token_purchase_notification_to_admin,
)


class Command(BaseCommand):
    help = 'Verify pending SRT token purchases against Paystack and credit the successful ones.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would happen without changing anything.',
        )
        parser.add_argument(
            '--lookback-hours',
            type=int,
            default=72,
            help='Only check purchases created within this many hours (default: 72).',
        )
        parser.add_argument(
            '--stale-minutes',
            type=int,
            default=30,
            help='Mark purchases Paystack reports as failed/abandoned as failed only '
                 'once they are older than this many minutes (default: 30).',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        lookback_hours = options['lookback_hours']
        stale_minutes = options['stale_minutes']

        now = timezone.now()
        cutoff = now - timedelta(hours=lookback_hours)
        stale_before = now - timedelta(minutes=stale_minutes)

        purchases = TokenPurchase.objects.filter(
            status__in=['pending', 'processing'],
            created_at__gte=cutoff,
        ).select_related('partner', 'account', 'package').order_by('created_at')

        if not purchases.exists():
            self.stdout.write(self.style.SUCCESS('No pending purchases to reconcile.'))
            return

        self.stdout.write(f'Checking {purchases.count()} pending purchase(s) against Paystack...')

        credited = failed = skipped = errors = 0

        for purchase in purchases:
            ref = purchase.paystack_reference
            paystack_status, error = verify_transaction(ref)
            if error:
                errors += 1
                self.stdout.write(self.style.ERROR(f'  {ref}: verify request failed — {error}'))
                continue

            if paystack_status == 'success':
                if dry_run:
                    self.stdout.write(
                        f'  [DRY RUN] {ref}: would credit {purchase.total_tokens} SRT '
                        f'to {purchase.partner.email}'
                    )
                    credited += 1
                    continue
                try:
                    if purchase.complete_purchase():
                        send_token_purchase_confirmation_to_user(purchase)
                        send_token_purchase_notification_to_admin(purchase)
                        credited += 1
                        self.stdout.write(self.style.SUCCESS(
                            f'  {ref}: credited {purchase.total_tokens} SRT to {purchase.partner.email}'
                        ))
                    else:
                        skipped += 1
                except Exception as exc:
                    errors += 1
                    self.stdout.write(self.style.ERROR(f'  {ref}: credit failed — {exc}'))

            elif paystack_status in ('failed', 'abandoned', 'reversed'):
                # Give the buyer a grace window before writing it off as failed.
                if purchase.created_at > stale_before:
                    skipped += 1
                    self.stdout.write(
                        f'  {ref}: Paystack "{paystack_status}" but still within grace window — leaving pending'
                    )
                    continue
                if dry_run:
                    self.stdout.write(f'  [DRY RUN] {ref}: would mark failed (Paystack "{paystack_status}")')
                    failed += 1
                    continue
                purchase.status = 'failed'
                purchase.save(update_fields=['status'])
                failed += 1
                self.stdout.write(self.style.WARNING(f'  {ref}: marked failed (Paystack "{paystack_status}")'))

            else:
                # ongoing / pending on Paystack's side too — check again next run
                skipped += 1

        summary = (
            f'\nDone. Credited: {credited}, Failed: {failed}, '
            f'Left pending: {skipped}, Errors: {errors}.'
        )
        style = self.style.SUCCESS if not errors else self.style.WARNING
        self.stdout.write(style(summary))
