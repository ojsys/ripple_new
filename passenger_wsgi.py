import os
import sys

# Add your project directory to the sys.path
path = '/home/username/ripple'
if path not in sys.path:
    sys.path.insert(0, path)

# Set environment variable to use production settings
os.environ['DJANGO_SETTINGS_MODULE'] = 'ripple.settings'

# Create application object
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()