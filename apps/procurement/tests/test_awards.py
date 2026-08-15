from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError, PermissionDenied
from django.utils import timezone
from decimal import Decimal
from apps.procurement.models import Tender, Bid, Award, Contract, ContractAmendment
from apps.procurement.services import approve_award_and_create_contract
from django.contrib.auth.models import Permission
import logging

User = get_user_model()

class AwardContractTests(TestCase):
    def setUp(self):
        # Create users
        self.authority_user = User.objects.create_user(
            username='auth1',
            email='authority@test.com',
            password='password123',
            role='authority'
        )
        self.other_authority = User.objects.create_user(
            username='auth2',
            email='other@test.com',
            password='password123',
            role='authority'
        )
        self.supplier_user = User.objects.create_user(
            username='sup1',
            email='supplier@test.com',
            password='password123',
            role='supplier'
        )
        self.staff_user = User.objects.create_user(
            username='staff1',
            email='staff@test.com',
            password='password123',
            is_staff=True
        )
        
        # Grant permissions to authority_user
        approve_perm = Permission.objects.get(codename='approve_award')
        self.authority_user.user_permissions.add(approve_perm)
        self.authority_user.save()
        
        # Create Tenders
        self.tender = Tender.objects.create(
            title='Test Tender',
            authority=self.authority_user,
            status='evaluating',
            budget=Decimal('1000000.00'),
            deadline=timezone.now() + timezone.timedelta(days=10)
        )
        self.other_tender = Tender.objects.create(
            title='Other Tender',
            authority=self.other_authority,
            status='evaluating',
            budget=Decimal('500000.00'),
            deadline=timezone.now() + timezone.timedelta(days=10)
        )
        
        # Create Bids
        self.bid = Bid.objects.create(
            tender=self.tender,
            supplier=self.supplier_user,
            financial_offer=Decimal('950000.00'),
            status='submitted'
        )
        self.other_bid = Bid.objects.create(
            tender=self.other_tender,
            supplier=self.supplier_user,
            financial_offer=Decimal('450000.00'),
            status='submitted'
        )

    def test_award_bid_tender_mismatch(self):
        """[x] لا يمكن ربط Award بعرض من Tender مختلف."""
        award = Award(
            tender=self.tender,
            winning_bid=self.other_bid,
            awarded_by=self.authority_user,
            awarded_amount=Decimal('100.00'),
            decision_reference='DEC-001'
        )
        with self.assertRaises(ValidationError) as ctx:
            award.clean()
        self.assertIn("winning_bid", str(ctx.exception))

    def test_prevent_duplicate_final_award(self):
        """[x] لا يمكن إنشاء Award نهائي مرتين للصفقة نفسها."""
        Award.objects.create(
            tender=self.tender,
            winning_bid=self.bid,
            awarded_by=self.authority_user,
            awarded_amount=Decimal('950000.00'),
            decision_reference='DEC-001',
            status='approved'
        )
        with self.assertRaises(ValidationError):
            approve_award_and_create_contract(
                user=self.authority_user,
                tender_id=self.tender.id,
                bid_id=self.bid.id,
                decision_reference='DEC-002',
                awarded_amount=Decimal('950000.00')
            )

    def test_contract_needs_valid_award(self):
        """[x] لا يمكن إنشاء Contract دون Award صحيح (المورد والمصلحة يتطابقان)."""
        award = Award.objects.create(
            tender=self.tender,
            winning_bid=self.bid,
            awarded_by=self.authority_user,
            awarded_amount=Decimal('950000.00'),
            decision_reference='DEC-001',
            status='approved'
        )
        # Attempt to create contract with wrong supplier
        contract = Contract(
            award=award,
            contract_number='C-001',
            supplier=self.staff_user, # Wrong supplier
            authority=self.tender.authority,
            title='Contract 1',
            total_value=award.awarded_amount,
            created_by=self.authority_user
        )
        with self.assertRaises(ValidationError) as ctx:
            contract.clean()
        self.assertIn("supplier", str(ctx.exception))

    def test_supplier_cannot_modify(self):
        """[x] لا يستطيع Supplier تعديل Award أو Contract."""
        with self.assertRaises(PermissionDenied):
            approve_award_and_create_contract(
                user=self.supplier_user,
                tender_id=self.tender.id,
                bid_id=self.bid.id,
                decision_reference='DEC-002',
                awarded_amount=Decimal('950000.00')
            )

    def test_staff_cannot_bypass_permissions(self):
        """[x] لا يستطيع is_staff وحده تجاوز الصلاحيات."""
        with self.assertRaises(PermissionDenied):
            approve_award_and_create_contract(
                user=self.staff_user, # is_staff but no has_perm('procurement.approve_award')
                tender_id=self.tender.id,
                bid_id=self.bid.id,
                decision_reference='DEC-002',
                awarded_amount=Decimal('950000.00')
            )

    def test_audit_log_created(self):
        """[x] تُسجل عمليات الإنشاء والتعديل والاعتماد."""
        with self.assertLogs('apps.procurement.services', level='INFO') as cm:
            approve_award_and_create_contract(
                user=self.authority_user,
                tender_id=self.tender.id,
                bid_id=self.bid.id,
                decision_reference='DEC-002',
                awarded_amount=Decimal('950000.00')
            )
        self.assertTrue(any("AuditLog:" in msg for msg in cm.output))

    def test_atomicity(self):
        """[x] تفشل العملية كاملة إذا فشل جزء منها."""
        # We will pass a wrong bid id to cause exception in the middle
        # to ensure no partial data is saved.
        try:
            approve_award_and_create_contract(
                user=self.authority_user,
                tender_id=self.tender.id,
                bid_id=99999, # Non-existent
                decision_reference='DEC-002',
                awarded_amount=Decimal('950000.00')
            )
        except ValidationError:
            pass
        
        self.assertEqual(Award.objects.count(), 0)
        self.assertEqual(Contract.objects.count(), 0)
