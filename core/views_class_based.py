from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils import timezone

from .models import Transaction, Category, Budget, FinancialGoal
from .forms import TransactionForm, CategoryForm, BudgetForm, FinancialGoalForm
from .utils import UserDataAccessMixin

# --------------------------------
# Transaction Views
# --------------------------------

class TransactionListView(LoginRequiredMixin, UserDataAccessMixin, ListView):
    """List view for user's transactions with data isolation"""
    model = Transaction
    template_name = 'core/transaction_list.html'
    context_object_name = 'transactions'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        transactions = context['transactions']
        
        # Calculate totals for the current user
        context['total_income'] = sum(t.amount for t in transactions if t.type == 'income')
        context['total_expenses'] = sum(t.amount for t in transactions if t.type == 'expense')
        context['balance'] = context['total_income'] - context['total_expenses']
        
        # Get categories for this user
        context['categories'] = Category.objects.filter(user=self.request.user)
        
        return context
        
class TransactionDetailView(LoginRequiredMixin, UserDataAccessMixin, DetailView):
    """Detail view for a specific transaction with data isolation"""
    model = Transaction
    template_name = 'core/transaction_detail.html'
    context_object_name = 'transaction'
    
class TransactionCreateView(LoginRequiredMixin, CreateView):
    """Create view for a new transaction"""
    model = Transaction
    form_class = TransactionForm
    template_name = 'core/transaction_form.html'
    success_url = reverse_lazy('transaction_list')
    
    def form_valid(self, form):
        # Set the current user before saving
        form.instance.user = self.request.user
        messages.success(self.request, 'Transaction created successfully.')
        return super().form_valid(form)
        
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Filter the categories in the form to only show user's categories
        kwargs['user'] = self.request.user
        return kwargs
        
class TransactionUpdateView(LoginRequiredMixin, UserDataAccessMixin, UpdateView):
    """Update view for an existing transaction with data isolation"""
    model = Transaction
    form_class = TransactionForm
    template_name = 'core/transaction_form.html'
    success_url = reverse_lazy('transaction_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Transaction updated successfully.')
        return super().form_valid(form)
        
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Filter the categories in the form to only show user's categories
        kwargs['user'] = self.request.user
        return kwargs
        
class TransactionDeleteView(LoginRequiredMixin, UserDataAccessMixin, DeleteView):
    """Delete view for an existing transaction with data isolation"""
    model = Transaction
    template_name = 'core/transaction_confirm_delete.html'
    success_url = reverse_lazy('transaction_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Transaction deleted successfully.')
        return super().delete(request, *args, **kwargs)

# --------------------------------
# Budget Views
# --------------------------------

class BudgetListView(LoginRequiredMixin, UserDataAccessMixin, ListView):
    """List view for user's budgets with data isolation"""
    model = Budget
    template_name = 'core/budget_list.html'
    context_object_name = 'budgets'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        budgets = context['budgets']
        
        # Add current month and spend percentage calculation
        current_month = timezone.now().month
        current_year = timezone.now().year
        
        for budget in budgets:
            # Calculate spending for the current month
            category_expenses = Transaction.objects.filter(
                user=self.request.user,
                category=budget.category,
                date__month=current_month,
                date__year=current_year,
                transaction_type='expense'
            ).values_list('amount', flat=True)
            
            spent = sum(category_expenses)
            budget.spent = spent
            budget.percent_used = (spent / budget.amount * 100) if budget.amount > 0 else 0
            
        return context
        
# Additional Budget CRUD views similar to the Transaction views would go here...

# --------------------------------
# Financial Goal Views
# --------------------------------

class GoalListView(LoginRequiredMixin, UserDataAccessMixin, ListView):
    """List view for user's financial goals with data isolation"""
    model = FinancialGoal
    template_name = 'core/goal_list.html'
    context_object_name = 'goals'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        goals = context['goals']
        
        # Calculate progress for each goal
        for goal in goals:
            goal.percent_complete = (goal.current_amount / goal.target_amount * 100) if goal.target_amount > 0 else 0
            goal.remaining = goal.target_amount - goal.current_amount
            
            # Calculate days remaining
            if goal.target_date:
                days_remaining = (goal.target_date - timezone.now().date()).days
                goal.days_remaining = max(0, days_remaining)
                
                # Calculate daily saving needed
                if days_remaining > 0 and goal.remaining > 0:
                    goal.daily_saving_needed = goal.remaining / days_remaining
                else:
                    goal.daily_saving_needed = 0
            else:
                goal.days_remaining = None
                goal.daily_saving_needed = None
                
        return context
        
# Additional Financial Goal CRUD views would go here...

# --------------------------------
# Category Views
# --------------------------------

class CategoryListView(LoginRequiredMixin, UserDataAccessMixin, ListView):
    """List view for user's categories with data isolation"""
    model = Category
    template_name = 'core/category_list.html'
    context_object_name = 'categories'
    
# Additional Category CRUD views would go here... 