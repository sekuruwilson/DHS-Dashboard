from django.shortcuts import redirect
from django.urls import reverse
from django.conf import settings

class AdminAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/admin-panel/') and not request.path.startswith('/admin-panel/login/'):
            if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
                return redirect(reverse('admin_login'))
        
        response = self.get_response(request)
        return response
