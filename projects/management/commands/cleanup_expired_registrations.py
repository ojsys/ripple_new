from django.core.management.base import BaseCommand
from django.utils import timezone
from projects.models import PendingRegistration


class Command(BaseCommand):
    help = 'Clean up expired pending registrations'

    def handle(self, *args, **options):
        # Find expired registrations
        expired_registrations = PendingRegistration.objects.filter(
            expires_at__lt=timezone.now()
        )
        
        count = expired_registrations.count()
        
        if count > 0:
            expired_registrations.delete()
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully deleted {count} expired pending registrations'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('No expired pending registrations found')
            )