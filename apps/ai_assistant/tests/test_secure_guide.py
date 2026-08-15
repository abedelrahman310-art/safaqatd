import json
from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch
from apps.accounts.models import User
from django.core.cache import cache

class SecureAIGuideTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('ai_assistant:secure')
        cache.clear()
        
        # Create users
        self.supplier = User.objects.create_user(
            username='supplier', password='password', role='supplier', sector='IT'
        )
        self.authority = User.objects.create_user(
            username='authority', password='password', role='authority'
        )

    def test_unauthenticated_access_denied(self):
        response = self.client.post(self.url, data=json.dumps({"question": "مرحبا"}), content_type='application/json')
        # Login required redirects to login page (302)
        self.assertEqual(response.status_code, 302)

    @patch('apps.ai_assistant.services.AIService.is_provider_available', return_value=True)
    @patch('apps.ai_assistant.services.AIService.generate_role_based_response')
    def test_supplier_context_is_used(self, mock_generate, mock_avail):
        mock_generate.return_value = {"status": "ok", "title": "Test", "answer": "Supplier answer"}
        
        self.client.force_login(self.supplier)
        response = self.client.post(self.url, data=json.dumps({"question": "كم عرض عندي"}), content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(mock_generate.called)
        
        # Check that context passed to mock contains supplier info
        args, kwargs = mock_generate.call_args
        context_passed = args[1]
        self.assertIn("متعامل اقتصادي", context_passed['role_context'])
        self.assertIn("previous_bids_count", context_passed['data'].get('supplier_profile', {}))

    @patch('apps.ai_assistant.services.AIService.is_provider_available', return_value=True)
    @patch('apps.ai_assistant.services.AIService.generate_role_based_response')
    def test_authority_context_is_used(self, mock_generate, mock_avail):
        mock_generate.return_value = {"status": "ok", "title": "Test", "answer": "Authority answer"}
        
        self.client.force_login(self.authority)
        response = self.client.post(self.url, data=json.dumps({"question": "كم صفقة لدي"}), content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(mock_generate.called)
        
        # Check that context passed to mock contains authority info
        args, kwargs = mock_generate.call_args
        context_passed = args[1]
        self.assertIn("مصلحة متعاقدة", context_passed['role_context'])
        self.assertIn("إجمالي صفقاتي", context_passed['data'])
