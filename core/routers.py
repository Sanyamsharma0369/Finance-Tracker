from asgiref.sync import sync_to_async

class UserSpecificRouter:
    """
    A router to control all database operations on models 
    for handling user-specific data isolation.
    """
    user_models = ['Transaction', 'Budget', 'Category', 'FinancialGoal', 'Notification', 'Settings']

    def db_for_read(self, model, **hints):
        """
        All reads go to the default database.
        """
        return 'default'

    def db_for_write(self, model, **hints):
        """
        All writes go to the default database.
        """
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        """
        Only allow relations between objects of the same user for user-specific models.
        """
        if obj1._meta.model_name in self.user_models and obj2._meta.model_name in self.user_models:
            # Check if both objects belong to the same user
            try:
                user1 = getattr(obj1, 'user', None)
                user2 = getattr(obj2, 'user', None)
                
                # If both have user attributes and they don't match, disallow the relation
                if user1 and user2 and user1.id != user2.id:
                    return False
            except AttributeError:
                pass
                
        # For all other models, allow relations
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Make sure all models use the default database.
        """
        return True


class AsyncUserSpecificRouter(UserSpecificRouter):
    """
    An asynchronous version of the UserSpecificRouter for use with async views.
    This router supports the same functionality but is compatible with Django's async database operations.
    """
    
    async def db_for_read(self, model, **hints):
        """
        Async version - all reads go to the default database.
        """
        return 'default'  # Simply return default directly for async read
        
    async def db_for_write(self, model, **hints):
        """
        Async version - all writes go to the default database.
        """
        return 'default'  # Simply return default directly for async write
        
    async def allow_relation(self, obj1, obj2, **hints):
        """
        Async version - check relations between user-specific models.
        """
        # Use sync_to_async to run the parent class's method
        parent_method = sync_to_async(super().allow_relation)
        return await parent_method(obj1, obj2, **hints)
        
    async def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Async version - allow migrations.
        """
        return True  # Simply return True directly for async migrate 