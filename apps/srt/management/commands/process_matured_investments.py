from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from apps.srt.models import VentureInvestment, SRTTransaction
import uuid


class Command(BaseCommand):
    help = 'Process matured investments and credit returns to partner accounts'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be processed without making changes'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        today = timezone.now().date()

        # Find all matured investments that are still active
        matured_investments = VentureInvestment.objects.filter(
            status='active',
            maturity_date__lte=today
        ).select_related('partner', 'account', 'venture')

        if not matured_investments.exists():
            self.stdout.write(self.style.SUCCESS('No matured investments to process.'))
            return

        self.stdout.write(f'Found {matured_investments.count()} matured investment(s) to process.')

        processed_count = 0
        error_count = 0

        for investment in matured_investments:
            try:
                if dry_run:
                    self.stdout.write(
                        f'  [DRY RUN] Would process: {investment.reference} - '
                        f'{investment.tokens_invested} SRT invested, '
                        f'{investment.expected_return} SRT expected return'
                    )
                    continue

                with transaction.atomic():
                    # Calculate actual return (using expected return for now)
                    actual_return = investment.expected_return
                    profit = actual_return - investment.tokens_invested

                    # Update investment status
                    investment.status = 'matured'
                    investment.actual_return = actual_return
                    investment.save()

                    # Release locked tokens and add return to account
                    account = investment.account

                    # Release the locked tokens
                    account.locked_tokens -= investment.tokens_invested
                    # Add the full return (principal + profit)
                    account.token_balance += actual_return
                    account.total_tokens_earned += profit
                    account.save()

                    # Create transaction record
                    SRTTransaction.objects.create(
                        account=account,
                        transaction_type='return',
                        amount=actual_return,
                        balance_after=account.token_balance,
                        venture=investment.venture,
                        reference=f"MAT-{uuid.uuid4().hex[:10].upper()}",
                        description=f"Investment matured: {investment.venture.title} "
                                    f"(Principal: {investment.tokens_invested:.2f} SRT, "
                                    f"Profit: {profit:.2f} SRT)"
                    )

                    processed_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  Processed: {investment.reference} - '
                            f'Credited {actual_return:.2f} SRT to {account.partner.email}'
                        )
                    )

            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(
                        f'  Error processing {investment.reference}: {str(e)}'
                    )
                )

        if dry_run:
            self.stdout.write(self.style.WARNING(
                f'\n[DRY RUN] Would have processed {matured_investments.count()} investments.'
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f'\nProcessed {processed_count} investments successfully. '
                f'{error_count} error(s).'
            ))
