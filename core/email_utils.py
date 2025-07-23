from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .models import EmailConfig

def get_email_settings():
    """
    Get email settings from the active EmailConfig or fall back to Django settings
    """
    try:
        # Try to get active email configuration
        config = EmailConfig.objects.filter(is_active=True).order_by('-updated_at').first()
        
        if config:
            return {
                'backend': config.email_backend,
                'host': config.email_host,
                'port': config.email_port,
                'username': config.email_host_user,
                'password': config.email_host_password,
                'use_tls': config.email_use_tls,
                'use_ssl': config.email_use_ssl,
                'from_email': config.default_from_email or config.email_host_user
            }
    except:
        # If there's any error (like the table doesn't exist yet), pass
        pass
        
    # Fall back to Django settings
    return {
        'backend': settings.EMAIL_BACKEND,
        'host': settings.EMAIL_HOST,
        'port': settings.EMAIL_PORT,
        'username': settings.EMAIL_HOST_USER,
        'password': settings.EMAIL_HOST_PASSWORD,
        'use_tls': settings.EMAIL_USE_TLS,
        'use_ssl': getattr(settings, 'EMAIL_USE_SSL', False),
        'from_email': settings.DEFAULT_FROM_EMAIL or settings.EMAIL_HOST_USER
    }

def test_email_config(recipient_email=None):
    """
    Tests the email configuration by sending a test email.
    
    Args:
        recipient_email: The email address to send the test to.
                         If None, uses the sender email.
    
    Returns:
        bool: True if the email was sent successfully, False otherwise
        str: A message indicating the result
    """
    email_config = get_email_settings()
    
    if recipient_email is None:
        recipient_email = email_config['username']
        
    try:
        # Send a test email
        send_mail(
            subject='Finance Tracker - Email Configuration Test',
            message='This is a test email to verify that your SMTP configuration is working correctly.',
            from_email=email_config['from_email'],
            recipient_list=[recipient_email],
            fail_silently=False,
        )
        return True, f"Test email sent successfully to {recipient_email}"
    except Exception as e:
        return False, f"Failed to send test email: {str(e)}"

def send_verification_email(user, verification_url):
    """
    Sends a verification email to a newly registered user.
    
    Args:
        user: The user object
        verification_url: The URL for email verification
    
    Returns:
        bool: Whether the email was sent successfully
    """
    email_config = get_email_settings()
    subject = 'Verify your Finance Tracker account'
    
    # Create HTML content from template
    html_content = render_to_string('core/email/verification_email.html', {
        'user': user,
        'verification_url': verification_url
    })
    
    # Create plain text content by stripping HTML
    text_content = strip_tags(html_content)
    
    # Create the email
    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=email_config['from_email'],
        to=[user.email]
    )
    
    # Attach HTML content
    email.attach_alternative(html_content, "text/html")
    
    try:
        # Send the email
        email.send(fail_silently=False)
        return True
    except Exception as e:
        print(f"Error sending verification email: {str(e)}")
        return False

def send_password_reset_email(user, reset_url):
    """
    Sends a password reset email.
    
    Args:
        user: The user object
        reset_url: The URL for password reset
    
    Returns:
        bool: Whether the email was sent successfully
    """
    email_config = get_email_settings()
    subject = 'Reset your Finance Tracker password'
    
    # Create HTML content from template
    html_content = render_to_string('core/email/password_reset_email.html', {
        'user': user,
        'reset_url': reset_url
    })
    
    # Create plain text content by stripping HTML
    text_content = strip_tags(html_content)
    
    # Create the email
    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=email_config['from_email'],
        to=[user.email]
    )
    
    # Attach HTML content
    email.attach_alternative(html_content, "text/html")
    
    try:
        # Send the email
        email.send(fail_silently=False)
        return True
    except Exception as e:
        print(f"Error sending password reset email: {str(e)}")
        return False 