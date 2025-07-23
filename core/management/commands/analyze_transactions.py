from django.core.management.base import BaseCommand
from django.db.models import Count, Sum, Q, Case, When, DecimalField
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

from core.models import Transaction, Category


class Command(BaseCommand):
    help = 'Analyzes and optionally repairs transaction data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Fix issues found in transactions',
        )
        parser.add_argument(
            '--user',
            type=str,
            help='Username to analyze transactions for',
        )
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days to analyze',
        )

    def handle(self, *args, **options):
        fix_mode = options['fix']
        days = options['days']
        username = options.get('user')

        self.stdout.write(self.style.SUCCESS(f"Starting transaction analysis{' and repair' if fix_mode else ''}"))
        
        # Set time period for analysis
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Filter transactions
        transactions = Transaction.objects.filter(date__gte=start_date)
        
        if username:
            try:
                user = User.objects.get(username=username)
                transactions = transactions.filter(user=user)
                self.stdout.write(f"Analyzing transactions for user: {username}")
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"User {username} not found"))
                return
        
        # Basic stats
        total_count = transactions.count()
        income_count = transactions.filter(type='income').count()
        expense_count = transactions.filter(type='expense').count()
        
        self.stdout.write(f"Found {total_count} transactions ({income_count} income, {expense_count} expense)")
        
        # Check for transactions without categories
        no_category = transactions.filter(category__isnull=True)
        if no_category.exists():
            self.stdout.write(self.style.WARNING(f"Found {no_category.count()} transactions without categories"))
            
            if fix_mode:
                self._fix_missing_categories(no_category)
        
        # Check for invalid amounts (zero or negative)
        invalid_amounts = transactions.filter(Q(amount__lte=0))
        if invalid_amounts.exists():
            self.stdout.write(self.style.WARNING(f"Found {invalid_amounts.count()} transactions with invalid amounts"))
            
            if fix_mode:
                self._fix_invalid_amounts(invalid_amounts)
        
        # Check for future-dated transactions
        future_transactions = transactions.filter(date__gt=timezone.now().date())
        if future_transactions.exists():
            self.stdout.write(self.style.WARNING(f"Found {future_transactions.count()} transactions with future dates"))
            
            if fix_mode:
                self._fix_future_dates(future_transactions)
        
        # Transaction summary by month
        self._show_monthly_summary(transactions)
        
        # Category distribution
        self._show_category_distribution(transactions)
        
        if fix_mode:
            self.stdout.write(self.style.SUCCESS("Repair operations completed"))
        else:
            self.stdout.write(self.style.SUCCESS("Analysis completed (run with --fix to repair issues)"))

    def _fix_missing_categories(self, transactions):
        """Assign default categories to transactions with missing categories"""
        income_cat = None
        expense_cat = None
        
        for tx in transactions:
            # Get or create appropriate category for the user
            if tx.type == 'income':
                if not income_cat or income_cat.user_id != tx.user_id:
                    income_cat, created = Category.objects.get_or_create(
                        user=tx.user,
                        name='Other Income',
                        defaults={'type': 'income', 'description': 'Auto-assigned income category'}
                    )
                tx.category = income_cat
            else:
                if not expense_cat or expense_cat.user_id != tx.user_id:
                    expense_cat, created = Category.objects.get_or_create(
                        user=tx.user,
                        name='Other Expenses',
                        defaults={'type': 'expense', 'description': 'Auto-assigned expense category'}
                    )
                tx.category = expense_cat
            
            tx.save()
            
        self.stdout.write(self.style.SUCCESS(f"Assigned categories to {transactions.count()} transactions"))

    def _fix_invalid_amounts(self, transactions):
        """Fix transactions with invalid amounts"""
        # For negative amounts, we'll flip the sign and change the type
        flipped_count = 0
        removed_count = 0
        
        for tx in transactions:
            if tx.amount < 0:
                # Negative amount - flip the sign and invert the type
                tx.amount = abs(tx.amount)
                tx.type = 'expense' if tx.type == 'income' else 'income'
                # Make sure category matches the new type
                if tx.category and tx.category.type != tx.type:
                    # Find a matching category or create one
                    matching_categories = Category.objects.filter(
                        user=tx.user, 
                        type=tx.type
                    ).first()
                    
                    if matching_categories:
                        tx.category = matching_categories
                    else:
                        # Create a new category
                        category_name = 'Other Income' if tx.type == 'income' else 'Other Expenses'
                        tx.category = Category.objects.create(
                            user=tx.user,
                            name=category_name,
                            type=tx.type,
                            description=f"Auto-created {tx.type} category"
                        )
                        
                tx.save()
                flipped_count += 1
            elif tx.amount == 0:
                # Zero amount - delete the transaction
                tx.delete()
                removed_count += 1
        
        self.stdout.write(self.style.SUCCESS(
            f"Fixed {flipped_count} transactions with negative amounts and removed {removed_count} zero-amount transactions"
        ))

    def _fix_future_dates(self, transactions):
        """Fix transactions with future dates"""
        today = timezone.now().date()
        updated_count = 0
        
        for tx in transactions:
            tx.date = today
            tx.save()
            updated_count += 1
            
        self.stdout.write(self.style.SUCCESS(f"Updated {updated_count} transactions with future dates to today's date"))

    def _show_monthly_summary(self, transactions):
        """Show monthly summary of transactions"""
        self.stdout.write("\nMonthly Summary:")
        
        # Get the first day of the current month
        current_month = timezone.now().replace(day=1)
        
        for i in range(3):
            month_start = current_month - timedelta(days=30*i)
            month_end = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(seconds=1)
            month_name = month_start.strftime('%b %Y')
            
            month_transactions = transactions.filter(date__range=(month_start, month_end))
            
            income = month_transactions.filter(type='income').aggregate(sum=Sum('amount'))['sum'] or 0
            expenses = month_transactions.filter(type='expense').aggregate(sum=Sum('amount'))['sum'] or 0
            net = income - expenses
            
            self.stdout.write(f"  {month_name}: Income: ${income:.2f}, Expenses: ${expenses:.2f}, Net: ${net:.2f}")

    def _show_category_distribution(self, transactions):
        """Show distribution of transactions by category"""
        self.stdout.write("\nCategory Distribution:")
        
        category_stats = transactions.values('category__name', 'type').annotate(
            count=Count('id'),
            total=Sum('amount')
        ).order_by('-total')
        
        for stat in category_stats:
            category_name = stat['category__name'] or 'No Category'
            self.stdout.write(f"  {category_name} ({stat['type']}): {stat['count']} transactions, ${stat['total']:.2f}") 