from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model, authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import send_mail
from django.utils import timezone
from django.db.models import Sum, Count, Q, F, ExpressionWrapper, DecimalField, Case, When
from django.db.models.functions import TruncMonth, Extract, Coalesce
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from django.conf import settings
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.template.loader import render_to_string
from django.core.exceptions import ObjectDoesNotExist
from django.utils.functional import cached_property
import json
import uuid
import random
import string
import logging
import os
from datetime import datetime, timedelta, date
from decimal import Decimal
from io import BytesIO
import base64
import calendar
import threading

# Import ReportLab for PDF generation
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib import colors

from .models import Transaction, Budget, Category, FinancialGoal, UserProfile, Settings, CommercialRegistration
from .forms import (TransactionForm, BudgetForm, CategoryForm, FinancialGoalForm, 
                   UserSettingsForm, UserRegistrationForm, OTPVerificationForm, 
                   CommercialRegistrationForm, AdminUserCreationForm, UserProfileForm, SettingsForm)

# Configure logging
logger = logging.getLogger(__name__)

# Email verification token generator
class EmailVerificationTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return (
            str(user.pk) + str(timestamp) + str(user.is_active)
        )

account_activation_token = EmailVerificationTokenGenerator()

def create_default_categories(user):
    """Create default categories for a new user"""
    default_categories = [
        # Income categories
        {'name': 'Salary', 'type': 'income', 'description': 'Regular employment income'},
        {'name': 'Freelance', 'type': 'income', 'description': 'Income from freelance work'},
        {'name': 'Investments', 'type': 'income', 'description': 'Income from investments'},
        {'name': 'Gifts', 'type': 'income', 'description': 'Money received as gifts'},
        
        # Expense categories
        {'name': 'Housing', 'type': 'expense', 'description': 'Rent, mortgage, property taxes'},
        {'name': 'Food', 'type': 'expense', 'description': 'Groceries, restaurants, takeout'},
        {'name': 'Transportation', 'type': 'expense', 'description': 'Gas, public transit, car maintenance'},
        {'name': 'Utilities', 'type': 'expense', 'description': 'Electricity, water, internet, phone'},
        {'name': 'Entertainment', 'type': 'expense', 'description': 'Movies, games, subscriptions'},
        {'name': 'Shopping', 'type': 'expense', 'description': 'Clothing, electronics, household items'},
        {'name': 'Healthcare', 'type': 'expense', 'description': 'Doctor visits, medicine, insurance'},
        {'name': 'Education', 'type': 'expense', 'description': 'Tuition, books, courses'},
        {'name': 'Travel', 'type': 'expense', 'description': 'Vacations, flights, accommodations'},
        {'name': 'Gifts', 'type': 'expense', 'description': 'Presents for others'},
        {'name': 'Personal Care', 'type': 'expense', 'description': 'Haircuts, cosmetics, gym'},
    ]
    
    for cat in default_categories:
        Category.objects.get_or_create(
            name=cat['name'],
            type=cat['type'],
            description=cat['description'],
            user=user
        )

