from django.test import TestCase
from django.urls import reverse
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()

class AccountsAppTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(email='test@example.com', username='testuser', password='password123', user_type='founder')

    def test_accounts_app_is_installed(self):
        """
        Tests that the 'apps.accounts' app is installed.
        """
        self.assertIn('apps.accounts', settings.INSTALLED_APPS)

    def test_dashboard_url_resolves_for_authenticated_user(self):
        """
        Tests that the 'dashboard' URL resolves and returns a 200 status code for an authenticated user with a completed profile.
        """
        self.user.profile_completed = True
        self.user.save()
        self.client.login(email='test@example.com', password='password123')
        url = reverse('accounts:dashboard')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_redirect_to_complete_profile_if_incomplete(self):
        """
        Tests that an authenticated user with an incomplete profile is redirected to the complete profile page.
        """
        self.user.profile_completed = False
        self.user.save()
        self.client.login(email='test@example.com', password='password123')
        
        # Access dashboard, should redirect
        url = reverse('accounts:dashboard')
        response = self.client.get(url)
        self.assertRedirects(response, reverse('accounts:complete_profile'))

    def test_complete_profile_page_no_redirect_loop(self):
        """
        Tests that accessing the complete profile page does not cause a redirect loop for incomplete profiles.
        """
        self.user.profile_completed = False
        self.user.save()
        self.client.login(email='test@example.com', password='password123')
        
        url = reverse('accounts:complete_profile')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

