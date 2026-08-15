from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission

User = get_user_model()

class CentralAdminPermissionsTest(TestCase):
    def setUp(self):
        # Create some default permissions if they don't exist in the test DB
        from django.contrib.contenttypes.models import ContentType
        content_type, _ = ContentType.objects.get_or_create(app_label='accounts', model='user')
        
        for codename in ['view_central_dashboard', 'manage_all_users', 'audit_all_tenders', 'view_system_reports']:
            Permission.objects.get_or_create(
                codename=codename,
                content_type=content_type,
                defaults={'name': f"Can {codename.replace('_', ' ')}"}
            )

    def test_central_admin_receives_permissions(self):
        """Test that a central_admin receives all necessary permissions upon creation."""
        user = User.objects.create_user(username='admin_test', email='admin@test.com', password='testpassword', role='central_admin')
        
        self.assertTrue(user.has_perm('accounts.view_central_dashboard'))
        self.assertTrue(user.has_perm('accounts.manage_all_users'))
        self.assertTrue(user.has_perm('accounts.audit_all_tenders'))
        self.assertTrue(user.has_perm('accounts.view_system_reports'))
        
    def test_supplier_does_not_receive_permissions(self):
        """Test that a supplier user does NOT receive central_admin permissions."""
        user = User.objects.create_user(username='supplier_test', email='sup@test.com', password='testpassword', role='supplier')
        
        self.assertFalse(user.has_perm('accounts.view_central_dashboard'))
        self.assertFalse(user.has_perm('accounts.manage_all_users'))
        self.assertFalse(user.has_perm('accounts.audit_all_tenders'))

    def test_role_change_assigns_permissions(self):
        """Test that changing an existing user's role to central_admin assigns permissions."""
        user = User.objects.create_user(username='change_test', email='change@test.com', password='testpassword', role='authority')
        self.assertFalse(user.has_perm('accounts.view_central_dashboard'))
        
        user.role = 'central_admin'
        user.save()
        
        # We must re-fetch the user to clear the permission cache
        user = User.objects.get(pk=user.pk)
        self.assertTrue(user.has_perm('accounts.view_central_dashboard'))
        self.assertTrue(user.has_perm('accounts.manage_all_users'))
