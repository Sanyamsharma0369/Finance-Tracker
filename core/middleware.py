from django.shortcuts import redirect
from django.contrib import messages
from django.urls import resolve
from django.apps import apps
from .utils import validate_user_data_access
import re
from django.conf import settings

class UserDataProtectionMiddleware:
    """Middleware to prevent data leakage between users by validating URL parameters"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        # Process the request before the view is called
        # Continue with normal flow
        response = self.get_response(request)
        return response
        
    def process_view(self, request, view_func, view_args, view_kwargs):
        # Skip middleware for admin, login, register and similar pages
        safe_paths = [
            '/admin/', 
            '/accounts/login/', 
            '/accounts/register/', 
            '/accounts/password_reset/',
            '/static/', 
            '/media/',
        ]
        
        # Skip for safe paths
        for path in safe_paths:
            if request.path.startswith(path):
                return None
                
        # Skip for unauthenticated users or when there's no pk in kwargs
        if not request.user.is_authenticated or 'pk' not in view_kwargs:
            return None
            
        # Object type checks - map URL patterns to model and user field
        object_types = {
            'transaction': {'model': 'Transaction', 'field': 'user'},
            'budget': {'model': 'Budget', 'field': 'user'},
            'goal': {'model': 'FinancialGoal', 'field': 'user'},
            'category': {'model': 'Category', 'field': 'user'},
        }
        
        # Determine if this view needs protection
        object_type = None
        for key in object_types:
            if key in request.path:
                object_type = key
                break
                
        if not object_type:
            return None
            
        # Use our utility function for validation
        try:
            model_class = apps.get_model('core', object_types[object_type]['model'])
            obj_id = view_kwargs.get('pk')
            user_field = object_types[object_type]['field']
            
            # Try to validate access - this will raise PermissionDenied if not allowed
            try:
                validate_user_data_access(
                    model_class=model_class,
                    object_id=obj_id,
                    user=request.user,
                    field_name=user_field
                )
            except:
                messages.error(request, f"You don't have permission to access this {object_type}.")
                return redirect('dashboard')
                
        except Exception as e:
            # Log the error but don't block the request
            print(f"UserDataProtectionMiddleware error: {e}")
            
        # Allow the request to continue
        return None 

class AdminAccessMiddleware:
    """Middleware to ensure only staff users can access admin URLs."""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.admin_url_pattern = re.compile(r'^/manage/')
        
    def __call__(self, request):
        # Check if the URL starts with /manage/
        if self.admin_url_pattern.match(request.path) and request.path != '/manage/login/':
            # If user is not authenticated or not staff, redirect to admin login
            if not request.user.is_authenticated or not request.user.is_staff:
                messages.error(request, 'You must be logged in as an administrator to access that page.')
                return redirect('admin_login')
                
        # Process the request
        response = self.get_response(request)
        return response

class SecurityHeadersMiddleware:
    """Middleware to handle security headers based on environment (dev vs prod)"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        response = self.get_response(request)
        
        # In development mode, remove security headers that cause issues when not using HTTPS
        if settings.DEBUG:
            # Remove Cross-Origin-Opener-Policy header which causes issues without HTTPS
            if 'Cross-Origin-Opener-Policy' in response:
                del response['Cross-Origin-Opener-Policy']
            
            # Also modify other security headers that might cause issues in development
            if 'Referrer-Policy' in response:
                response['Referrer-Policy'] = 'no-referrer-when-downgrade'
                
            # Remove Content-Security-Policy header for local development
            if 'Content-Security-Policy' in response:
                del response['Content-Security-Policy']
                
            # Allow PDF export and other sensitive operations in development
            # by setting less restrictive security headers
            if '/export-pdf/' in request.path or 'pdf' in request.path:
                # Remove any headers that might block PDF download in development
                if 'X-Content-Type-Options' in response:
                    del response['X-Content-Type-Options']
                # Add header to allow PDF to be served over HTTP in development
                response['Access-Control-Allow-Origin'] = '*'
        
        return response 