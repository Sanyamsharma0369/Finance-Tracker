from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User, AnonymousUser

class AnonymousUserBackend(ModelBackend):
    """
    Custom authentication backend that allows anonymous users to access views
    that would normally require authentication.
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        # Use the default ModelBackend authentication
        return super().authenticate(request, username, password, **kwargs)
    
    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
    
    def has_perm(self, user_obj, perm, obj=None):
        # If the user is authenticated, use the default permission check
        if user_obj.is_authenticated:
            return super().has_perm(user_obj, perm, obj)
        # For anonymous users, grant read-only access
        if perm.startswith('view_'):
            return True
        return False

    def has_module_perms(self, user_obj, app_label):
        # Allow module permissions for demonstration purposes
        return True
        
    def with_perm(self, perm, is_active=True, include_superusers=True, obj=None):
        # This method is required for Django 3.2+
        # Returns all users with the given permission
        return [] 