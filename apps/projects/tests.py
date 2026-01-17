from django.test import TestCase
from django.apps import apps
from django.conf import settings
from django.urls import reverse

class ProjectsAppTests(TestCase):

    def test_projects_app_is_installed(self):
        """
        Tests that the 'apps.projects' app is installed.
        """
        self.assertIn('apps.projects', settings.INSTALLED_APPS)
        
    def test_project_model_exists(self):
        """
        Tests that the 'Project' model exists in the 'projects' app.
        """
        try:
            apps.get_model('projects', 'Project')
        except LookupError:
            self.fail("Model 'Project' not found in app 'projects'")

    def test_project_list_url_resolves(self):
        """
        Tests that the 'project_list' URL resolves and returns a 200 status code.
        """
        url = reverse('projects:project_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

