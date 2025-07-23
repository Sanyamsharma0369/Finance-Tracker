from django.conf import settings

def demo_mode(request):
    return {'DEMO_MODE': settings.DEMO_MODE}

def currency_info(request):
    currency_symbols = {
        'USD': '$',
        'EUR': '€',
        'GBP': '£',
        'JPY': '¥',
        'INR': '₹'
    }
    
    currency_code = 'INR'
    currency_symbol = '₹'
    
    if request.user.is_authenticated:
        from core.models import Settings
        settings, created = Settings.objects.get_or_create(
            user=request.user,
            defaults={
                'currency': 'INR',
                'theme': 'dark',
            }
        )
        if settings.currency != 'INR':
            settings.currency = 'INR'
            settings.save()
        
        currency_code = settings.currency
        currency_symbol = currency_symbols.get(currency_code, '₹')
    
    return {
        'currency_code': currency_code,
        'currency_symbol': currency_symbol
    }

def user_profile(request):
    context = {}
    
    if request.user.is_authenticated:
        try:
            from core.models import UserProfile
            profile, created = UserProfile.objects.get_or_create(user=request.user)
            context['user_profile'] = profile
            context['has_profile_picture'] = bool(profile.profile_picture)
        except Exception:
            context['has_profile_picture'] = False
    
    return context 