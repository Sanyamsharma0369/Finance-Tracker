from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings

def test_email_configuration(recipient_email=None):
    if recipient_email is None:
        recipient_email = settings.EMAIL_HOST_USER
        
    try:
        send_mail(
            subject='Finance Tracker - Email Configuration Test',
            message='This is a test email to verify that your SMTP configuration is working correctly.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient_email],
            fail_silently=False,
        )
        return True, f"Test email sent successfully to {recipient_email}"
    except Exception as e:
        return False, f"Failed to send test email: {str(e)}"

def validate_user_data_access(model_class, object_id, user, field_name='user'):
    if not user.is_authenticated:
        raise PermissionDenied("Authentication required")
        
    filter_kwargs = {'pk': object_id}
    filter_kwargs[field_name] = user
    obj = get_object_or_404(model_class, **filter_kwargs)
    
    return obj
    
def get_user_related_objects(model_class, user, filter_kwargs=None):
    if filter_kwargs is None:
        filter_kwargs = {}
        
    if user.is_authenticated:
        filter_kwargs['user'] = user
        return model_class.objects.filter(**filter_kwargs)
    
    return model_class.objects.none()
    
class UserDataAccessMixin:
    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(user=self.request.user)
        
async def async_validate_user_data_access(model_class, object_id, user, field_name='user'):
    from asgiref.sync import sync_to_async
    
    if not user.is_authenticated:
        raise PermissionDenied("Authentication required")
    
    async_get_object_or_404 = sync_to_async(get_object_or_404)
    
    filter_kwargs = {'pk': object_id}
    filter_kwargs[field_name] = user
    
    obj = await async_get_object_or_404(model_class, **filter_kwargs)
    
    return obj
