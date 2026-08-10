from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.db import connection
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission

User = get_user_model()

from django.contrib.contenttypes.models import ContentType

class RegulatorDashboardQueryTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="regulator_test",
            password="password123",
            role="regulator"
        )
        
        ct, _ = ContentType.objects.get_or_create(app_label='dashboard', model='dashboard')
        perm, _ = Permission.objects.get_or_create(
            codename='view_regulator_dashboard',
            content_type=ct,
            defaults={'name': 'Can view regulator dashboard'}
        )
        
        self.user.user_permissions.add(perm)
        self.client.force_login(self.user)

    def test_dashboard_query_count(self):
        with CaptureQueriesContext(connection) as queries:
            response = self.client.get(
                reverse("dashboard:regulator")
            )
            self.assertEqual(response.status_code, 200)

        self.assertLessEqual(len(queries), 12)
