from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission

User = get_user_model()

@override_settings(AXES_ENABLED=False)
class CentralAdminPermissionsViewsTest(TestCase):
    def setUp(self):
        # Create permissions
        from django.contrib.contenttypes.models import ContentType
        content_type, _ = ContentType.objects.get_or_create(app_label='accounts', model='user')
        
        for codename in ['view_central_dashboard', 'manage_all_users', 'audit_all_tenders', 'view_system_reports']:
            Permission.objects.get_or_create(
                codename=codename,
                content_type=content_type,
                defaults={'name': f"Can {codename}"}
            )
            
        self.dashboard_url = reverse('dashboard:regulator')
        self.users_url = reverse('dashboard:regulator_users')
        self.audit_url = reverse('dashboard:regulator_audit')
        self.reports_url = reverse('dashboard:regulator_audit_log')
        
        self.client = Client()
        
        # 1. Normal user without perms
        self.normal_user = User.objects.create_user(username='normal', password='pwd', role='supplier')
        
        # 2. Central Admin (should have perms via signals)
        self.central_admin = User.objects.create_user(username='central', password='pwd', role='central_admin')
        
        # 3. Supplier
        self.supplier = User.objects.create_user(username='supplier', password='pwd', role='supplier')
        
        # 4. Authority
        self.authority = User.objects.create_user(username='auth', password='pwd', role='authority')
        
        # 5. Staff only
        self.staff_user = User.objects.create_user(username='staff', password='pwd', is_staff=True)
        
        # 6. Superuser only
        self.super_user = User.objects.create_superuser(username='super', password='pwd', email='super@s.com')
        
        # 7. Inactive user
        self.inactive_user = User.objects.create_user(username='inactive', password='pwd', role='central_admin', is_active=False)
        
        # 8. Central Admin WITHOUT perms (we manually strip them to ensure code checks perm not role)
        self.stripped_admin = User.objects.create_user(username='stripped', password='pwd', role='central_admin')
        self.stripped_admin.user_permissions.clear()
        
    def test_anonymous_user(self):
        urls = [self.dashboard_url, self.users_url, self.audit_url, self.reports_url]
        for url in urls:
            response = self.client.get(url)
            self.assertRedirects(response, f'/accounts/login/?next={url}')
            
    def check_forbidden_or_redirect(self, client):
        # Class-Based View with PermissionRequiredMixin returns 403 for authenticated users (dashboard)
        # Function-Based View with raise_exception=True returns 403 (users, audit)
        # Function-Based View WITHOUT raise_exception=True redirects to login (302) (reports)
        
        response_dash = client.get(self.dashboard_url)
        self.assertEqual(response_dash.status_code, 403)
        
        response_users = client.get(self.users_url)
        self.assertEqual(response_users.status_code, 403)
        
        response_audit = client.get(self.audit_url)
        self.assertEqual(response_audit.status_code, 403)
        
        response_reports = client.get(self.reports_url)
        self.assertRedirects(response_reports, f'/accounts/login/?next={self.reports_url}')

    def test_normal_user_without_permissions(self):
        self.client.force_login(self.normal_user)
        self.check_forbidden_or_redirect(self.client)
            
    def test_supplier_and_authority(self):
        self.client.force_login(self.supplier)
        self.check_forbidden_or_redirect(self.client)
        
        self.client.force_login(self.authority)
        self.check_forbidden_or_redirect(self.client)
        
    def test_staff_user_only(self):
        self.client.force_login(self.staff_user)
        self.check_forbidden_or_redirect(self.client)
        
    def test_superuser_only(self):
        self.client.force_login(self.super_user)
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard/regulator_dashboard.html')
        
    def test_inactive_user(self):
        self.client.login(username='inactive', password='pwd')
        # Login should fail or redirect
        response = self.client.get(self.dashboard_url)
        # Because inactive users can't log in successfully via Django's default backend
        self.assertRedirects(response, f'/accounts/login/?next={self.dashboard_url}')
        
    def test_stripped_admin_without_permissions(self):
        from django.db.models.signals import post_save
        from apps.accounts.signals import assign_central_admin_permissions
        
        # Disconnect signal so login (which updates last_login and triggers post_save) doesn't self-heal
        post_save.disconnect(assign_central_admin_permissions, sender=User)
        
        try:
            stripped = User.objects.get(pk=self.stripped_admin.pk)
            self.client.force_login(stripped)
            self.check_forbidden_or_redirect(self.client)
        finally:
            post_save.connect(assign_central_admin_permissions, sender=User)
        
    def test_central_admin_with_permissions(self):
        self.client.force_login(self.central_admin)
        
        response_dash = self.client.get(self.dashboard_url)
        self.assertEqual(response_dash.status_code, 200)
        self.assertTemplateUsed(response_dash, 'dashboard/regulator_dashboard.html')
        
        response_users = self.client.get(self.users_url)
        self.assertEqual(response_users.status_code, 200)
        self.assertTemplateUsed(response_users, 'dashboard/regulator_users.html')
        
        response_audit = self.client.get(self.audit_url)
        self.assertEqual(response_audit.status_code, 200)
        self.assertTemplateUsed(response_audit, 'dashboard/regulator_audit.html')
        
        response_log = self.client.get(self.reports_url)
        self.assertEqual(response_log.status_code, 200)
        self.assertTemplateUsed(response_log, 'dashboard/regulator_audit_log.html')
