from django.shortcuts import redirect

class ProfileCompletionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        if request.user.is_authenticated:
            exempt_paths = [
                '/logout/',
                '/complete-profile/',
                '/static/',
                '/media/',
            ]
            
            if (not request.user.profile_completed and 
                not any(request.path.startswith(path) for path in exempt_paths)):
                return redirect('complete_profile')
        
        return response