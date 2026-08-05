from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from apps.accounts.models import User

# Create Group
group, created = Group.objects.get_or_create(name='Central Admins')

# Get the content type for User model where custom permissions are defined
user_ct = ContentType.objects.get_for_model(User)

# Fetch the specific permissions
perms = ['view_central_dashboard', 'manage_all_users', 'audit_all_tenders', 'view_system_reports']
permissions = Permission.objects.filter(content_type=user_ct, codename__in=perms)

# Assign permissions to the group
group.permissions.set(permissions)
print("Central Admins group configured successfully with permissions:")
for p in permissions:
    print(f" - {p.codename}")
