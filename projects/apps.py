from django.apps import AppConfig
import warnings


class ProjectsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'projects'

    def ready(self):
        import projects.signals
        # Suppress CKEditor security warnings
        warnings.filterwarnings('ignore', message='.*CKEditor.*', category=UserWarning)
