from django.test import TestCase, override_settings
from django.urls import reverse
from apps.accounts.models import User
from apps.procurement.models import Tender

@override_settings(AXES_ENABLED=False)
class AuthorityPermissionsTest(TestCase):
    def setUp(self):
        # Create an authority user
        self.authority_user = User.objects.create_user(
            username='auth1',
            email='auth1@example.com',
            password='password123',
            role='authority'
        )
        
        # Create a supplier user
        self.supplier_user = User.objects.create_user(
            username='supp1',
            email='supp1@example.com',
            password='password123',
            role='supplier'
        )
        
        self.dashboard_url = reverse('dashboard:authority')
        self.reports_url = reverse('dashboard:authority_reports')

    def test_authority_has_permissions_via_signal(self):
        """Test that the signal properly assigns permissions to authority users."""
        self.assertTrue(self.authority_user.has_perm('procurement.view_tender'))
        self.assertTrue(self.authority_user.has_perm('procurement.add_tender'))
        self.assertFalse(self.supplier_user.has_perm('procurement.view_tender'))

    def test_authority_can_access_dashboard(self):
        """Test that an authority can access the authority dashboard."""
        self.client.force_login(self.authority_user)
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 200)

    def test_supplier_cannot_access_dashboard(self):
        """Test that a supplier gets a 403 Forbidden when trying to access authority dashboard."""
        self.client.force_login(self.supplier_user)
        response = self.client.get(self.dashboard_url)
        # PermissionRequiredMixin/decorator raises PermissionDenied (403) for authenticated users without permission
        self.assertEqual(response.status_code, 403)
        
    def test_anonymous_redirected_to_login(self):
        """Test that an anonymous user is redirected to the login page."""
        response = self.client.get(self.dashboard_url)
        # 302 redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse('accounts:login')))
