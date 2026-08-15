import io
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from apps.procurement.models import Tender, DocumentPayment
from django.contrib.auth.models import Permission
import tempfile
import filetype

User = get_user_model()

class AuthorityDocumentsSecurityTest(TestCase):
    def setUp(self):
        self.client = Client()
        
        # Users
        self.authority = User.objects.create_user(username='auth', role='authority')
        self.other_auth = User.objects.create_user(username='other_auth', role='authority')
        self.supplier = User.objects.create_user(username='supp', role='supplier')
        self.regulator = User.objects.create_user(username='reg', role='regulator')
        
        view_perm = Permission.objects.get(codename='view_tender')
        self.authority.user_permissions.add(view_perm)
        self.supplier.user_permissions.add(view_perm)
        
        # Valid PDF content (magic bytes for PDF)
        valid_pdf_content = b'%PDF-1.4\n1 0 obj\n<<\n/Title (Test PDF)\n>>\nendobj\ntrailer\n<<\n/Root 1 0 R\n>>\n%%EOF'
        self.pdf_file = SimpleUploadedFile("test_doc.pdf", valid_pdf_content, content_type="application/pdf")
        
        self.tender_free = Tender.objects.create(
            title="Free Tender", authority=self.authority, budget=100, deadline="2027-01-01",
            status="published", document_fee=0, document=self.pdf_file
        )
        
        self.tender_paid = Tender.objects.create(
            title="Paid Tender", authority=self.authority, budget=100, deadline="2027-01-01",
            status="published", document_fee=5000, document=self.pdf_file
        )

        self.tender_draft = Tender.objects.create(
            title="Draft Tender", authority=self.authority, budget=100, deadline="2027-01-01",
            status="draft", document_fee=0, document=self.pdf_file
        )

    def test_anonymous_access_denied(self):
        response = self.client.get(reverse('procurement:download_tender_document', args=[self.tender_free.id]))
        self.assertEqual(response.status_code, 302) # Redirect to login

    def test_supplier_free_published_download(self):
        self.client.force_login(self.supplier)
        response = self.client.get(reverse('procurement:download_tender_document', args=[self.tender_free.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')

    def test_supplier_paid_no_payment_denied(self):
        self.client.force_login(self.supplier)
        response = self.client.get(reverse('procurement:download_tender_document', args=[self.tender_paid.id]))
        # Should redirect back or 403. Our implementation redirects with messages.error
        self.assertEqual(response.status_code, 302)

    def test_supplier_paid_with_payment_success(self):
        DocumentPayment.objects.create(tender=self.tender_paid, supplier=self.supplier, amount=5000, transaction_id="TX123")
        self.client.force_login(self.supplier)
        response = self.client.get(reverse('procurement:download_tender_document', args=[self.tender_paid.id]))
        self.assertEqual(response.status_code, 200)

    def test_supplier_cannot_download_draft(self):
        self.client.force_login(self.supplier)
        response = self.client.get(reverse('procurement:download_tender_document', args=[self.tender_draft.id]))
        self.assertEqual(response.status_code, 403)

    def test_authority_can_download_own(self):
        self.client.force_login(self.authority)
        response = self.client.get(reverse('procurement:download_tender_document', args=[self.tender_draft.id]))
        self.assertEqual(response.status_code, 200)

    def test_authority_cannot_download_other(self):
        self.client.force_login(self.other_auth)
        response = self.client.get(reverse('procurement:download_tender_document', args=[self.tender_draft.id]))
        self.assertEqual(response.status_code, 403)
        
    def test_regulator_can_download_any(self):
        self.client.force_login(self.regulator)
        response = self.client.get(reverse('procurement:download_tender_document', args=[self.tender_draft.id]))
        self.assertEqual(response.status_code, 200)
