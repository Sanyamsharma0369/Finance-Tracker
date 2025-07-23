from django.urls import path
from . import views_class_based as views

urlpatterns = [
    # Transaction URLs - Class-based views
    path('class/transactions/', 
        views.TransactionListView.as_view(), 
        name='transaction_list_class'),
    path('class/transactions/<int:pk>/', 
        views.TransactionDetailView.as_view(), 
        name='transaction_detail_class'),
    path('class/transactions/create/', 
        views.TransactionCreateView.as_view(), 
        name='transaction_create_class'),
    path('class/transactions/<int:pk>/edit/', 
        views.TransactionUpdateView.as_view(), 
        name='transaction_edit_class'),
    path('class/transactions/<int:pk>/delete/', 
        views.TransactionDeleteView.as_view(), 
        name='transaction_delete_class'),
    
    # Budget URLs - Class-based views
    path('class/budgets/', 
        views.BudgetListView.as_view(), 
        name='budget_list_class'),
    
    # Category URLs - Class-based views
    path('class/categories/', 
        views.CategoryListView.as_view(), 
        name='category_list_class'),
    
    # Goal URLs - Class-based views
    path('class/goals/', 
        views.GoalListView.as_view(), 
        name='goal_list_class'),
] 