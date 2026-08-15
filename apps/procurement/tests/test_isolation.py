from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.procurement.models import Tender, Bid, Award, Contract
from django.contrib.auth.models import Permission
from decimal import Decimal
from django.utils import timezone

User = get_user_model()

class AuthorityIsolationTests(TestCase):
    def setUp(self):
        self.client_a = Client()
        self.client_b = Client()
        
        # Authority A
        self.authority_a = User.objects.create_user(
            username='auth_a', email='auth_a@test.com', password='password123', role='authority'
        )
        # Authority B
        self.authority_b = User.objects.create_user(
            username='auth_b', email='auth_b@test.com', password='password123', role='authority'
        )
        
        # Supplier
        self.supplier = User.objects.create_user(
            username='sup', email='sup@test.com', password='password123', role='supplier'
        )

        # Grant permissions
        approve_perm = Permission.objects.get(codename='approve_award')
        change_contract_perm = Permission.objects.get(codename='change_contract')
        self.authority_a.user_permissions.add(approve_perm, change_contract_perm)
        self.authority_b.user_permissions.add(approve_perm, change_contract_perm)

        # Tender & Bid for A
        self.tender_a = Tender.objects.create(
            title='Tender A', authority=self.authority_a, status='evaluating', 
            budget=Decimal('1000.00'), deadline=timezone.now() + timezone.timedelta(days=10)
        )
        self.bid_a = Bid.objects.create(
            tender=self.tender_a, supplier=self.supplier, financial_offer=Decimal('900.00'), status='submitted'
        )
        
        # Tender & Bid for B
        self.tender_b = Tender.objects.create(
            title='Tender B', authority=self.authority_b, status='evaluating', 
            budget=Decimal('2000.00'), deadline=timezone.now() + timezone.timedelta(days=10)
        )
        self.bid_b = Bid.objects.create(
            tender=self.tender_b, supplier=self.supplier, financial_offer=Decimal('1900.00'), status='submitted'
        )

        # Pre-approved Award for B
        self.award_b = Award.objects.create(
            tender=self.tender_b, winning_bid=self.bid_b, awarded_by=self.authority_b,
            awarded_amount=Decimal('1900.00'), decision_reference='DEC-B', status='approved'
        )
        self.contract_b = Contract.objects.create(
            award=self.award_b, contract_number='C-B001', supplier=self.supplier,
            authority=self.authority_b, title='Contract B', total_value=Decimal('1900.00'),
            created_by=self.authority_b, status='draft'
        )

        self.client_a.force_login(self.authority_a)
        self.client_b.force_login(self.authority_b)

    def test_authority_a_cannot_view_award_b(self):
        """[x] اختبار منع مصلحة A من رؤية تفاصيل إسناد المصلحة B."""
        response = self.client_a.get(reverse('procurement:award_detail', kwargs={'pk': self.award_b.pk}))
        self.assertEqual(response.status_code, 403) # Forbidden

    def test_authority_a_cannot_approve_tender_b(self):
        """[x] اختبار منع مصلحة A من تنفيذ قرار إسناد للصفقة B."""
        url = reverse('procurement:award_approve', kwargs={'tender_id': self.tender_b.id, 'bid_id': self.bid_b.id})
        response = self.client_a.get(url)
        self.assertEqual(response.status_code, 403)

    def test_authority_a_cannot_view_contract_b(self):
        """[x] اختبار منع مصلحة A من رؤية تفاصيل عقد المصلحة B."""
        response = self.client_a.get(reverse('procurement:contract_detail', kwargs={'pk': self.contract_b.pk}))
        self.assertEqual(response.status_code, 403)

    def test_authority_a_cannot_update_contract_b(self):
        """[x] اختبار منع مصلحة A من تعديل مسودة العقد للمصلحة B."""
        response = self.client_a.post(reverse('procurement:contract_update', kwargs={'pk': self.contract_b.pk}), {
            'title': 'Hacked Title'
        })
        self.assertEqual(response.status_code, 403)
