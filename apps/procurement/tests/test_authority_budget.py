from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.procurement.models import AnnualBudget, PlannedProject
from django.contrib.auth.models import Permission

User = get_user_model()

class AuthorityBudgetTest(TestCase):
    def setUp(self):
        self.client = Client()
        
        self.authority = User.objects.create_user(username='auth', role='authority')
        self.other_auth = User.objects.create_user(username='auth2', role='authority')
        self.supplier = User.objects.create_user(username='supp', role='supplier')
        
        view_perm = Permission.objects.get(codename='view_tender')
        add_perm = Permission.objects.get(codename='add_tender')
        change_perm = Permission.objects.get(codename='change_tender')
        
        self.authority.user_permissions.add(view_perm, add_perm, change_perm)
        self.other_auth.user_permissions.add(view_perm, add_perm, change_perm)
        
        self.budget = AnnualBudget.objects.create(
            year=2024, sector='Test Sector', total_budget=100000, authority=self.authority, status='draft'
        )

    def test_authority_budget_list_access(self):
        self.client.force_login(self.authority)
        response = self.client.get(reverse('procurement:authority_budget_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Sector')
        
    def test_supplier_budget_list_denied(self):
        self.client.force_login(self.supplier)
        response = self.client.get(reverse('procurement:authority_budget_list'))
        self.assertEqual(response.status_code, 403) # No permission

    def test_budget_create(self):
        self.client.force_login(self.authority)
        url = reverse('procurement:budget_create')
        data = {
            'year': 2025,
            'sector': 'New Sector',
            'budget_type': 'state',
            'total_budget': 500000,
            'notes': 'خطة تجريبية'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302) # Redirects to detail
        self.assertTrue(AnnualBudget.objects.filter(year=2025).exists())

    def test_budget_detail_and_add_project(self):
        self.client.force_login(self.authority)
        url = reverse('procurement:budget_detail', args=[self.budget.id])
        
        # Test Get
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        
        # Test POST (add project)
        data = {
            'operation_code': 'OP-2024-01',
            'ap_number': 'AP-992',
            'title': 'New Project',
            'procurement_nature': 'works',
            'planned_procedure': 'open',
            'estimated_value': 20000,
            'estimated_quarter': 1,
            'expected_launch_date': '2024-12-01'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.budget.planned_projects.count(), 1)
        self.assertEqual(self.budget.planned_projects.first().title, 'New Project')

    def test_budget_submit(self):
        self.client.force_login(self.authority)
        
        # Try to submit empty budget (should fail but redirect)
        url = reverse('procurement:budget_submit', args=[self.budget.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.budget.refresh_from_db()
        self.assertEqual(self.budget.status, 'draft') # Status didn't change
        
        # Add project
        PlannedProject.objects.create(budget=self.budget, title='Proj', estimated_value=100)
        
        # Try submit again
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.budget.refresh_from_db()
        self.assertEqual(self.budget.status, 'submitted') # Status changed

    def test_other_authority_cannot_access_budget(self):
        self.client.force_login(self.other_auth)
        url = reverse('procurement:budget_detail', args=[self.budget.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404) # get_object_or_404 filters by authority=request.user

    def test_launch_tender_from_project(self):
        self.client.force_login(self.authority)
        project = PlannedProject.objects.create(
            budget=self.budget, 
            title='مشروع بناء مدرسة',
            estimated_value=15000000,
            procurement_nature='works',
            planned_procedure='open',
            estimated_quarter=2
        )
        url = reverse('procurement:launch_tender_from_project', args=[project.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        project.refresh_from_db()
        self.assertTrue(project.is_launched)
        self.assertIsNotNone(project.tender)
        self.assertEqual(project.tender.title, 'مشروع بناء مدرسة')
        self.assertEqual(project.tender.status, 'draft')
