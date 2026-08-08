from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.procurement.models import Tender, Bid
from django.utils import timezone
from datetime import timedelta
import os
from django.core.files.uploadedfile import SimpleUploadedFile

User = get_user_model()

class SecureBidDownloadTests(TestCase):
    def setUp(self):
        self.client = Client()
        
        # Create Users
        self.authority_user = User.objects.create_user(
            username='authority', 
            password='password123',
            role='authority'
        )
        self.bidder_user = User.objects.create_user(
            username='bidder', 
            password='password123',
            role='supplier'
        )
        self.other_bidder = User.objects.create_user(
            username='other_bidder', 
            password='password123',
            role='supplier'
        )
        
        # Create Tender
        self.tender = Tender.objects.create(
            title="Test Tender",
            description="Tender Description",
            budget=100000.00,
            authority=self.authority_user,
            deadline=timezone.now().date() + timedelta(days=1),
            status='active',
            is_bids_opened=False
        )
        
        # Create Bid with a dummy file
        dummy_file = SimpleUploadedFile(
            "dummy_financial.pdf",
            b"file_content",
            content_type="application/pdf"
        )
        
        self.bid = Bid.objects.create(
            tender=self.tender,
            supplier=self.bidder_user,
            supplier_name="Test Supplier",
            financial_offer=1000.00,
            financial_document=dummy_file,
            status='pending'
        )

    def test_unauthenticated_access(self):
        url = reverse('procurement:secure_bid_download', args=[self.bid.id, 'financial'])
        response = self.client.get(url)
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)

    def test_owner_can_access_before_opening(self):
        self.client.force_login(self.bidder_user)
        url = reverse('procurement:secure_bid_download', args=[self.bid.id, 'financial'])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')

    def test_other_bidder_cannot_access(self):
        self.client.force_login(self.other_bidder)
        url = reverse('procurement:secure_bid_download', args=[self.bid.id, 'financial'])
        response = self.client.get(url)
        # Should raise PermissionDenied (403)
        self.assertEqual(response.status_code, 403)

    def test_authority_cannot_access_before_opening(self):
        self.client.force_login(self.authority_user)
        url = reverse('procurement:secure_bid_download', args=[self.bid.id, 'financial'])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_authority_can_access_after_opening(self):
        self.tender.is_bids_opened = True
        self.tender.save()
        
        self.client.force_login(self.authority_user)
        url = reverse('procurement:secure_bid_download', args=[self.bid.id, 'financial'])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_invalid_document_type(self):
        self.client.force_login(self.bidder_user)
        url = reverse('procurement:secure_bid_download', args=[self.bid.id, 'invalid_type'])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_superuser_cannot_access_unowned_bids(self):
        superuser = User.objects.create_superuser(
            username='admin',
            password='password123',
            email='admin@test.com'
        )
        self.client.force_login(superuser)
        url = reverse('procurement:secure_bid_download', args=[self.bid.id, 'financial'])
        response = self.client.get(url)
        # Should raise PermissionDenied (403) since superusers are NOT an exception
        self.assertEqual(response.status_code, 403)

    def test_direct_media_access_forbidden(self):
        url = f'/media/{self.bid.financial_document.name}'
        response = self.client.get(url)
        # Should return 403 Forbidden due to our custom URL regex blocking /media/bids/secure/
        self.assertEqual(response.status_code, 403)
