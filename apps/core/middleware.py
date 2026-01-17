"""
Core middleware for the Ripple application.
"""
from django.shortcuts import redirect


class ProfileCompletionMiddleware:
    """
    Middleware to ensure users complete their profile before accessing most pages.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            exempt_paths = [
                '/accounts/logout/',
                '/accounts/complete-profile/',
                '/static/',
                '/media/',
                '/admin/',
            ]

            if (not request.user.profile_completed and
                not any(request.path.startswith(path) for path in exempt_paths)):
                return redirect('accounts:complete_profile')

        response = self.get_response(request)
        return response