def dashboard(request):
    # Initialize dictionaries for charts
    income_by_category = {}
    expense_by_category = {}
    monthly_data = {
        'income': {},
        'expense': {}
    }
    
    # For recommendations and insights
    expense_insights = []
    savings_recommendations = []

    # Get current date for calculations
    current_date = timezone.now()
    current_month = current_date.month
    current_year = current_date.year
    previous_month = (current_date - timedelta(days=30)).month
    previous_month_year = (current_date - timedelta(days=30)).year
    
    # Get user currency info
    currency_info = get_user_currency(request)
    currency_symbol = currency_info['currency_symbol']
    
    # Get data based on authentication status
    if request.user.is_authenticated:
        # Get real transactions for authenticated users
        recent_transactions = Transaction.objects.filter(user=request.user).order_by('-date')[:5]
        
        # Recent stats: current month's income and expenses
        current_month_income = Transaction.objects.filter(
            user=request.user,
            date__month=current_month,
            date__year=current_year,
            type='income'
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        current_month_expenses = Transaction.objects.filter(
            user=request.user,
            date__month=current_month,
            date__year=current_year,
            type='expense'
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        # Previous month's expenses for comparison
        previous_month_expenses = Transaction.objects.filter(
            user=request.user,
            date__month=previous_month,
            date__year=previous_month_year,
            type='expense'
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        # Get category-wise expenses for the current month
        category_expenses = {}
        expense_categories = Transaction.objects.filter(
            user=request.user,
            date__month=current_month,
            date__year=current_year,
            type='expense'
        ).values('category__name').annotate(total=Sum('amount')).order_by('-total')
        
        for category in expense_categories:
            category_expenses[category['category__name']] = category['total']
        
        # Generate expense insights and recommendations
        # 1. Compare with previous month
        if previous_month_expenses > 0:
            percent_change = ((current_month_expenses - previous_month_expenses) / previous_month_expenses) * 100
            if percent_change > 10:
                expense_insights.append(f"Your spending is up {percent_change:.1f}% compared to last month.")
            elif percent_change < -10:
                expense_insights.append(f"Great job! Your spending is down {abs(percent_change):.1f}% compared to last month.")
        
        # 2. Identify top spending categories and provide recommendations
        if expense_categories:
            top_category = expense_categories[0]['category__name']
            top_amount = expense_categories[0]['total']
            top_percent = (top_amount / current_month_expenses) * 100 if current_month_expenses > 0 else 0
            
            expense_insights.append(f"Your highest spending category is {top_category} at ${top_amount:.2f} ({top_percent:.1f}% of total expenses).")
            
            # Category-specific recommendations
            if top_category == "Food" and top_percent > 25:
                savings_recommendations.append("Consider meal planning and grocery shopping with a list to reduce food expenses.")
            elif top_category == "Entertainment" and top_percent > 15:
                savings_recommendations.append("Look for free or low-cost entertainment options to reduce discretionary spending.")
            elif top_category == "Shopping" and top_percent > 20:
                savings_recommendations.append("Try implementing a 24-hour rule before making non-essential purchases.")
            elif top_category == "Transportation" and top_percent > 15:
                savings_recommendations.append("Consider carpooling, public transportation, or combining errands to save on fuel costs.")
        
        # 3. Savings rate recommendations
        savings_rate = ((current_month_income - current_month_expenses) / current_month_income) * 100 if current_month_income > 0 else 0
        if savings_rate < 10 and current_month_income > 0:
            savings_recommendations.append("Aim to save at least 10-15% of your income. Consider automating your savings.")
        elif savings_rate >= 20:
            expense_insights.append(f"Great job saving {savings_rate:.1f}% of your income this month!")
        
        # 4. Budget adherence
        over_budget_categories = []
        budgets = Budget.objects.filter(user=request.user)
        for budget in budgets:
            expenses = Transaction.objects.filter(
                user=request.user,
                category=budget.category,
                date__month=current_month,
                date__year=current_year,
                type='expense'
            ).aggregate(Sum('amount'))['amount__sum'] or 0
            
            budget.spent = expenses
            if budget.amount > 0:
                budget.progress = min(100, int((expenses / budget.amount) * 100))
                if expenses > budget.amount:
                    over_budget_categories.append((budget.category.name, expenses - budget.amount))
            else:
                budget.progress = 0
        
        if over_budget_categories:
            overspent_category, amount_over = max(over_budget_categories, key=lambda x: x[1])
            expense_insights.append(f"You're ${amount_over:.2f} over budget in {overspent_category}. Consider adjusting your spending in this category.")
        
        # Filter to top 3 budgets - manually sort instead of using order_by on non-existent field
        all_budgets = list(budgets)
        all_budgets.sort(key=lambda x: x.progress, reverse=True)
        top_budgets = all_budgets[:3]
        
        # Get goals and calculate progress
        goals = FinancialGoal.objects.filter(user=request.user).order_by('deadline')[:3]
        for goal in goals:
            if goal.target_amount > 0:
                # Don't set the progress property directly, use progress_value attribute instead
                goal.progress_value = min(100, int((goal.current_amount / goal.target_amount) * 100))
            else:
                goal.progress_value = 0
        
        # Prepare chart data
        transactions = Transaction.objects.filter(user=request.user)
        
        # Income by category
        income_transactions = transactions.filter(type='income')
        for transaction in income_transactions:
            # Check if category exists before accessing its name
            if transaction.category:
                category_name = transaction.category.name
            else:
                category_name = "Uncategorized"
            
            if category_name in income_by_category:
                income_by_category[category_name] += float(transaction.amount)
            else:
                income_by_category[category_name] = float(transaction.amount)
        
        # Expense by category
        expense_transactions = transactions.filter(type='expense')
        for transaction in expense_transactions:
            # Check if category exists before accessing its name
            if transaction.category:
                category_name = transaction.category.name
            else:
                category_name = "Uncategorized"
            
            if category_name in expense_by_category:
                expense_by_category[category_name] += float(transaction.amount)
            else:
                expense_by_category[category_name] = float(transaction.amount)
        
        # Monthly income and expense data for trend chart
        # Go back 6 months
        for i in range(5, -1, -1):
            # Calculate the month we're looking at
            month_date = current_date - timedelta(days=30*i)
            month_key = month_date.strftime('%b')  # Get abbreviated month name
            
            # Get income for this month
            month_income = transactions.filter(
                type='income',
                date__month=month_date.month,
                date__year=month_date.year
            ).aggregate(Sum('amount'))['amount__sum'] or 0
            
            # Get expenses for this month
            month_expenses = transactions.filter(
                type='expense',
                date__month=month_date.month,
                date__year=month_date.year
            ).aggregate(Sum('amount'))['amount__sum'] or 0
            
            # Convert to float for JSON serialization
            monthly_data['income'][month_key] = float(month_income)
            monthly_data['expense'][month_key] = float(month_expenses)
            
    else:
        # Sample transactions with Indian Rupee values
        sample_transactions = [
            {'id': 1, 'description': 'Salary', 'amount': 45000.00, 'date': timezone.now().date() - timedelta(days=5), 'type': 'income', 'category': 'Salary'},
            {'id': 2, 'description': 'Rent', 'amount': 15000.00, 'date': timezone.now().date() - timedelta(days=3), 'type': 'expense', 'category': 'Housing'},
            {'id': 3, 'description': 'Groceries', 'amount': 3500.00, 'date': timezone.now().date() - timedelta(days=2), 'type': 'expense', 'category': 'Food'},
            {'id': 4, 'description': 'Uber', 'amount': 450.00, 'date': timezone.now().date() - timedelta(days=1), 'type': 'expense', 'category': 'Transportation'},
            {'id': 5, 'description': 'Freelance Work', 'amount': 12000.00, 'date': timezone.now().date() - timedelta(days=7), 'type': 'income', 'category': 'Freelance'},
        ]
        
        # Create sample transaction objects for anonymous users
        class SampleTransaction:
            def __init__(self, id, description, amount, date, transaction_type, category):
                self.id = id
                self.pk = id  # Add pk attribute needed for URL generation
                self.description = description
                self.amount = amount
                self.date = date
                self.type = transaction_type
                self.category = type('Category', (), {'name': category})
        
        # Convert dictionary transactions to objects for template compatibility
        recent_transactions = [
            SampleTransaction(
                t['id'],
                t['description'],
                t['amount'],
                t['date'],
                t['type'],
                t['category']
            ) for t in sample_transactions
        ]
        
        # Current month stats
        current_month_income = 3500.00
        current_month_expenses = 2100.00
        
        # Sample budgets
        top_budgets = [
            {'id': 1, 'category': {'name': 'Housing'}, 'amount': 1500.00, 'spent': 1200.00, 'progress': 80},
            {'id': 2, 'category': {'name': 'Food'}, 'amount': 500.00, 'spent': 450.00, 'progress': 90},
            {'id': 3, 'category': {'name': 'Transportation'}, 'amount': 300.00, 'spent': 180.00, 'progress': 60}
        ]
        
        # Sample goals
        goals = [
            {'id': 1, 'name': 'Emergency Fund', 'target_amount': 10000.00, 'current_amount': 5000.00, 'deadline': current_date + timedelta(days=180), 'progress': 50},
            {'id': 2, 'name': 'New Car', 'target_amount': 25000.00, 'current_amount': 5000.00, 'deadline': current_date + timedelta(days=360), 'progress': 20},
            {'id': 3, 'name': 'Vacation', 'target_amount': 3000.00, 'current_amount': 1200.00, 'deadline': current_date + timedelta(days=90), 'progress': 40}
        ]
        
        # Sample chart data
        income_by_category = {
            'Salary': 3000.00,
            'Freelance': 500.00,
            'Investments': 200.00,
            'Other': 100.00
        }
        
        expense_by_category = {
            'Housing': 1200.00,
            'Food': 600.00,
            'Transportation': 250.00,
            'Utilities': 200.00,
            'Entertainment': 150.00
        }
        
        # Sample monthly data with realistic values - use actual month names
        months = []
        for i in range(5, -1, -1):
            month_date = current_date - timedelta(days=30*i)
            month_key = month_date.strftime('%b')
            months.append(month_key)
            monthly_data['income'][month_key] = round(3000 + random.uniform(-500, 500), 2)
            monthly_data['expense'][month_key] = round(2000 + random.uniform(-300, 300), 2)
        
        # Sample insights and recommendations
        expense_insights = [
            "Your highest spending category is Housing at $1,200.00 (57% of total expenses).",
            "You're spending has remained consistent compared to last month."
        ]
        
        savings_recommendations = [
            "Consider meal planning and grocery shopping with a list to reduce food expenses.",
            "Try implementing a 24-hour rule before making non-essential purchases.",
            "Aim to save at least 10-15% of your income. Consider automating your savings."
        ]
    
    # Calculate net income and savings rate
    net_income = current_month_income - current_month_expenses
    savings_rate = (current_month_income - current_month_expenses) / current_month_income * 100 if current_month_income > 0 else 0
    
    # Prepare chart data for JS
    chart_data = {
        'labels': list(monthly_data['income'].keys()),
        'income': list(monthly_data['income'].values()),
        'expenses': list(monthly_data['expense'].values())
    }
    
    # Prepare context for the template
    context = {
        'recent_transactions': recent_transactions,
        'current_month_income': current_month_income,
        'current_month_expenses': current_month_expenses,
        'net_income': net_income,
        'savings_rate': int(savings_rate),
        'budgets': top_budgets,
        'goals': goals,
        'income_by_category': income_by_category,
        'expense_by_category': expense_by_category,
        'monthly_data': monthly_data,
        'chart_data': chart_data,
        'expense_insights': expense_insights,
        'savings_recommendations': savings_recommendations,
        'upcoming_goals': goals,
        'currency_symbol': currency_symbol,
    }
    
    return render(request, 'core/dashboard.html', context)

def transaction_list(request):
    """View to display a list of transactions"""
    # Initialize variables for the template context
    transactions = []
    total_income = 0
    total_expenses = 0
    categories = []
    
    class SampleTransaction:
        """Class to create sample transaction objects with all required attributes"""
        def __init__(self, id, description, amount, date, transaction_type, category):
            self.id = id
            self.pk = id  # Add pk attribute for URL generation
            self.description = description
            self.amount = amount
            self.date = date
            self.type = transaction_type  # Store as type to match model field
            self.category = type('Category', (), {'name': category})()

    if request.user.is_authenticated:
        # Get the user's transactions
        transactions = Transaction.objects.filter(user=request.user).order_by('-date')
        
        # Calculate totals
        total_income = transactions.filter(type='income').aggregate(
            Sum('amount'))['amount__sum'] or 0
        total_expenses = transactions.filter(type='expense').aggregate(
            Sum('amount'))['amount__sum'] or 0
            
        # Get categories for filtering
        categories = Category.objects.filter(user=request.user)
    else:
        # Sample data for anonymous users
        sample_data = [
            {'id': 1, 'description': 'Salary', 'amount': 45000.00, 'date': timezone.now().date() - timedelta(days=5), 'type': 'income', 'category': 'Salary'},
            {'id': 2, 'description': 'Rent', 'amount': 15000.00, 'date': timezone.now().date() - timedelta(days=3), 'type': 'expense', 'category': 'Housing'},
            {'id': 3, 'description': 'Groceries', 'amount': 3500.00, 'date': timezone.now().date() - timedelta(days=2), 'type': 'expense', 'category': 'Food'},
            {'id': 4, 'description': 'Uber', 'amount': 450.00, 'date': timezone.now().date() - timedelta(days=1), 'type': 'expense', 'category': 'Transportation'},
            {'id': 5, 'description': 'Freelance Work', 'amount': 12000.00, 'date': timezone.now().date() - timedelta(days=7), 'type': 'income', 'category': 'Freelance'},
            {'id': 6, 'description': 'Mobile Bill', 'amount': 999.00, 'date': timezone.now().date() - timedelta(days=10), 'type': 'expense', 'category': 'Utilities'},
            {'id': 7, 'description': 'Restaurant', 'amount': 1800.00, 'date': timezone.now().date() - timedelta(days=6), 'type': 'expense', 'category': 'Dining Out'},
            {'id': 8, 'description': 'Electricity Bill', 'amount': 2500.00, 'date': timezone.now().date() - timedelta(days=15), 'type': 'expense', 'category': 'Utilities'},
            {'id': 9, 'description': 'Investment Return', 'amount': 5000.00, 'date': timezone.now().date() - timedelta(days=20), 'type': 'income', 'category': 'Investments'},
            {'id': 10, 'description': 'Movie Tickets', 'amount': 800.00, 'date': timezone.now().date() - timedelta(days=8), 'type': 'expense', 'category': 'Entertainment'},
        ]
        
        # Create SampleTransaction objects instead of dictionaries
        transactions = [
            SampleTransaction(
                id=item['id'],
                description=item['description'],
                amount=item['amount'],
                date=item['date'],
                transaction_type=item['type'],
                category=item['category']
            )
            for item in sample_data
        ]
        
        # Calculate totals
        total_income = sum(t.amount for t in transactions if t.type == 'income')
        total_expenses = sum(t.amount for t in transactions if t.type == 'expense')
        
        # Sample categories for filtering
        categories = [
            type('Category', (), {'id': 1, 'name': 'Housing', 'type': 'expense'})(),
            type('Category', (), {'id': 2, 'name': 'Food', 'type': 'expense'})(),
            type('Category', (), {'id': 3, 'name': 'Transportation', 'type': 'expense'})(),
            type('Category', (), {'id': 4, 'name': 'Utilities', 'type': 'expense'})(),
            type('Category', (), {'id': 5, 'name': 'Entertainment', 'type': 'expense'})(),
            type('Category', (), {'id': 6, 'name': 'Salary', 'type': 'income'})(),
            type('Category', (), {'id': 7, 'name': 'Freelance', 'type': 'income'})(),
            type('Category', (), {'id': 8, 'name': 'Investments', 'type': 'income'})(),
        ]
    
    context = {
        'transactions': transactions,
        'total_income': total_income,
        'total_expenses': total_expenses,
        'net': total_income - total_expenses,
        'categories': categories
    }
    
    return render(request, 'core/transaction_list.html', context)

def transaction_create(request):
    if request.method == 'POST':
        form = TransactionForm(request.POST, request.FILES)
        if form.is_valid():
            transaction = form.save(commit=False)
            if request.user.is_authenticated:
                # Ensure the category belongs to the current user
                category = form.cleaned_data.get('category')
                if category and category.user.id != request.user.id:
                    messages.error(request, 'Invalid category selected.')
                    return redirect('transaction_list')
                    
                transaction.user = request.user
                transaction.save()
                messages.success(request, 'Transaction created successfully!')
            else:
                messages.warning(request, 'Demo mode active. Transactions can only be created by registered users.')
            return redirect('transaction_list')
    else:
        form = TransactionForm()
    
    # Get categories for the form, depending on user authentication
    if request.user.is_authenticated:
        categories = Category.objects.filter(user=request.user)
    else:
        # For anonymous users, create sample categories
        sample_categories = [
            {'id': 1, 'name': 'Salary', 'type': 'income'},
            {'id': 2, 'name': 'Freelance', 'type': 'income'},
            {'id': 3, 'name': 'Housing', 'type': 'expense'},
            {'id': 4, 'name': 'Food', 'type': 'expense'},
            {'id': 5, 'name': 'Transportation', 'type': 'expense'},
            {'id': 6, 'name': 'Entertainment', 'type': 'expense'},
            {'id': 7, 'name': 'Utilities', 'type': 'expense'},
        ]
        
        # Create sample Category objects
        class SampleCategory:
            def __init__(self, id, name, type):
                self.id = id
                self.pk = id  # Add pk attribute for form rendering
                self.name = name
                self.type = type
                
        categories = [SampleCategory(**cat) for cat in sample_categories]
        messages.info(request, 'Demo mode active. Please log in to create real transactions.')
    
    # Get currency info from context processor
    currency_info = get_user_currency(request)
    
    return render(request, 'core/transaction_form.html', {
        'form': form,
        'categories': categories,
        'title': 'Create Transaction',
        'currency_symbol': currency_info['currency_symbol']
    })

def transaction_edit(request, pk):
    if request.user.is_authenticated:
        # Ensure the transaction belongs to the current user
        transaction = get_object_or_404(Transaction, pk=pk, user=request.user)
        
        if request.method == 'POST':
            form = TransactionForm(request.POST, request.FILES, instance=transaction)
            if form.is_valid():
                # Extra security: verify the category belongs to the user
                category = form.cleaned_data.get('category')
                if category and category.user.id != request.user.id:
                    messages.error(request, 'Invalid category selected.')
                    return redirect('transaction_list')
                    
                form.save()
                messages.success(request, 'Transaction updated successfully!')
                return redirect('transaction_list')
        else:
            form = TransactionForm(instance=transaction)
        
        # Only show categories belonging to the user
        categories = Category.objects.filter(user=request.user)
        return render(request, 'core/transaction_form.html', {
            'form': form,
            'categories': categories,
            'transaction': transaction,
            'title': 'Edit Transaction'
        })
    else:
        messages.warning(request, 'Demo mode active. Editing is only available for registered users.')
        return redirect('transaction_list')

def transaction_delete(request, pk):
    if request.user.is_authenticated:
        transaction = get_object_or_404(Transaction, pk=pk, user=request.user)
        
        if request.method == 'POST':
            transaction.delete()
            messages.success(request, 'Transaction deleted successfully!')
            return redirect('transaction_list')
        
        return render(request, 'core/transaction_confirm_delete.html', {'transaction': transaction})
    else:
        messages.warning(request, 'Demo mode active. Deletion is only available for registered users.')
        return redirect('transaction_list')

def budget_list(request):
    # Initialize variables
    total_budget = 0
    total_spent = 0
    total_remaining = 0
    
    class SampleBudget:
        """Class to create sample budget objects with all required attributes"""
        def __init__(self, id, category_name, amount, spent, progress):
            self.id = id
            self.pk = id  # Add pk attribute for URL generation
            self.amount = amount
            self.spent = spent
            self.remaining = amount - spent
            self.progress = progress
            self.category = type('Category', (), {'name': category_name})()
    
    if request.user.is_authenticated:
        budgets = Budget.objects.filter(user=request.user).order_by('-period')
        
        # Get current date for calculations
        current_date = timezone.now()
        current_month = current_date.month
        current_year = current_date.year
        
        # Calculate spent amount for each budget
        for budget in budgets:
            # Calculate amount spent in the current month for this category
            spent = Transaction.objects.filter(
                user=request.user,
                category=budget.category,
                date__month=current_month,
                date__year=current_year,
                type='expense'
            ).aggregate(Sum('amount'))['amount__sum'] or 0
            
            # Add spent as an attribute to the budget object
            budget.spent = spent
            
            # Calculate progress percentage
            if budget.amount > 0:
                budget.progress = min(100, int((spent / budget.amount) * 100))
            else:
                budget.progress = 0
                
            # Calculate remaining budget
            budget.remaining = budget.amount - spent
            
            # Update totals
            total_budget += budget.amount
            total_spent += budget.spent
            total_remaining += budget.remaining
    else:
        # Sample data for anonymous users
        sample_data = [
            {'id': 1, 'category_name': 'Housing', 'amount': 18000.00, 'spent': 15000.00, 'progress': 83},
            {'id': 2, 'category_name': 'Food', 'amount': 10000.00, 'spent': 6000.00, 'progress': 60},
            {'id': 3, 'category_name': 'Transportation', 'amount': 5000.00, 'spent': 3000.00, 'progress': 60},
            {'id': 4, 'category_name': 'Entertainment', 'amount': 3000.00, 'spent': 1800.00, 'progress': 60},
            {'id': 5, 'category_name': 'Utilities', 'amount': 5000.00, 'spent': 3500.00, 'progress': 70},
        ]
        
        # Create SampleBudget objects
        budgets = [
            SampleBudget(
                id=item['id'],
                category_name=item['category_name'],
                amount=item['amount'],
                spent=item['spent'],
                progress=item['progress']
            )
            for item in sample_data
        ]
        
        # Calculate totals
        total_budget = sum(b.amount for b in budgets)
        total_spent = sum(b.spent for b in budgets)
        total_remaining = total_budget - total_spent
    
    return render(request, 'core/budget_list.html', {
        'budgets': budgets,
        'total_budget': total_budget,
        'total_spent': total_spent,
        'total_remaining': total_remaining
    })

def budget_create(request):
    if request.method == 'POST':
        form = BudgetForm(request.POST)
        if form.is_valid():
            budget = form.save(commit=False)
            if request.user.is_authenticated:
                # Ensure the category belongs to the current user
                category = form.cleaned_data.get('category')
                if category and category.user.id != request.user.id:
                    messages.error(request, 'Invalid category selected.')
                    return redirect('budget_list')
                    
                budget.user = request.user
                # Set period to 'monthly' by default if not provided
                if not budget.period:
                    budget.period = 'monthly'
                
                # Set the month field to the first day of the current month
                # This is required because the database schema still has this field
                # but it's not in the model definition
                budget.month = timezone.now().date().replace(day=1)
                
                budget.save()
                messages.success(request, 'Budget created successfully!')
                return redirect('budget_list')
            else:
                messages.warning(request, 'Demo mode active. Budgets can only be created by registered users.')
                return redirect('budget_list')
        else:
            # Add more detailed error messages for better user feedback
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = BudgetForm()
        # Pre-populate with current month
        form.initial = {
            'period': 'monthly',
        }
    
    # Get categories for the current user or return empty list if not authenticated
    categories = Category.objects.filter(user=request.user) if request.user.is_authenticated else []
    
    return render(request, 'core/budget_form.html', {'form': form, 'categories': categories})

def budget_edit(request, pk):
    if request.user.is_authenticated:
        # Ensure the budget belongs to the current user
        budget = get_object_or_404(Budget, pk=pk, user=request.user)
    else:
        messages.warning(request, 'Demo mode active. Editing is only available for registered users.')
        return redirect('budget_list')
        
    if request.method == 'POST':
        form = BudgetForm(request.POST, instance=budget)
        if form.is_valid():
            # Extra security: verify the category belongs to the user
            category = form.cleaned_data.get('category')
            if category and category.user.id != request.user.id:
                messages.error(request, 'Invalid category selected.')
                return redirect('budget_list')
                
            form.save()
            messages.success(request, 'Budget updated successfully!')
            return redirect('budget_list')
    else:
        form = BudgetForm(instance=budget)
    
    # Only show categories belonging to the user
    categories = Category.objects.filter(user=request.user)
    return render(request, 'core/budget_form.html', {'form': form, 'categories': categories})

def budget_delete(request, pk):
    if request.user.is_authenticated:
        budget = get_object_or_404(Budget, pk=pk, user=request.user)
    else:
        messages.warning(request, 'Demo mode active. Deletion is only available for registered users.')
        return redirect('budget_list')
        
    if request.method == 'POST':
        budget.delete()
        messages.success(request, 'Budget deleted successfully!')
        return redirect('budget_list')
    return render(request, 'core/budget_confirm_delete.html', {'object': budget})

def goal_list(request):
    class SampleGoal:
        """Class to create sample goal objects with all required attributes"""
        def __init__(self, id, name, target_amount, current_amount, deadline, progress):
            self.id = id
            self.pk = id  # Add pk attribute for URL generation
            self.name = name
            self.target_amount = target_amount
            self.current_amount = current_amount
            self.deadline = deadline
            self.progress_value = progress  # Using progress_value instead of _progress
            self.remaining = target_amount - current_amount
            # Convert deadline date to datetime or using timezone.now().date() for comparison
            self.days_left = (deadline - timezone.now().date()).days
    
    if request.user.is_authenticated:
        goals = FinancialGoal.objects.filter(user=request.user).order_by('deadline')
        
        # Calculate days left and remaining amount for each goal
        # Progress is already a property of the model, so no need to set it
        for goal in goals:
            goal.remaining = goal.target_amount - goal.current_amount
            # Fix: Convert timezone.now() to date for comparison with goal.deadline which is a date
            goal.days_left = (goal.deadline - timezone.now().date()).days
            # Store the calculated progress in progress_value instead of _progress
            goal.progress_value = min(100, int(goal.progress))
    else:
        # Sample data for anonymous users
        sample_data = [
            {'id': 1, 'name': 'Emergency Fund', 'target_amount': 300000.00, 'current_amount': 150000.00, 'deadline': timezone.now().date() + timedelta(days=180), 'progress': 50},
            {'id': 2, 'name': 'New Car', 'target_amount': 750000.00, 'current_amount': 150000.00, 'deadline': timezone.now().date() + timedelta(days=360), 'progress': 20},
            {'id': 3, 'name': 'Vacation', 'target_amount': 100000.00, 'current_amount': 40000.00, 'deadline': timezone.now().date() + timedelta(days=90), 'progress': 40},
        ]
        
        # Create SampleGoal objects
        goals = [
            SampleGoal(
                id=item['id'],
                name=item['name'],
                target_amount=item['target_amount'],
                current_amount=item['current_amount'],
                deadline=item['deadline'],
                progress=item['progress']
            )
            for item in sample_data
        ]
    
    return render(request, 'core/goal_list.html', {'goals': goals})

def goal_create(request):
    if request.method == 'POST':
        form = FinancialGoalForm(request.POST)
        if form.is_valid():
            goal = form.save(commit=False)
            if request.user.is_authenticated:
                # Ensure the category belongs to the current user
                category = form.cleaned_data.get('category')
                if category and category.user.id != request.user.id:
                    messages.error(request, 'Invalid category selected.')
                    return redirect('goal_list')
                    
                goal.user = request.user
                goal.save()
                messages.success(request, 'Financial goal created successfully!')
                return redirect('goal_list')
            else:
                messages.warning(request, 'Demo mode active. Goals can only be created by registered users.')
                return redirect('goal_list')
        else:
            # Add more detailed error messages for better user feedback
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = FinancialGoalForm()
        # Set default values
        form.initial = {
            'deadline': (timezone.now() + timedelta(days=365)).date(),
            'current_amount': 0
        }
    
    # Get categories for the form, filtered by the current user
    categories = Category.objects.filter(user=request.user) if request.user.is_authenticated else []
    
    return render(request, 'core/goal_form.html', {'form': form, 'categories': categories})

def goal_edit(request, pk):
    if request.user.is_authenticated:
        # Ensure the goal belongs to the current user
        goal = get_object_or_404(FinancialGoal, pk=pk, user=request.user)
    else:
        messages.warning(request, 'Demo mode active. Editing is only available for registered users.')
        return redirect('goal_list')
        
    if request.method == 'POST':
        if 'current_amount' in request.POST:
            try:
                current_amount = float(request.POST.get('current_amount'))
                goal.current_amount = current_amount
                goal.save()
                messages.success(request, f'Progress for {goal.name} updated successfully!')
                return redirect('goal_list')
            except ValueError:
                messages.error(request, 'Invalid amount provided')
                return redirect('goal_edit', pk=pk)
        else:
            form = FinancialGoalForm(request.POST, instance=goal)
            if form.is_valid():
                # Extra security: verify the category belongs to the user
                category = form.cleaned_data.get('category')
                if category and category.user.id != request.user.id:
                    messages.error(request, 'Invalid category selected.')
                    return redirect('goal_list')
                    
                form.save()
                messages.success(request, 'Financial goal updated successfully!')
                return redirect('goal_list')
    else:
        form = FinancialGoalForm(instance=goal)
    
    # Only show categories belonging to the user
    categories = Category.objects.filter(user=request.user)
    return render(request, 'core/goal_form.html', {'form': form, 'categories': categories})

def goal_delete(request, pk):
    if request.user.is_authenticated:
        goal = get_object_or_404(FinancialGoal, pk=pk, user=request.user)
    else:
        messages.warning(request, 'Demo mode active. Deletion is only available for registered users.')
        return redirect('goal_list')
        
    if request.method == 'POST':
        goal.delete()
        messages.success(request, 'Financial goal deleted successfully!')
        return redirect('goal_list')
    return render(request, 'core/goal_confirm_delete.html', {'object': goal})

def category_list(request):
    if request.user.is_authenticated:
        # Get all categories for the user
        categories = Category.objects.filter(user=request.user)
        
        # Split categories by type
        expense_categories = categories.filter(type='expense')
        income_categories = categories.filter(type='income')
        
        # Add transaction count and total for each category
        for category in expense_categories:
            category.transaction_count = Transaction.objects.filter(
                user=request.user, category=category).count()
            category.total_amount = Transaction.objects.filter(
                user=request.user, category=category).aggregate(Sum('amount'))['amount__sum'] or 0
                
        for category in income_categories:
            category.transaction_count = Transaction.objects.filter(
                user=request.user, category=category).count()
            category.total_amount = Transaction.objects.filter(
                user=request.user, category=category).aggregate(Sum('amount'))['amount__sum'] or 0
    else:
        # Sample data for anonymous users
        categories = []
        expense_categories = []
        income_categories = []
        for i in range(1, 6):
            category = type('Category', (), {
                'id': i,
                'name': f'Sample Category {i}',
                'type': 'expense' if i % 2 == 0 else 'income',
                'description': f'Sample description for category {i}',
                'transaction_count': i * 3,
                'total_amount': i * 100.00
            })()
            categories.append(category)
            if i % 2 == 0:
                expense_categories.append(category)
            else:
                income_categories.append(category)
    
    return render(request, 'core/category_list.html', {
        'categories': categories,
        'expense_categories': expense_categories,
        'income_categories': income_categories
    })

def category_create(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            if request.user.is_authenticated:
                category.user = request.user
                category.save()
                messages.success(request, 'Category created successfully!')
            else:
                messages.warning(request, 'Demo mode active. Categories can only be created by registered users.')
            return redirect('category_list')
    else:
        form = CategoryForm()
    return render(request, 'core/category_form.html', {'form': form})

def category_edit(request, pk):
    if request.user.is_authenticated:
        category = get_object_or_404(Category, pk=pk, user=request.user)
        if request.method == 'POST':
            form = CategoryForm(request.POST, instance=category)
            if form.is_valid():
                form.save()
                messages.success(request, 'Category updated successfully!')
                return redirect('category_list')
        else:
            form = CategoryForm(instance=category)
    else:
        messages.warning(request, 'Demo mode active. Editing is only available for registered users.')
        return redirect('category_list')
    
    return render(request, 'core/category_form.html', {'form': form})

def category_delete(request, pk):
    if request.user.is_authenticated:
        category = get_object_or_404(Category, pk=pk, user=request.user)
        
        # Check if category is used in transactions or budgets
        transaction_count = Transaction.objects.filter(category=category).count()
        budget_count = Budget.objects.filter(category=category).count()
        
        if request.method == 'POST':
            category.delete()
            messages.success(request, 'Category deleted successfully!')
            return redirect('category_list')
        
        # Add count information for the template
        category.transaction_count = transaction_count
        category.budget_count = budget_count
    else:
        messages.warning(request, 'Demo mode active. Deletion is only available for registered users.')
        return redirect('category_list')
    
    return render(request, 'core/category_confirm_delete.html', {'object': category})

def settings_view(request):
    """Handle user settings and profile."""
    # Get currency info
    currency_info = get_user_currency(request)
    
    if request.user.is_authenticated:
        # Get or create user's settings
        settings, settings_created = Settings.objects.get_or_create(
            user=request.user,
            defaults={
                'currency': 'INR',
                'theme': 'dark',
                'notifications_enabled': True,
                'email_notifications': True,
                'budget_alerts': True,
                'goal_reminders': True,
                'language': 'en',
                'timezone': 'UTC',
                'date_format': '%Y-%m-%d'
            }
        )
        
        # Get or create user's profile
        profile, profile_created = UserProfile.objects.get_or_create(
            user=request.user
        )
        
        if request.method == 'POST':
            form = UserSettingsForm(request.POST, request.FILES)
            if form.is_valid():
                # Update User model
                request.user.first_name = form.cleaned_data['first_name']
                request.user.last_name = form.cleaned_data['last_name']
                request.user.email = form.cleaned_data['email']
                request.user.save()
                
                # Update UserProfile model
                profile.phone_number = form.cleaned_data['phone_number']
                if form.cleaned_data.get('profile_picture'):
                    profile.profile_picture = form.cleaned_data['profile_picture']
                profile.save()
                
                # Update Settings model
                settings.currency = form.cleaned_data['currency']
                settings.theme = form.cleaned_data['theme']
                settings.notifications_enabled = form.cleaned_data['notifications_enabled']
                settings.email_notifications = form.cleaned_data['email_notifications']
                settings.budget_alerts = form.cleaned_data['budget_alerts']
                settings.goal_reminders = form.cleaned_data['goal_reminders']
                settings.language = form.cleaned_data['language']
                settings.timezone = form.cleaned_data['timezone']
                settings.date_format = form.cleaned_data['date_format']
                settings.save()
                
                messages.success(request, 'Settings and profile updated successfully!')
                
                # Update session values to reflect changes immediately
                request.session['currency_code'] = settings.currency
                request.session['currency_symbol'] = currency_info['currency_symbols'].get(settings.currency, '₹')
                request.session['date_format'] = settings.date_format
                request.session['language'] = settings.language
                request.session['timezone'] = settings.timezone
                
                return redirect('settings')
        else:
            # Pre-populate the form with existing data
            initial_data = {
                # User data
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
                'email': request.user.email,
                
                # Profile data
                'phone_number': profile.phone_number,
                
                # Settings data
                'currency': settings.currency,
                'theme': settings.theme,
                'notifications_enabled': settings.notifications_enabled,
                'email_notifications': settings.email_notifications,
                'budget_alerts': settings.budget_alerts,
                'goal_reminders': settings.goal_reminders,
                'language': settings.language,
                'timezone': settings.timezone,
                'date_format': settings.date_format
            }
            form = UserSettingsForm(initial=initial_data)
        
        context = {
            'form': form,
            'settings': settings,
            'profile': profile,
            'user': request.user,
            'page_title': 'Settings',
            'is_settings_page': True,
            'currency_code': currency_info['currency_code'],
            'currency_symbol': currency_info['currency_symbol'],
            'currency_symbols': currency_info['currency_symbols'],
            'has_profile_picture': bool(profile.profile_picture)
        }
    else:
        # For anonymous users, create a dummy form with default values
        # but don't attempt to save it to the database
        initial_data = {
            # User data
            'first_name': 'Demo',
            'last_name': 'User',
            'email': 'demo@example.com',
            
            # Profile data
            'phone_number': '',
            
            # Settings data
            'currency': 'INR',
            'theme': 'dark',
            'notifications_enabled': True,
            'email_notifications': True,
            'budget_alerts': True,
            'goal_reminders': True,
            'language': 'en',
            'timezone': 'UTC',
            'date_format': '%Y-%m-%d'
        }
        
        form = UserSettingsForm(initial=initial_data)
        
        if request.method == 'POST':
            messages.warning(request, 'Demo mode active. Settings can only be saved in a real account.')
            return redirect('dashboard')
        
        context = {
            'form': form,
            'page_title': 'Settings',
            'is_settings_page': True,
            'is_anonymous': True,
            'currency_code': currency_info['currency_code'],
            'currency_symbol': currency_info['currency_symbol'],
            'currency_symbols': currency_info['currency_symbols']
        }
    
    return render(request, 'core/settings.html', context)

def trends_view(request):
    if request.user.is_authenticated:
        today = timezone.now()
        income_categories = Category.objects.filter(user=request.user, type='income')
        expense_categories = Category.objects.filter(user=request.user, type='expense')
        
        # Generate chart data for last 6 months
        last_6_months = [today - timedelta(days=30*i) for i in range(6)]
        chart_data = {
            'labels': [d.strftime('%b %Y') for d in reversed(last_6_months)],
            'income': [],
            'expenses': []
        }

        for date in reversed(last_6_months):
            month_start = date.replace(day=1)
            month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            
            income = Transaction.objects.filter(
                user=request.user,
                type='income',
                date__range=[month_start, month_end]
            ).aggregate(Sum('amount'))['amount__sum'] or 0
            
            expenses = Transaction.objects.filter(
                user=request.user,
                type='expense',
                date__range=[month_start, month_end]
            ).aggregate(Sum('amount'))['amount__sum'] or 0
            
            # Convert Decimal to float for JSON serialization
            chart_data['income'].append(float(income))
            chart_data['expenses'].append(float(expenses))
    else:
        # More realistic sample data for anonymous users with Indian Rupee values
        current_month = timezone.now().month
        months = []
        
        # Generate last 6 months names
        for i in range(6):
            month_date = timezone.now() - timedelta(days=30*i)
            months.append(month_date.strftime('%b %Y'))
        
        # Sample data with realistic patterns for Indian income/expenses
        chart_data = {
            'labels': list(reversed(months)),
            'income': [45000, 50000, 48000, 55000, 52000, 57000],  # More consistent income
            'expenses': [35000, 38000, 32000, 36000, 33000, 34000]  # Varying expenses
        }
        
        income_categories = []
        expense_categories = []
    
    context = {
        'chart_data': json.dumps(chart_data),
        'income_categories': income_categories,
        'expense_categories': expense_categories,
    }
    
    return render(request, 'core/trends.html', context)

# Helper function to get currency symbol and settings
def get_user_currency(request):
    currency_symbols = {
        'USD': '$',
        'EUR': '€',
        'GBP': '£',
        'JPY': '¥',
        'INR': '₹'
    }
    
    # Default currency
    currency_code = 'INR'
    currency_symbol = '₹'
    
    if request.user.is_authenticated:
        # Get the user's settings
        settings, created = Settings.objects.get_or_create(
            user=request.user,
            defaults={
                'currency': 'INR',
                'theme': 'dark',
            }
        )
        currency_code = settings.currency
        currency_symbol = currency_symbols.get(currency_code, '₹')
    
    return {
        'currency_code': currency_code,
        'currency_symbol': currency_symbol,
        'currency_symbols': currency_symbols  # Include all currency symbols
    }

# Add context processor
def add_context(request):
    """Add common data to all views."""
    # Get currency info
    currency_info = get_user_currency(request)
    
    # Default context
    context = {
        'currency_code': currency_info['currency_code'],
        'currency_symbol': currency_info['currency_symbol']
    }
    
    # Add user profile info for authenticated users
    if request.user.is_authenticated:
        try:
            profile = request.user.userprofile
            context['user_profile'] = profile
            context['has_profile_picture'] = bool(profile.profile_picture)
        except:
            # If the profile doesn't exist for some reason
            context['has_profile_picture'] = False
    
    return context

# User Registration Views
def register_view(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            # Create user and activate immediately
            user = form.save()
            
            # Set user as active (no email verification)
            user.is_active = True
            user.save()
            
            # Create user profile if one doesn't already exist
            if not UserProfile.objects.filter(user=user).exists():
                user_profile = UserProfile.objects.create(user=user)
            
            # Create default categories for the user
            create_default_categories(user)
            
            # Log the user in
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            
            messages.success(request, 'Your account has been created successfully! Welcome to Finance Tracker.')
            return redirect('dashboard')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'core/register.html', {'form': form})

def verify_otp(request):
    """
    OTP verification view
    """
    user_id = request.session.get('user_id_to_verify')
    if not user_id:
        messages.error(request, 'Something went wrong. Please try registering again.')
        return redirect('register')
    
    try:
        user = User.objects.get(pk=user_id)
        otp_verification = OTPVerification.objects.get(user=user)
    except (User.DoesNotExist, OTPVerification.DoesNotExist):
        messages.error(request, 'Something went wrong. Please try registering again.')
        return redirect('register')
    
    if request.method == 'POST':
        form = OTPVerificationForm(request.POST)
        if form.is_valid():
            otp_entered = form.cleaned_data.get('otp_code')
            
            # Check if OTP is valid
            totp = pyotp.TOTP(otp_verification.otp_secret, interval=300)
            
            if totp.verify(otp_entered, valid_window=1):
                # Mark user as active
                user.is_active = True
                user.save()
                
                # Clean up session
                if 'user_id_to_verify' in request.session:
                    del request.session['user_id_to_verify']
                
                # Log the user in with specific backend
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                
                messages.success(request, 'Account verified successfully!')
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid verification code. Please try again.')
    else:
        form = OTPVerificationForm()
    
    return render(request, 'core/verify_otp.html', {'form': form})

def resend_otp(request):
    """
    Resend OTP to user's email
    """
    user_id = request.session.get('user_id_to_verify')
    if not user_id:
        return JsonResponse({'success': False, 'message': 'Invalid session'})
    
    try:
        user = User.objects.get(pk=user_id)
        otp_verification = OTPVerification.objects.get(user=user)
        
        # Check if last OTP was sent within the last minute
        one_minute_ago = timezone.now() - timedelta(minutes=1)
        if otp_verification.updated_at and otp_verification.updated_at > one_minute_ago:
            return JsonResponse({
                'success': False, 
                'message': 'Please wait at least 1 minute before requesting a new code.'
            })
        
        # Generate new OTP
        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret, interval=300)  # 5-minute interval
        otp_code = totp.now()
        
        # Update OTP verification record
        otp_verification.otp_secret = secret
        otp_verification.updated_at = timezone.now()
        otp_verification.save()
        
        # Send email with OTP
        subject = 'Verify your Finance Tracker account'
        message = f'Your new verification code is: {otp_code}'
        email_from = settings.EMAIL_HOST_USER
        recipient_list = [user.email]
        
        send_mail(subject, message, email_from, recipient_list)
        
        return JsonResponse({'success': True, 'message': 'A new verification code has been sent to your email.'})
        
    except (User.DoesNotExist, OTPVerification.DoesNotExist):
        return JsonResponse({'success': False, 'message': 'User not found'})

def commercial_register(request):
    """
    Commercial user registration view
    """
    if request.method == 'POST':
        form = CommercialRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            # Create user with active status
            user = User.objects.create_user(
                username=form.cleaned_data['email'].split('@')[0],  # Use part of email as username
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password1']
            )
            
            # Set user as active immediately
            user.is_active = True
            user.save()
            
            # Create user profile
            if not UserProfile.objects.filter(user=user).exists():
                user_profile = UserProfile.objects.create(
                    user=user,
                    phone_number=form.cleaned_data['phone_number'],
                    is_commercial=True
                )
            
            # Create commercial registration
            commercial_reg = CommercialRegistration.objects.create(
                user=user,
                company_name=form.cleaned_data['company_name'],
                business_type=form.cleaned_data['business_type'],
                registration_number=form.cleaned_data['registration_number'],
                tax_id=form.cleaned_data['tax_id'],
                business_address=form.cleaned_data['business_address'],
                business_document=form.cleaned_data['business_document']
            )
            
            # Create default categories for the user
            create_default_categories(user)
            
            # Log the user in
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            
            messages.success(request, f'Welcome {form.cleaned_data["company_name"]}! Your commercial account has been created successfully.')
            return redirect('dashboard')
            
    else:
        form = CommercialRegistrationForm()
    
    return render(request, 'core/commercial_register.html', {'form': form})

def password_reset_otp(request):
    """
    Custom password reset view using OTP
    """
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            
            # Generate a random 6-digit OTP
            import random
            otp = ''.join([str(random.randint(0, 9)) for _ in range(6)])
            
            # Store OTP in session for verification
            request.session['reset_otp'] = otp
            request.session['reset_email'] = email
            
            # Send OTP via email
            subject = 'Password Reset OTP for Finance Tracker'
            message = f'Your OTP for password reset is: {otp}. This OTP will expire in 15 minutes.'
            from_email = 'noreply@financetracker.com'
            recipient_list = [email]
            
            try:
                send_mail(subject, message, from_email, recipient_list)
                messages.success(request, f'An OTP has been sent to {email}. Please check your email.')
                return redirect('password_reset_confirm_custom')
            except Exception as e:
                messages.error(request, f'Error sending email: {str(e)}')
        except User.DoesNotExist:
            messages.error(request, 'No user is associated with this email address.')
    
    return render(request, 'core/password_reset_otp.html')

def password_reset_confirm_custom(request):
    """
    Custom password reset confirmation view
    """
    if request.method == 'POST':
        otp = request.POST.get('otp')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        stored_otp = request.session.get('reset_otp')
        reset_email = request.session.get('reset_email')
        
        if not stored_otp or not reset_email:
            messages.error(request, 'Password reset session has expired. Please try again.')
            return redirect('password_reset_otp')
        
        if otp != stored_otp:
            messages.error(request, 'Invalid OTP. Please try again.')
            return render(request, 'core/password_reset_confirm.html')
        
        if new_password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'core/password_reset_confirm.html')
        
        try:
            user = User.objects.get(email=reset_email)
            user.set_password(new_password)
            user.save()
            
            # Clear session
            del request.session['reset_otp']
            del request.session['reset_email']
            
            messages.success(request, 'Your password has been reset successfully. You can now login with your new password.')
            return redirect('login')
        except User.DoesNotExist:
            messages.error(request, 'User not found.')
            return redirect('password_reset_otp')
    
    return render(request, 'core/password_reset_confirm.html')

def verify_commercial_otp(request):
    """
    Commercial account OTP verification view
    """
    user_id = request.session.get('user_id_to_verify')
    is_commercial = request.session.get('is_commercial')
    
    if not user_id or not is_commercial:
        messages.error(request, 'Something went wrong. Please try registering again.')
        return redirect('commercial_register')
    
    try:
        user = User.objects.get(pk=user_id)
        otp_verification = OTPVerification.objects.get(user=user)
    except (User.DoesNotExist, OTPVerification.DoesNotExist):
        messages.error(request, 'Something went wrong. Please try registering again.')
        return redirect('commercial_register')
    
    if request.method == 'POST':
        form = OTPVerificationForm(request.POST)
        if form.is_valid():
            otp_entered = form.cleaned_data.get('otp_code')
            
            # Check if OTP is valid
            totp = pyotp.TOTP(otp_verification.otp_secret, interval=300)
            
            if totp.verify(otp_entered, valid_window=1):
                # User is verified but requires admin approval for commercial accounts
                messages.success(request, 'Your account verification is complete. Your account requires admin approval before you can login. You will receive an email once your account is approved.')
                
                # Clean up session
                if 'user_id_to_verify' in request.session:
                    del request.session['user_id_to_verify']
                if 'is_commercial' in request.session:
                    del request.session['is_commercial']
                
                # Send notification to admin
                admin_email = settings.ADMIN_EMAIL if hasattr(settings, 'ADMIN_EMAIL') else settings.EMAIL_HOST_USER
                subject = 'New Commercial Account Registration'
                message = f'A new commercial account has been registered and requires approval:\n\nCompany: {user.commercialregistration.company_name}\nEmail: {user.email}\n\nPlease login to the admin panel to review and approve this account.'
                send_mail(subject, message, settings.EMAIL_HOST_USER, [admin_email])
                
                return redirect('login')
            else:
                messages.error(request, 'Invalid verification code. Please try again.')
    else:
        form = OTPVerificationForm()
    
    return render(request, 'core/verify_commercial_otp.html', {'form': form})

# Admin views
def is_admin(user):
    """Check if user is an admin"""
    return user.is_staff or user.is_superuser

def admin_dashboard(request):
    """Admin dashboard view"""
    # Check if user is authenticated and has admin privileges
    if not request.user.is_authenticated or not is_admin(request.user):
        messages.warning(request, 'Please login with administrator credentials to access the admin panel.')
        return redirect('admin_login')
    
    # Count statistics
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    commercial_accounts = UserProfile.objects.filter(is_commercial=True).count()
    pending_approvals = CommercialRegistration.objects.filter(is_approved=False).count()
    
    context = {
        'total_users': total_users,
        'active_users': active_users,
        'commercial_accounts': commercial_accounts,
        'pending_approvals': pending_approvals,
    }
    
    return render(request, 'core/admin/dashboard.html', context)

def admin_user_list(request):
    """Admin user list view"""
    # Check if user is authenticated and has admin privileges
    if not request.user.is_authenticated or not is_admin(request.user):
        messages.warning(request, 'Please login with administrator credentials to access the admin panel.')
        return redirect('admin_login')
    
    users = User.objects.all().select_related('userprofile')
    
    # Filter functionality
    account_type = request.GET.get('account_type')
    status = request.GET.get('status')
    
    if account_type == 'personal':
        users = users.filter(userprofile__is_commercial=False)
    elif account_type == 'commercial':
        users = users.filter(userprofile__is_commercial=True)
    
    if status == 'active':
        users = users.filter(is_active=True)
    elif status == 'inactive':
        users = users.filter(is_active=False)
    
    context = {
        'users': users,
        'account_type': account_type,
        'status': status,
    }
    
    return render(request, 'core/admin/user_list.html', context)

@login_required
@user_passes_test(is_admin)
def admin_user_create(request):
    """Admin create user view"""
    # Check if user is authenticated and has admin privileges
    if not request.user.is_authenticated or not is_admin(request.user):
        messages.warning(request, 'Please login with administrator credentials to access the admin panel.')
        return redirect('admin_login')
    
    if request.method == 'POST':
        form = AdminUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create default categories for the user
            create_default_categories(user)
            messages.success(request, f'User {user.username} created successfully')
            return redirect('admin_user_list')
        else:
            # Debug: Print form errors to the console
            print(f"Form errors: {form.errors}")
            messages.error(request, f"Error creating user. Please check the form.")
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = AdminUserCreationForm()
    
    return render(request, 'core/admin/user_form.html', {
        'form': form,
        'action': 'Create'
    })

@login_required
@user_passes_test(is_admin)
def admin_user_edit(request, pk):
    """Admin edit user view"""
    # Check if user is authenticated and has admin privileges
    if not request.user.is_authenticated or not is_admin(request.user):
        messages.warning(request, 'Please login with administrator credentials to access the admin panel.')
        return redirect('admin_login')
    
    try:
        user = User.objects.get(pk=pk)
    except User.DoesNotExist:
        messages.error(request, 'User not found')
        return redirect('admin_user_list')
    
    profile, created = UserProfile.objects.get_or_create(user=user)
    
    if request.method == 'POST':
        # Basic user information
        user.username = request.POST.get('username')
        user.email = request.POST.get('email')
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.is_active = 'is_active' in request.POST
        user.is_staff = 'is_staff' in request.POST
        
        # User profile
        profile.phone_number = request.POST.get('phone_number')
        profile.is_commercial = 'is_commercial' in request.POST
        
        # If it's a commercial account
        if profile.is_commercial:
            commercial, created = CommercialRegistration.objects.get_or_create(user=user)
            commercial.company_name = request.POST.get('company_name', '')
            commercial.business_type = request.POST.get('business_type', '')
            commercial.registration_number = request.POST.get('registration_number', '')
            commercial.tax_id = request.POST.get('tax_id', '')
            commercial.business_address = request.POST.get('business_address', '')
            commercial.is_approved = 'is_approved' in request.POST
            commercial.save()
        
        # Change password if provided
        new_password = request.POST.get('new_password')
        if new_password:
            user.set_password(new_password)
        
        user.save()
        profile.save()
        
        messages.success(request, f'User {user.username} updated successfully')
        return redirect('admin_user_list')
    
    # Get commercial data if exists
    commercial_data = None
    if profile.is_commercial:
        try:
            commercial_data = CommercialRegistration.objects.get(user=user)
        except CommercialRegistration.DoesNotExist:
            pass
    
    context = {
        'user_obj': user,
        'profile': profile,
        'commercial_data': commercial_data,
        'action': 'Edit'
    }
    
    return render(request, 'core/admin/user_edit.html', context)

@login_required
@user_passes_test(is_admin)
def admin_user_delete(request, pk):
    """Admin delete user view"""
    try:
        user = User.objects.get(pk=pk)
    except User.DoesNotExist:
        messages.error(request, 'User not found')
        return redirect('admin_user_list')
    
    # Prevent admin from deleting their own account
    if user.pk == request.user.pk:
        messages.error(request, 'You cannot delete your own admin account')
        return redirect('admin_user_list')
    
    # Prevent deleting superuser accounts if the current user is not a superuser
    if user.is_superuser and not request.user.is_superuser:
        messages.error(request, 'You do not have permission to delete superuser accounts')
        return redirect('admin_user_list')
    
    if request.method == 'POST':
        try:
            username = user.username
            user.delete()
            messages.success(request, f'User {username} deleted successfully')
        except Exception as e:
            messages.error(request, f'Error deleting user: {str(e)}')
            print(f"Error deleting user: {e}")
        return redirect('admin_user_list')
    
    return render(request, 'core/admin/user_confirm_delete.html', {'user': user})

# Admin data management views
@login_required
@user_passes_test(is_admin)
def admin_transactions(request):
    """Admin view to access all user transactions"""
    transactions = Transaction.objects.all().select_related('user', 'category').order_by('-date')
    
    # Filter functionality
    user_id = request.GET.get('user_id')
    transaction_type = request.GET.get('type')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    if user_id:
        transactions = transactions.filter(user_id=user_id)
    
    if transaction_type:
        transactions = transactions.filter(type=transaction_type)
        
    if date_from:
        transactions = transactions.filter(date__gte=date_from)
        
    if date_to:
        transactions = transactions.filter(date__lte=date_to)
    
    # Get users for the filter
    users = User.objects.all()
    
    context = {
        'transactions': transactions,
        'users': users,
        'selected_user_id': user_id,
        'selected_type': transaction_type,
        'date_from': date_from,
        'date_to': date_to,
    }
    
    return render(request, 'core/admin/transactions.html', context)

@login_required
@user_passes_test(is_admin)
def admin_transaction_edit(request, pk):
    """Admin view to edit any user's transaction"""
    transaction = get_object_or_404(Transaction, pk=pk)
    
    if request.method == 'POST':
        form = TransactionForm(request.POST, request.FILES, instance=transaction)
        if form.is_valid():
            form.save()
            messages.success(request, f'Transaction updated successfully')
            return redirect('admin_transactions')
    else:
        form = TransactionForm(instance=transaction)
    
    context = {
        'form': form,
        'transaction': transaction,
        'user': transaction.user,
    }
    
    return render(request, 'core/admin/transaction_edit.html', context)

@login_required
@user_passes_test(is_admin)
def admin_transaction_delete(request, pk):
    """Admin view to delete any user's transaction"""
    transaction = get_object_or_404(Transaction, pk=pk)
    
    if request.method == 'POST':
        username = transaction.user.username
        transaction_desc = transaction.description
        transaction.delete()
        messages.success(request, f'Transaction "{transaction_desc}" for user {username} deleted successfully')
        return redirect('admin_transactions')
    
    return render(request, 'core/admin/transaction_confirm_delete.html', {'transaction': transaction})

@login_required
@user_passes_test(is_admin)
def admin_budgets(request):
    """Admin view to access all user budgets"""
    budgets = Budget.objects.all().select_related('user', 'category')
    
    # Filter functionality
    user_id = request.GET.get('user_id')
    period = request.GET.get('period')
    
    if user_id:
        budgets = budgets.filter(user_id=user_id)
    
    if period:
        budgets = budgets.filter(period=period)
    
    # Get users for the filter
    users = User.objects.all()
    
    context = {
        'budgets': budgets,
        'users': users,
        'selected_user_id': user_id,
        'selected_period': period,
    }
    
    return render(request, 'core/admin/budgets.html', context)

@login_required
@user_passes_test(is_admin)
def admin_budget_edit(request, pk):
    """Admin view to edit any user's budget"""
    budget = get_object_or_404(Budget, pk=pk)
    
    if request.method == 'POST':
        form = BudgetForm(request.POST, instance=budget)
        if form.is_valid():
            form.save()
            messages.success(request, f'Budget updated successfully')
            return redirect('admin_budgets')
    else:
        form = BudgetForm(instance=budget)
    
    context = {
        'form': form,
        'budget': budget,
        'user': budget.user,
    }
    
    return render(request, 'core/admin/budget_edit.html', context)

@login_required
@user_passes_test(is_admin)
def admin_budget_delete(request, pk):
    """Admin view to delete any user's budget"""
    budget = get_object_or_404(Budget, pk=pk)
    
    if request.method == 'POST':
        username = budget.user.username
        category_name = budget.category.name
        budget.delete()
        messages.success(request, f'Budget for {category_name} for user {username} deleted successfully')
        return redirect('admin_budgets')
    
    return render(request, 'core/admin/budget_confirm_delete.html', {'budget': budget})

@login_required
@user_passes_test(is_admin)
def admin_goals(request):
    """Admin view to access all user financial goals"""
    goals = FinancialGoal.objects.all().select_related('user', 'category')
    
    # Filter functionality
    user_id = request.GET.get('user_id')
    
    if user_id:
        goals = goals.filter(user_id=user_id)
    
    # Get users for the filter
    users = User.objects.all()
    
    context = {
        'goals': goals,
        'users': users,
        'selected_user_id': user_id,
    }
    
    return render(request, 'core/admin/goals.html', context)

@login_required
@user_passes_test(is_admin)
def admin_goal_edit(request, pk):
    """Admin view to edit any user's financial goal"""
    goal = get_object_or_404(FinancialGoal, pk=pk)
    
    if request.method == 'POST':
        form = FinancialGoalForm(request.POST, instance=goal)
        if form.is_valid():
            form.save()
            messages.success(request, f'Goal updated successfully')
            return redirect('admin_goals')
    else:
        form = FinancialGoalForm(instance=goal)
    
    context = {
        'form': form,
        'goal': goal,
        'user': goal.user,
    }
    
    return render(request, 'core/admin/goal_edit.html', context)

@login_required
@user_passes_test(is_admin)
def admin_goal_delete(request, pk):
    """Admin view to delete any user's financial goal"""
    goal = get_object_or_404(FinancialGoal, pk=pk)
    
    if request.method == 'POST':
        username = goal.user.username
        goal_name = goal.name
        goal.delete()
        messages.success(request, f'Goal "{goal_name}" for user {username} deleted successfully')
        return redirect('admin_goals')
    
    return render(request, 'core/admin/goal_confirm_delete.html', {'goal': goal})

@login_required
@user_passes_test(is_admin)
def admin_categories(request):
    """Admin view to access all user categories"""
    categories = Category.objects.all().select_related('user')
    
    # Filter functionality
    user_id = request.GET.get('user_id')
    category_type = request.GET.get('type')
    
    if user_id:
        categories = categories.filter(user_id=user_id)
    
    if category_type:
        categories = categories.filter(type=category_type)
    
    # Get users for the filter
    users = User.objects.all()
    
    context = {
        'categories': categories,
        'users': users,
        'selected_user_id': user_id,
        'selected_type': category_type,
    }
    
    return render(request, 'core/admin/categories.html', context)

@login_required
@user_passes_test(is_admin)
def admin_category_edit(request, pk):
    """Admin view to edit any user's category"""
    category = get_object_or_404(Category, pk=pk)
    
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, f'Category updated successfully')
            return redirect('admin_categories')
    else:
        form = CategoryForm(instance=category)
    
    context = {
        'form': form,
        'category': category,
        'user': category.user,
    }
    
    return render(request, 'core/admin/category_edit.html', context)

@login_required
@user_passes_test(is_admin)
def admin_category_delete(request, pk):
    """Admin view to delete any user's category"""
    category = get_object_or_404(Category, pk=pk)
    
    # Check if this category is used in transactions, budgets, or goals
    transactions_count = Transaction.objects.filter(category=category).count()
    budgets_count = Budget.objects.filter(category=category).count()
    goals_count = FinancialGoal.objects.filter(category=category).count()
    
    if request.method == 'POST':
        if 'confirm' in request.POST:
            username = category.user.username
            category_name = category.name
            category.delete()
            messages.success(request, f'Category "{category_name}" for user {username} deleted successfully')
            return redirect('admin_categories')
    
    context = {
        'category': category,
        'transactions_count': transactions_count,
        'budgets_count': budgets_count,
        'goals_count': goals_count,
    }
    
    return render(request, 'core/admin/category_confirm_delete.html', context)

@login_required
@user_passes_test(is_admin)
def admin_reports(request):
    """Admin reports view"""
    
    # Get overall statistics
    users_count = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    inactive_users = users_count - active_users
    
    transactions_count = Transaction.objects.count()
    total_income = Transaction.objects.filter(type='income').aggregate(Sum('amount'))['amount__sum'] or 0
    total_expenses = Transaction.objects.filter(type='expense').aggregate(Sum('amount'))['amount__sum'] or 0
    net_balance = total_income - total_expenses
    
    # Get monthly statistics
    current_year = timezone.now().year
    monthly_stats = Transaction.objects.filter(
        date__year=current_year
    ).annotate(
        month=TruncMonth('date')
    ).values('month').annotate(
        income=Sum(Case(When(type='income', then='amount'), default=0, output_field=DecimalField())),
        expenses=Sum(Case(When(type='expense', then='amount'), default=0, output_field=DecimalField())),
        transaction_count=Count('id')
    ).order_by('month')
    
    # Get category distribution
    income_by_category = Transaction.objects.filter(
        type='income'
    ).values('category__name').annotate(
        total=Sum('amount')
    ).order_by('-total')
    
    expense_by_category = Transaction.objects.filter(
        type='expense'
    ).values('category__name').annotate(
        total=Sum('amount')
    ).order_by('-total')
    
    # Prepare data for charts
    months = []
    income_data = []
    expense_data = []
    net_data = []
    
    for stat in monthly_stats:
        month_name = stat['month'].strftime('%B')
        months.append(month_name)
        income_data.append(float(stat['income']))
        expense_data.append(float(stat['expenses']))
        net_data.append(float(stat['income'] - stat['expenses']))
    
    # Format category data for pie charts
    income_categories = []
    income_amounts = []
    for item in income_by_category[:5]:  # Top 5 categories
        income_categories.append(item['category__name'] or 'Uncategorized')
        income_amounts.append(float(item['total']))
    
    expense_categories = []
    expense_amounts = []
    for item in expense_by_category[:5]:  # Top 5 categories
        expense_categories.append(item['category__name'] or 'Uncategorized')
        expense_amounts.append(float(item['total']))
    
    # Get recent transactions
    recent_transactions = Transaction.objects.order_by('-date')[:10]
    
    context = {
        'users_count': users_count,
        'active_users': active_users,
        'inactive_users': inactive_users,
        'transactions_count': transactions_count,
        'total_income': total_income,
        'total_expenses': total_expenses,
        'net_balance': net_balance,
        'monthly_stats': monthly_stats,
        'income_by_category': income_by_category,
        'expense_by_category': expense_by_category,
        'recent_transactions': recent_transactions,
        
        # Chart data
        'months': json.dumps(months),
        'income_data': json.dumps(income_data),
        'expense_data': json.dumps(expense_data),
        'net_data': json.dumps(net_data),
        'income_categories': json.dumps(income_categories),
        'income_amounts': json.dumps(income_amounts),
        'expense_categories': json.dumps(expense_categories),
        'expense_amounts': json.dumps(expense_amounts),
    }
    
    return render(request, 'core/admin/reports.html', context)

@login_required
@user_passes_test(is_admin)
def admin_analyze_transactions(request):
    """Run transaction analysis and return to reports"""
    from io import StringIO
    from django.core.management import call_command
    
    # Capture command output
    output = StringIO()
    
    # Check if fix mode is requested
    fix_mode = request.GET.get('fix') == 'true'
    
    # Run the analysis command
    if fix_mode:
        call_command('analyze_transactions', '--fix', stdout=output)
    else:
        call_command('analyze_transactions', stdout=output)
    
    # Store output in session for display
    request.session['analysis_results'] = output.getvalue()
    
    # Redirect back to reports
    messages.success(request, 'Transaction analysis completed')
    return redirect('admin_reports')

def admin_login(request):
    """
    Admin authentication
    """
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Authenticate user and check if they are staff
        user = authenticate(username=username, password=password)
        
        if user is not None and user.is_staff:
            login(request, user)
            return redirect('admin_dashboard')
        else:
            messages.error(request, 'Invalid admin credentials')
            
    return render(request, 'core/admin/admin_login.html')

def custom_login(request):
    """Custom login view for regular users"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password')
    
    return render(request, 'core/login.html')

def custom_logout(request):
    """Custom logout view"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('dashboard')

# Create PDF export view
def export_financial_data_pdf(request):
    """Export user's financial data as a PDF file."""
    # Create a BytesIO buffer to receive the PDF content
    buffer = BytesIO()
    
    # Create the PDF object, using the BytesIO as its "file"
    doc = SimpleDocTemplate(buffer, pagesize=A4, 
                            rightMargin=72, leftMargin=72,
                            topMargin=72, bottomMargin=72)
    
    # Get styles
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    section_style = styles['Heading2']
    normal_style = styles['Normal']
    
    # Create a list to store our elements (paragraphs, tables, etc.)
    elements = []
    
    # Add the logo if available
    logo_path = os.path.join('static', 'img', 'logo.png')
    if os.path.exists(logo_path):
        logo = Image(logo_path, width=2*inch, height=1*inch)
        elements.append(logo)
    
    # Document title
    elements.append(Paragraph("Finance Tracker Report", title_style))
    elements.append(Spacer(1, 0.5*inch))
    
    # Add current date
    elements.append(Paragraph(f"Report generated on: {datetime.now().strftime('%B %d, %Y')}", normal_style))
    if request.user.is_authenticated:
        elements.append(Paragraph(f"User: {request.user.username}", normal_style))
    else:
        elements.append(Paragraph("User: Anonymous (Demo Mode)", normal_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # Get data based on authentication status
    if request.user.is_authenticated:
        # Transactions
        transactions = Transaction.objects.filter(user=request.user).order_by('-date')[:50]  # Limit to recent 50
        
        # Budgets
        budgets = Budget.objects.filter(user=request.user)
        
        # Goals
        goals = FinancialGoal.objects.filter(user=request.user)
        
        # Financial Overview
        income = Transaction.objects.filter(user=request.user, type='income').aggregate(total=Sum('amount'))['total'] or 0
        expenses = Transaction.objects.filter(user=request.user, type='expense').aggregate(total=Sum('amount'))['total'] or 0
        net = income - expenses
    else:
        # For anonymous users, create sample data similar to views
        # Sample transactions
        try:
            # Create sample transactions
            sample_transactions = [
                SampleTransaction(id=1, description="Salary", amount=3000, date=timezone.now() - timedelta(days=2), 
                                  transaction_type="income", category="Salary"),
                SampleTransaction(id=2, description="Rent", amount=1200, date=timezone.now() - timedelta(days=5), 
                                  transaction_type="expense", category="Housing"),
                SampleTransaction(id=3, description="Groceries", amount=150, date=timezone.now() - timedelta(days=3), 
                                  transaction_type="expense", category="Food"),
                SampleTransaction(id=4, description="Freelance Work", amount=500, date=timezone.now() - timedelta(days=1), 
                                  transaction_type="income", category="Side Income"),
                SampleTransaction(id=5, description="Restaurant", amount=75, date=timezone.now() - timedelta(days=4), 
                                  transaction_type="expense", category="Food")
            ]
            transactions = sample_transactions
        except Exception:
            # Fallback to dictionaries if there's any issue
            transactions = [
                {"id": 1, "description": "Salary", "amount": 3000, "date": timezone.now() - timedelta(days=2), 
                 "type": "income", "category": "Salary"},
                {"id": 2, "description": "Rent", "amount": 1200, "date": timezone.now() - timedelta(days=5), 
                 "type": "expense", "category": "Housing"},
                {"id": 3, "description": "Groceries", "amount": 150, "date": timezone.now() - timedelta(days=3), 
                 "type": "expense", "category": "Food"}
            ]
        
        # Sample budgets
        budgets = [
            {"category": "Housing", "amount": 1500, "period": "monthly"},
            {"category": "Food", "amount": 400, "period": "monthly"},
            {"category": "Transportation", "amount": 200, "period": "monthly"},
            {"category": "Entertainment", "amount": 150, "period": "monthly"}
        ]
        
        # Sample goals
        goals = [
            {"name": "Emergency Fund", "target_amount": 10000, "current_amount": 5000, "deadline": timezone.now() + timedelta(days=180)},
            {"name": "Vacation", "target_amount": 3000, "current_amount": 1200, "deadline": timezone.now() + timedelta(days=120)},
            {"name": "New Computer", "target_amount": 2000, "current_amount": 800, "deadline": timezone.now() + timedelta(days=90)}
        ]
        
        # Sample overview
        income = 3500
        expenses = 1425
        net = income - expenses
    
    # Add financial overview section
    elements.append(Paragraph("Financial Overview", section_style))
    elements.append(Spacer(1, 0.1*inch))
    
    # Create a table for financial overview
    overview_data = [
        ["Total Income", "Total Expenses", "Net Balance"],
        [f"Rs {income:.2f}", f"Rs {expenses:.2f}", f"Rs {net:.2f}"]
    ]
    overview_table = Table(overview_data, colWidths=[doc.width/3.0]*3)
    overview_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (0, 1), colors.lightgreen),
        ('BACKGROUND', (1, 1), (1, 1), colors.lightcoral),
        ('BACKGROUND', (2, 1), (2, 1), colors.lightblue),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(overview_table)
    elements.append(Spacer(1, 0.2*inch))
    
    # Add transaction section
    elements.append(Paragraph("Recent Transactions", section_style))
    elements.append(Spacer(1, 0.1*inch))
    
    if transactions:
        # Create a table for transactions
        transaction_data = [["Date", "Description", "Type", "Category", "Amount"]]
        
        for tx in transactions[:15]:  # Limit to 15 transactions for space
            if hasattr(tx, 'date') and callable(getattr(tx, 'date', None)):
                # If date is a method (for model instances)
                date = tx.date() if callable(tx.date) else tx.date
            else:
                # If date is an attribute
                date = tx.date if hasattr(tx, 'date') else (tx.get('date', 'N/A'))
            
            if isinstance(date, datetime):
                date_str = date.strftime('%Y-%m-%d')
            else:
                date_str = str(date)
            
            description = tx.description if hasattr(tx, 'description') else tx.get('description', 'N/A')
            tx_type = tx.transaction_type if hasattr(tx, 'transaction_type') else (
                tx.type if hasattr(tx, 'type') else tx.get('type', 'N/A'))
            category = tx.category if hasattr(tx, 'category') else tx.get('category', 'N/A')
            if hasattr(category, 'name'):  # If category is an object
                category = category.name
            amount = tx.amount if hasattr(tx, 'amount') else tx.get('amount', 0)
            
            transaction_data.append([
                date_str,
                description,
                tx_type.capitalize() if isinstance(tx_type, str) else 'N/A',
                category,
                f"Rs {float(amount):.2f}"
            ])
        
        tx_table = Table(transaction_data, colWidths=[doc.width/5.0]*5)
        tx_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        elements.append(tx_table)
    else:
        elements.append(Paragraph("No transactions found.", normal_style))
    
    elements.append(Spacer(1, 0.2*inch))
    
    # Add budget section
    elements.append(Paragraph("Budget Information", section_style))
    elements.append(Spacer(1, 0.1*inch))
    
    if budgets:
        # Create a table for budgets
        budget_data = [["Category", "Amount", "Period"]]
        
        for budget in budgets:
            category = budget.category.name if hasattr(budget, 'category') and hasattr(budget.category, 'name') else (
                budget['category'] if isinstance(budget, dict) else str(budget.category) if hasattr(budget, 'category') else 'N/A')
            amount = budget.amount if hasattr(budget, 'amount') else budget.get('amount', 0)
            period = budget.period if hasattr(budget, 'period') else budget.get('period', 'monthly')
            
            budget_data.append([
                category,
                f"Rs {float(amount):.2f}",
                period.capitalize() if isinstance(period, str) else 'Monthly'
            ])
        
        budget_table = Table(budget_data, colWidths=[doc.width/3.0]*3)
        budget_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        elements.append(budget_table)
    else:
        elements.append(Paragraph("No budget information found.", normal_style))
    
    elements.append(Spacer(1, 0.2*inch))
    
    # Add goals section
    elements.append(Paragraph("Financial Goals", section_style))
    elements.append(Spacer(1, 0.1*inch))
    
    if goals:
        # Create a table for goals
        goal_data = [["Goal", "Target", "Current", "Progress", "Deadline"]]
        
        for goal in goals:
            name = goal.name if hasattr(goal, 'name') else goal.get('name', 'N/A')
            target = goal.target_amount if hasattr(goal, 'target_amount') else goal.get('target_amount', 0)
            current = goal.current_amount if hasattr(goal, 'current_amount') else goal.get('current_amount', 0)
            
            # Calculate progress percentage
            if float(target) > 0:
                progress = (float(current) / float(target)) * 100
            else:
                progress = 0
                
            deadline = goal.deadline if hasattr(goal, 'deadline') else goal.get('deadline', 'N/A')
            if isinstance(deadline, datetime):
                deadline_str = deadline.strftime('%Y-%m-%d')
            else:
                deadline_str = str(deadline)
            
            goal_data.append([
                name,
                f"Rs {float(target):.2f}",
                f"Rs {float(current):.2f}",
                f"{progress:.1f}%",
                deadline_str
            ])
        
        goal_table = Table(goal_data, colWidths=[doc.width/5.0]*5)
        goal_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        elements.append(goal_table)
    else:
        elements.append(Paragraph("No financial goals found.", normal_style))
    
    # Add disclaimer
    elements.append(Spacer(1, 0.3*inch))
    elements.append(Paragraph("This report contains financial information as of the generation date. Past data may not reflect current status.", 
                            ParagraphStyle("Disclaimer", 
                                        parent=normal_style,
                                        fontSize=8,
                                        textColor=colors.gray)))
    
    # Build the PDF
    doc.build(elements)
    
    # FileResponse sets the Content-Disposition header so that browsers
    # present the option to save the file.
    buffer.seek(0)
    
    # Create the HttpResponse with PDF content
    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
    filename = f"finance_tracker_report_{timestamp}.pdf"
    
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response

def verify_email(request, token):
    """
    View to verify email address using the token sent via email
    """
    try:
        verification = EmailVerification.objects.get(token=token)
        user = verification.user
        
        # Check if already verified
        if verification.is_verified:
            messages.info(request, 'Your email has already been verified. Please log in.')
            return redirect('login')
            
        # Check if token expired
        if verification.is_expired:
            messages.error(request, 'The verification link has expired. Please request a new one.')
            # Redirect to resend verification page
            return redirect('resend_verification_email')
        
        # Mark as verified and activate user
        verification.is_verified = True
        verification.save()
        
        user.is_active = True
        user.save()
        
        # Render the success page
        return render(request, 'core/verification_success.html')
        
    except EmailVerification.DoesNotExist:
        messages.error(request, 'Invalid verification link. Please check your email or register again.')
        return redirect('register')

def resend_verification_email(request):
    """
    View to resend verification email
    """
    if request.method == 'POST':
        email = request.POST.get('email')
        
        try:
            user = User.objects.get(email=email)
            
            # Check if user is already active
            if user.is_active:
                messages.info(request, 'Your account is already verified. Please log in.')
                return redirect('login')
            
            # Get or create email verification
            email_verification, created = EmailVerification.objects.get_or_create(user=user)
            
            # If not created, regenerate the token
            if not created:
                email_verification.token = uuid.uuid4()
                email_verification.created_at = timezone.now()
                email_verification.is_verified = False
                email_verification.save()
            
            # Build verification URL
            current_site = get_current_site(request)
            verification_url = f"http://{current_site.domain}/verify-email/{email_verification.token}/"
            
            # Send verification email
            subject = "Verify your Finance Tracker account"
            message = f"""
            Hello {user.username},
            
            You have requested a new verification link. To verify your email address, please click on the link below:
            
            {verification_url}
            
            This link will expire in 72 hours.
            
            If you did not register for Finance Tracker, please ignore this email.
            
            Best regards,
            The Finance Tracker Team
            """
            
            from_email = settings.EMAIL_HOST_USER
            recipient_list = [user.email]
            
            send_mail(subject, message, from_email, recipient_list)
            
            messages.success(request, 'A new verification email has been sent. Please check your inbox.')
            return redirect('login')
            
        except User.DoesNotExist:
            messages.error(request, 'No account found with this email address.')
    
    # Render the form
    return render(request, 'core/resend_verification.html')

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            # Create user but don't save password yet
            user = form.save(commit=False)
            user.is_active = False  # Deactivate until email is verified
            user.save()
            
            # Set the password after saving to properly hash it
            user.set_password(form.cleaned_data['password1'])
            user.save()
            
            # Create user profile
            UserProfile.objects.create(user=user)
            
            # Create default categories
            create_default_categories(user)
            
            # Create email verification token and URL
            current_site = get_current_site(request)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = account_activation_token.make_token(user)
            
            verification_url = f"http://{current_site.domain}{reverse('activate_account', kwargs={'uidb64': uid, 'token': token})}"
            
            # Send verification email
            success = send_verification_email(user, verification_url)
            
            if success:
                messages.success(request, 'Your account has been created! Please check your email to verify your account.')
            else:
                messages.warning(request, 'Your account has been created but we could not send the verification email. Please contact support.')
                
            return redirect('login')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'core/register.html', {'form': form})

def activate_account(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        
        # Log the user in
        login(request, user)
        
        messages.success(request, 'Your account has been verified and activated successfully!')
        return redirect('dashboard')
    else:
        messages.error(request, 'The activation link is invalid or has expired.')
        return redirect('login')

def test_email_view(request):
    """View to test the email configuration"""
    if request.method == 'POST':
        recipient_email = request.POST.get('email')
        success, message = test_email_config(recipient_email)
        
        if success:
            messages.success(request, message)
        else:
            messages.error(request, message)
        
        return redirect('test_email')
    
    # If user is staff, allow testing with any email
    is_staff = request.user.is_authenticated and request.user.is_staff
    
    return render(request, 'core/test_email.html', {
        'is_staff': is_staff,
        'user_email': request.user.email if request.user.is_authenticated else ''
    })
