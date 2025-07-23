from django.contrib import admin
from .models import (
    Transaction, Category, Budget, FinancialGoal, 
    Settings, UserProfile, Notification, CommercialRegistration,
    EmailVerification, EmailConfig
)

# Register your models here.

@admin.register(EmailConfig)
class EmailConfigAdmin(admin.ModelAdmin):
    list_display = ('email_host', 'email_host_user', 'is_active', 'updated_at')
    list_filter = ('is_active', 'email_use_tls', 'email_use_ssl')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Backend Settings', {
            'fields': ('email_backend', 'is_active')
        }),
        ('SMTP Server Settings', {
            'fields': ('email_host', 'email_port', 'email_use_tls', 'email_use_ssl')
        }),
        ('Authentication', {
            'fields': ('email_host_user', 'email_host_password', 'default_from_email')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
