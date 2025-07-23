"""
URL configuration for finance_tracker project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from core.views import (
    dashboard, register_view, verify_otp, resend_otp,
    admin_dashboard, admin_user_list, admin_user_create,
    admin_user_edit, admin_user_delete, commercial_register,
    verify_commercial_otp, admin_transactions, admin_transaction_edit,
    admin_transaction_delete, admin_budgets, admin_budget_edit, 
    admin_budget_delete, admin_goals, admin_goal_edit,
    admin_goal_delete, admin_categories, admin_category_edit,
    admin_category_delete, admin_reports, admin_login, admin_analyze_transactions,
    custom_logout
)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Include all core app URLs
    path('', include('core.urls')),
    
    # Include class-based view URLs
    path('', include('core.urls_class_based')),
    
    # Authentication URLs
    path('accounts/login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(template_name='registration/logout.html'), name='logout'),
    path('accounts/custom-logout/', custom_logout, name='custom_logout'),
    path('accounts/register/', register_view, name='register'),
    path('accounts/verify-otp/', verify_otp, name='verify_otp'),
    path('accounts/resend-otp/', resend_otp, name='resend_otp'),
    
    # Commercial Registration URLs
    path('accounts/commercial-register/', commercial_register, name='commercial_register'),
    path('accounts/verify-commercial-otp/', verify_commercial_otp, name='verify_commercial_otp'),
    
    # Admin Authentication
    path('manage/login/', admin_login, name='admin_login'),
    
    # Admin Management URLs
    path('manage/', admin_dashboard, name='admin_dashboard'),
    
    # Admin User Management
    path('manage/users/', admin_user_list, name='admin_user_list'),
    path('manage/users/create/', admin_user_create, name='admin_user_create'),
    path('manage/users/<int:pk>/edit/', admin_user_edit, name='admin_user_edit'),
    path('manage/users/<int:pk>/delete/', admin_user_delete, name='admin_user_delete'),
    
    # Admin Transaction Management
    path('manage/transactions/', admin_transactions, name='admin_transactions'),
    path('manage/transactions/<int:pk>/edit/', admin_transaction_edit, name='admin_transaction_edit'),
    path('manage/transactions/<int:pk>/delete/', admin_transaction_delete, name='admin_transaction_delete'),
    
    # Admin Budget Management
    path('manage/budgets/', admin_budgets, name='admin_budgets'),
    path('manage/budgets/<int:pk>/edit/', admin_budget_edit, name='admin_budget_edit'),
    path('manage/budgets/<int:pk>/delete/', admin_budget_delete, name='admin_budget_delete'),
    
    # Admin Goal Management
    path('manage/goals/', admin_goals, name='admin_goals'),
    path('manage/goals/<int:pk>/edit/', admin_goal_edit, name='admin_goal_edit'),
    path('manage/goals/<int:pk>/delete/', admin_goal_delete, name='admin_goal_delete'),
    
    # Admin Category Management
    path('manage/categories/', admin_categories, name='admin_categories'),
    path('manage/categories/<int:pk>/edit/', admin_category_edit, name='admin_category_edit'),
    path('manage/categories/<int:pk>/delete/', admin_category_delete, name='admin_category_delete'),
    
    # Admin Reports
    path('manage/reports/', admin_reports, name='admin_reports'),
    path('manage/analyze-transactions/', admin_analyze_transactions, name='admin_analyze_transactions'),
    
    # Password reset URLs
    path('accounts/password-reset/', auth_views.PasswordResetView.as_view(template_name='core/password_reset.html'), name='password_reset'),
    path('accounts/password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='core/password_reset_done.html'), name='password_reset_done'),
    path('accounts/password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='core/password_reset_confirm.html'), name='password_reset_confirm'),
    path('accounts/password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(template_name='core/password_reset_complete.html'), name='password_reset_complete'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
