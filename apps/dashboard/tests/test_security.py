from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Permission
from apps.procurement.models import Tender
import logging
from io import StringIO
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

class RegulatorSecurityTests(TestCase):
    def setUp(self):
        # Create users
        self.regulator = User.objects.create_user(username="regulator", password="123", role="regulator")
        self.supplier = User.objects.create_user(username="supplier", password="123", role="supplier")
        self.authority = User.objects.create_user(username="authority", password="123", role="authority")
        
        # Grant permission to regulator
        ct, _ = ContentType.objects.get_or_create(app_label='dashboard', model='dashboard')
        perm, _ = Permission.objects.get_or_create(
            codename='view_regulator_dashboard',
            content_type=ct,
            defaults={'name': 'Can view regulator dashboard'}
        )
        self.regulator.user_permissions.add(perm)

        # Create some tenders
        self.tender_visible = Tender.objects.create(
            title="Tender 1", status="published", is_deleted=False,
            budget=10000, authority=self.authority, deadline=timezone.now() + timedelta(days=7)
        )
        self.tender_deleted = Tender.objects.create(
            title="Tender Deleted", status="published", is_deleted=True,
            budget=10000, authority=self.authority, deadline=timezone.now() + timedelta(days=7)
        )
        # Note: Tender.objects.visible_to(regulator) depends on implementation, usually all non-deleted for regulator.
        
    def test_unauthenticated_user_rejected(self):
        # 1. مستخدم غير مصادق لا يصل إلى لوحة المراقب
        response = self.client.get(reverse("dashboard:regulator"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_supplier_rejected(self):
        # 2. مستخدم مورد لا يصل إلى لوحة المراقب
        self.client.force_login(self.supplier)
        response = self.client.get(reverse("dashboard:regulator"))
        self.assertEqual(response.status_code, 403)

    def test_authority_rejected(self):
        # 3. مستخدم جهة متعاقدة لا يصل إلى وظائف المراقب المركزية
        self.client.force_login(self.authority)
        response = self.client.get(reverse("dashboard:regulator"))
        self.assertEqual(response.status_code, 403)

    def test_regulator_sees_only_permitted_data(self):
        # 4 & 7. المراقب يرى فقط البيانات المسموح بها / لا تظهر بيانات مؤسسة أخرى
        self.client.force_login(self.regulator)
        response = self.client.get(reverse("dashboard:regulator"))
        self.assertEqual(response.status_code, 200)
        
        summary = response.context.get("total")
        # Should not include deleted tenders
        self.assertEqual(summary, 1)

    def test_filters_do_not_bypass_permissions(self):
        # 5. تغيير الفلاتر لا يتجاوز الصلاحيات
        self.client.force_login(self.regulator)
        # Attempt to filter for deleted tender's status
        response = self.client.get(reverse("dashboard:regulator"), {"status": "published"})
        self.assertEqual(response.context.get("total"), 1) # Still 1, deleted one not exposed

    def test_date_from_after_date_to_rejected(self):
        # 10 & 11. التاريخ غير الصحيح يرفض + date_from بعد date_to يرفض
        self.client.force_login(self.regulator)
        response = self.client.get(reverse("dashboard:regulator"), {
            "date_from": "2026-08-10",
            "date_to": "2026-08-01"
        })
        # The form should be invalid, returning empty cleaned_data (filters ignored)
        self.assertEqual(response.status_code, 200)
        form = response.context['filter'].form
        self.assertFalse(form.is_valid())
        self.assertIn("__all__", form.errors) # Form validation error

    def test_export_action_logged_to_audit_trail(self):
        # 13. سجل التصدير يضاف إلى Audit Trail
        self.client.force_login(self.regulator)
        with self.assertLogs('dashboard.exports', level='INFO') as cm:
            self.client.get(reverse("dashboard:export_regulator_csv"))
            self.assertTrue(any("exported CSV" in msg for msg in cm.output))
