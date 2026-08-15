from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from apps.accounts.models import User


class Command(BaseCommand):
    help = 'إعداد مجموعة الإدارة المركزية وتعيين الصلاحيات اللازمة'

    def handle(self, *args, **options):
        # Create Group
        group, created = Group.objects.get_or_create(name='Central Admins')
        status = 'Created' if created else 'Already exists'
        self.stdout.write(f'Group Central Admins: {status}')

        # Get the content type for User model where custom permissions are defined
        user_ct = ContentType.objects.get_for_model(User)

        # Fetch the specific permissions
        perm_codenames = [
            'view_central_dashboard',
            'manage_all_users',
            'audit_all_tenders',
            'view_system_reports',
        ]
        permissions = Permission.objects.filter(
            content_type=user_ct,
            codename__in=perm_codenames,
        )

        if not permissions.exists():
            self.stdout.write(self.style.WARNING(
                'Warning: Custom permissions not found. '
                'Make sure to run migrate first.'
            ))
            return

        # Assign permissions to the group
        group.permissions.set(permissions)
        self.stdout.write(self.style.SUCCESS(
            'Central Admins group configured successfully with permissions:'
        ))
        for p in permissions:
            self.stdout.write(f'  - {p.codename}')
