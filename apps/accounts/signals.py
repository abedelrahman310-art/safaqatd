from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission

User = get_user_model()

@receiver(post_save, sender=User)
def assign_central_admin_permissions(sender, instance, created, **kwargs):
    """
    Automatically assign required permissions to central_admin users.
    This replaces the need to manually assign them in Django Admin
    and completely avoids using is_superuser.
    """
    if instance.role == 'central_admin':
        # List of permissions required for central_admin
        required_permissions = [
            'view_central_dashboard',
            'manage_all_users',
            'audit_all_tenders',
            'view_system_reports',
        ]
        
        # We need to fetch the Permission objects
        permissions_to_add = Permission.objects.filter(
            codename__in=required_permissions,
            content_type__app_label='accounts'
        )
        
        if permissions_to_add.exists():
            # Add permissions without removing existing ones
            instance.user_permissions.add(*permissions_to_add)

@receiver(post_save, sender=User)
def assign_authority_permissions(sender, instance, created, **kwargs):
    """
    Automatically assign required permissions to authority users.
    """
    if instance.role == 'authority':
        # List of permissions required for authority
        required_permissions = [
            'view_tender',
            'add_tender',
            'change_tender',
        ]
        
        # We need to fetch the Permission objects from procurement app
        permissions_to_add = Permission.objects.filter(
            codename__in=required_permissions,
            content_type__app_label='procurement'
        )
        
        if permissions_to_add.exists():
            instance.user_permissions.add(*permissions_to_add)
