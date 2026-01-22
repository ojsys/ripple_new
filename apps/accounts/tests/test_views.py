from django.test import TestCase
from django.urls import reverse

class AccountsViewsTest(TestCase):
    def test_signup_view(self):
        """Test that the signup page is accessible and renders correctly."""
        response = self.client.get(reverse('accounts:signup'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Join StartUpRipple')
        # Test for step 1 content
        self.assertContains(response, 'How will you be using StartUpRipple?')
        self.assertContains(response, 'I&#39;m a Founder seeking funding')
