"""
Management command to reconcile Project.total_investment_raised with
the actual sum of approved Investment records.

Run on production if investments exist but the project-level totals are stale:
    python manage.py reconcile_investment_totals
"""
from django.core.management.base import BaseCommand
from django.db.models import Sum
from apps.projects.models import Project
from apps.funding.models import Investment

COUNTING_STATUSES = ('pending_approval', 'active', 'approved', 'completed')


class Command(BaseCommand):
    help = 'Reconcile Project.total_investment_raised with actual Investment sums'

    def handle(self, *args, **options):
        ventures = Project.objects.filter(listing_type='venture')
        fixed = 0

        for project in ventures:
            actual = Investment.objects.filter(
                project=project,
                status__in=COUNTING_STATUSES,
            ).aggregate(total=Sum('amount'))['total'] or 0

            if project.total_investment_raised != actual:
                self.stdout.write(
                    f'  {project.title[:40]}: stored={project.total_investment_raised} → correcting to {actual}'
                )
                Project.objects.filter(pk=project.pk).update(total_investment_raised=actual)
                fixed += 1

        self.stdout.write(self.style.SUCCESS(f'Done. {fixed} project(s) corrected.'))
