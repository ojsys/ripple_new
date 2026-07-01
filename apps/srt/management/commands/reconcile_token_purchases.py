"""
Reconcile pending SRT token purchase *intents* against Paystack.

Because the agency's Paystack account has a single, shared webhook URL that this
app cannot point to, a payment can be left unconfirmed when the buyer never
returns to the callback URL (e.g. closes the tab after paying).

Pending attempts live as TokenPurchaseIntent rows (they are NOT shown in the
admin). This command verifies each intent with Paystack and:
  - success  → record the real TokenPurchase, credit the partner (+ emails),
               and remove the intent
  - failed / abandoned (older than --stale-minutes) → delete the intent
  - anything else → leave untouched for the next run

Only successful purchases ever land in the TokenPurchase table.

Intended to run on a cron, e.g. every 5 minutes:
    */5 * * * * /path/to/env/bin/python /path/to/manage.py reconcile_token_purchases
"""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.srt.models import TokenPurchaseIntent
from apps.srt.paystack_utils import verify_transaction
from apps.srt.views import finalize_successful_purchase


class Command(BaseCommand):
    help = 'Verify pending SRT purchase intents against Paystack and credit the successful ones.'

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
            help='Only check intents created within this many hours (default: 72).',
        )
        parser.add_argument(
            '--stale-minutes',
            type=int,
            default=30,
            help='Delete intents Paystack reports as failed/abandoned only once they '
                 'are older than this many minutes (default: 30).',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        lookback_hours = options['lookback_hours']
        stale_minutes = options['stale_minutes']

        now = timezone.now()
        cutoff = now - timedelta(hours=lookback_hours)
        stale_before = now - timedelta(minutes=stale_minutes)

        intents = TokenPurchaseIntent.objects.filter(
            created_at__gte=cutoff,
        ).select_related('partner', 'account', 'package').order_by('created_at')

        if not intents.exists():
            self.stdout.write(self.style.SUCCESS('No pending intents to reconcile.'))
            return

        self.stdout.write(f'Checking {intents.count()} pending intent(s) against Paystack...')

        credited = deleted = skipped = errors = 0

        for intent in intents:
            ref = intent.paystack_reference
            paystack_status, error = verify_transaction(ref)
            if error:
                errors += 1
                self.stdout.write(self.style.ERROR(f'  {ref}: verify request failed — {error}'))
                continue

            if paystack_status == 'success':
                if dry_run:
                    self.stdout.write(
                        f'  [DRY RUN] {ref}: would credit {intent.total_tokens} SRT '
                        f'to {intent.partner.email}'
                    )
                    credited += 1
                    continue
                try:
                    _, was_credited = finalize_successful_purchase(ref)
                    if was_credited:
                        credited += 1
                        self.stdout.write(self.style.SUCCESS(
                            f'  {ref}: credited {intent.total_tokens} SRT to {intent.partner.email}'
                        ))
                    else:
                        skipped += 1
                except Exception as exc:
                    errors += 1
                    self.stdout.write(self.style.ERROR(f'  {ref}: credit failed — {exc}'))

            elif paystack_status in ('failed', 'abandoned', 'reversed', 'not_found'):
                # Give the buyer a grace window before writing it off.
                if intent.created_at > stale_before:
                    skipped += 1
                    self.stdout.write(
                        f'  {ref}: Paystack "{paystack_status}" but still within grace window — leaving pending'
                    )
                    continue
                if dry_run:
                    self.stdout.write(f'  [DRY RUN] {ref}: would delete (Paystack "{paystack_status}")')
                    deleted += 1
                    continue
                intent.delete()
                deleted += 1
                self.stdout.write(self.style.WARNING(f'  {ref}: deleted (Paystack "{paystack_status}")'))

            else:
                # ongoing / pending on Paystack's side too — check again next run
                skipped += 1

        summary = (
            f'\nDone. Credited: {credited}, Deleted: {deleted}, '
            f'Left pending: {skipped}, Errors: {errors}.'
        )
        style = self.style.SUCCESS if not errors else self.style.WARNING
        self.stdout.write(style(summary))
