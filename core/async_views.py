from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from asgiref.sync import sync_to_async
from django.utils import timezone
import json
from datetime import datetime, timedelta

from .models import Transaction, Category
from .utils import async_validate_user_data_access

@require_http_methods(["GET"])
async def async_transaction_list(request):
    if request.user.is_authenticated:
        get_transactions = sync_to_async(lambda: list(Transaction.objects.filter(
            user=request.user
        ).select_related('category').order_by('-date')[:50]))
        
        transactions = await get_transactions()
        
        formatted_transactions = []
        for transaction in transactions:
            formatted_transactions.append({
                'id': transaction.id,
                'description': transaction.description,
                'amount': float(transaction.amount),
                'date': transaction.date.strftime('%Y-%m-%d'),
                'type': transaction.type,
                'category': transaction.category.name if transaction.category else None,
                'category_id': transaction.category.id if transaction.category else None,
            })
    else:
        sample_data = [
            {
                'id': 1,
                'description': 'Salary',
                'amount': 3000.00,
                'date': (timezone.now() - timedelta(days=2)).strftime('%Y-%m-%d'),
                'type': 'income',
                'category': 'Income',
                'category_id': 1,
            },
            {
                'id': 2,
                'description': 'Groceries',
                'amount': 150.75,
                'date': (timezone.now() - timedelta(days=1)).strftime('%Y-%m-%d'),
                'type': 'expense',
                'category': 'Food',
                'category_id': 2,
            },
            {
                'id': 3,
                'description': 'Utilities',
                'amount': 95.20,
                'date': timezone.now().strftime('%Y-%m-%d'),
                'type': 'expense',
                'category': 'Housing',
                'category_id': 3,
            }
        ]
        formatted_transactions = sample_data
    
    return JsonResponse({
        'transactions': formatted_transactions,
        'count': len(formatted_transactions),
        'timestamp': timezone.now().isoformat()
    })

@require_http_methods(["GET"])
async def async_transaction_detail(request, pk):
    if request.user.is_authenticated:
        try:
            transaction = await async_validate_user_data_access(
                model_class=Transaction,
                object_id=pk,
                user=request.user
            )
            
            get_category_name = sync_to_async(lambda: transaction.category.name if transaction.category else None)
            category_name = await get_category_name()
            
            transaction_data = {
                'id': transaction.id,
                'description': transaction.description,
                'amount': float(transaction.amount),
                'date': transaction.date.strftime('%Y-%m-%d'),
                'type': transaction.type,
                'category': category_name,
                'category_id': transaction.category.id if transaction.category else None,
            }
            
            return JsonResponse({
                'transaction': transaction_data,
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            return JsonResponse({
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }, status=404)
    else:
        if pk in [1, 2, 3]:
            sample_data = {
                1: {
                    'id': 1,
                    'description': 'Salary',
                    'amount': 3000.00,
                    'date': (timezone.now() - timedelta(days=2)).strftime('%Y-%m-%d'),
                    'type': 'income',
                    'category': 'Income',
                    'category_id': 1,
                },
                2: {
                    'id': 2,
                    'description': 'Groceries',
                    'amount': 150.75,
                    'date': (timezone.now() - timedelta(days=1)).strftime('%Y-%m-%d'),
                    'type': 'expense',
                    'category': 'Food',
                    'category_id': 2,
                },
                3: {
                    'id': 3,
                    'description': 'Utilities',
                    'amount': 95.20,
                    'date': timezone.now().strftime('%Y-%m-%d'),
                    'type': 'expense',
                    'category': 'Housing',
                    'category_id': 3,
                }
            }
            
            return JsonResponse({
                'transaction': sample_data[pk],
                'timestamp': timezone.now().isoformat()
            })
        else:
            return JsonResponse({
                'error': 'Transaction not found',
                'timestamp': timezone.now().isoformat()
            }, status=404) 