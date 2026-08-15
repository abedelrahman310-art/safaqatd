from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.procurement.models import Tender
from django.contrib.auth.models import Permission

User = get_user_model()

class AuthorityTendersSecurityTest(TestCase):
    def setUp(self):
        self.client = Client()
        
        # Create Authority User with permissions
        self.authority = User.objects.create_user(
            username='auth_test',
            email='auth@test.com',
            password='password123',
            role='authority'
        )
        
        view_perm = Permission.objects.get(codename='view_tender')
        add_perm = Permission.objects.get(codename='add_tender')
        change_perm = Permission.objects.get(codename='change_tender')
        delete_perm = Permission.objects.get(codename='delete_tender')
        
        self.authority.user_permissions.add(view_perm, add_perm, change_perm, delete_perm)
        
        # Create another Authority User
        self.other_authority = User.objects.create_user(
            username='auth_other',
            email='other@test.com',
            password='password123',
            role='authority'
        )
        self.other_authority.user_permissions.add(view_perm, add_perm, change_perm, delete_perm)
        
        # Create Supplier User
        self.supplier = User.objects.create_user(
            username='supp_test',
            email='supp@test.com',
            password='password123',
            role='supplier'
        )
        
        # Create Tenders
        self.draft_tender = Tender.objects.create(
            title="Draft Tender",
            authority=self.authority,
            description="Test",
            budget=100.00,
            deadline="2027-01-01",
            status="draft"
        )
        
        self.published_tender = Tender.objects.create(
            title="Published Tender",
            authority=self.authority,
            description="Test",
            budget=100.00,
            deadline="2027-01-01",
            status="published"
        )

    def test_supplier_access_denied(self):
        # Supplier should not access authority_tender_list (403 or redirect)
        self.client.force_login(self.supplier)
        response = self.client.get(reverse('procurement:authority_tender_list'))
        self.assertEqual(response.status_code, 403)
        
    def test_unauthenticated_access_denied(self):
        # Unauthenticated user should be redirected to login (302)
        response = self.client.get(reverse('procurement:authority_tender_list'))
        self.assertEqual(response.status_code, 302)
        
    def test_authority_cannot_edit_others_tender(self):
        # auth_other tries to edit auth_test's tender (should get 404)
        self.client.force_login(self.other_authority)
        response = self.client.get(reverse('procurement:tender_edit', args=[self.draft_tender.id]))
        self.assertEqual(response.status_code, 404)

    def test_authority_cannot_edit_published_tender(self):
        # auth_test tries to edit their own published tender (should be redirected/blocked)
        self.client.force_login(self.authority)
        response = self.client.get(reverse('procurement:tender_edit', args=[self.published_tender.id]))
        # Should redirect back to list because of the block we added
        self.assertRedirects(response, reverse('procurement:authority_tender_list'))
        
    def test_authority_can_edit_draft_tender(self):
        # auth_test tries to edit their own draft tender
        self.client.force_login(self.authority)
        response = self.client.get(reverse('procurement:tender_edit', args=[self.draft_tender.id]))
        self.assertEqual(response.status_code, 200)

    def test_authority_cannot_delete_published_tender(self):
        # auth_test tries to delete published tender
        self.client.force_login(self.authority)
        response = self.client.post(reverse('procurement:tender_delete', args=[self.published_tender.id]))
        self.assertRedirects(response, reverse('procurement:authority_tender_list'))
        self.published_tender.refresh_from_db()
        self.assertFalse(self.published_tender.is_deleted)
