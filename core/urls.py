from django.urls import path
from . import views
from .async_views import async_transaction_list, async_transaction_detail
from django.shortcuts import render

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    
    # Transaction URLs
    path('transactions/', views.transaction_list, name='transaction_list'),
    path('transactions/create/', views.transaction_create, name='transaction_create'),
    path('transactions/<int:pk>/edit/', views.transaction_edit, name='transaction_edit'),
    path('transactions/<int:pk>/delete/', views.transaction_delete, name='transaction_delete'),
    
    # Async API URLs
    path('api/transactions/', async_transaction_list, name='async_transaction_list'),
    path('api/transactions/<int:pk>/', async_transaction_detail, name='async_transaction_detail'),
    
    # Budget URLs
    path('budgets/', views.budget_list, name='budget_list'),
    path('budgets/create/', views.budget_create, name='budget_create'),
    path('budgets/<int:pk>/edit/', views.budget_edit, name='budget_edit'),
    path('budgets/<int:pk>/delete/', views.budget_delete, name='budget_delete'),
    
    # Goal URLs
    path('goals/', views.goal_list, name='goal_list'),
    path('goals/create/', views.goal_create, name='goal_create'),
    path('goals/<int:pk>/edit/', views.goal_edit, name='goal_edit'),
    path('goals/<int:pk>/delete/', views.goal_delete, name='goal_delete'),
    
    # Category URLs
    path('categories/', views.category_list, name='category_list'),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/<int:pk>/edit/', views.category_edit, name='category_edit'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),
    
    # Settings URL
    path('settings/', views.settings_view, name='settings'),
    
    # API Demo URL
    path('api-demo/', lambda request: render(request, 'core/api_demo.html'), name='api_demo'),
    
    # Admin URLs
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/login/', views.admin_login, name='admin_login'),
    
    # Custom Authentication URLs
    path('login/', views.custom_login, name='login'),
    path('logout/', views.custom_logout, name='custom_logout'),
    path('register/', views.register_view, name='register'),
    path('register/commercial/', views.commercial_register, name='commercial_register'),
    
    # Trends URL
    path('trends/', views.trends_view, name='trends'),
    
    # Password Reset URLs
    path('password-reset/', views.password_reset_otp, name='password_reset_otp'),
    path('password-reset-confirm/', views.password_reset_confirm_custom, name='password_reset_confirm_custom'),
    
    # Export PDF URL
    path('export-pdf/', views.export_financial_data_pdf, name='export_pdf'),
] 