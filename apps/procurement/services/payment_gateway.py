import uuid
from decimal import Decimal
from django.utils import timezone
from django.db import transaction
from apps.procurement.models import DocumentPayment, Tender, ProcurementAuditLog

class AlgerianPaymentService:
    """
    Sovereign Payment Gateway Service for Algerian Public Procurement.
    Supports SATIM (CIB) and Algérie Poste (Edahabia) protocols.
    """

    @staticmethod
    def generate_order_id(tender_id, user_id):
        """Generates an institutional, collision-free transaction order ID."""
        ts = int(timezone.now().timestamp())
        raw = f"DZ-T{tender_id}-U{user_id}-{ts}"
        return raw

    @staticmethod
    def generate_receipt_number(tender_id, payment_id):
        """Generates an official public treasury receipt number."""
        year = timezone.now().year
        return f"REC-{year}-{tender_id:04d}-{payment_id:06d}"

    @classmethod
    def initiate_payment_session(cls, user, tender, payment_method='edahabia'):
        """
        Initializes an electronic payment session for purchasing the Cahier des Charges.
        Returns the checkout parameters or simulation payload for sandbox environments.
        """
        if not user.is_authenticated or user.role != 'supplier':
            raise PermissionError("الدفع متاح فقط للمتعاملين الاقتصاديين المسجلين.")

        # Check if already paid and completed
        existing = DocumentPayment.objects.filter(tender=tender, supplier=user, status='completed').first()
        if existing:
            return {
                'already_paid': True,
                'payment_id': existing.id,
                'receipt_number': existing.receipt_number,
                'status': 'completed'
            }

        order_id = cls.generate_order_id(tender.id, user.id)
        amount = tender.document_fee if tender.document_fee > 0 else Decimal('1000.00')

        payment, created = DocumentPayment.objects.get_or_create(
            tender=tender,
            supplier=user,
            defaults={
                'amount': amount,
                'transaction_id': order_id,
                'payment_method': payment_method,
                'status': 'initialized'
            }
        )

        if not created and payment.status != 'completed':
            payment.transaction_id = order_id
            payment.payment_method = payment_method
            payment.status = 'initialized'
            payment.amount = amount
            payment.save()

        return {
            'already_paid': False,
            'payment_id': payment.id,
            'order_id': order_id,
            'amount': float(amount),
            'currency': 'DZD',
            'tender_title': tender.title,
            'authority_name': tender.authority.institution_name if (tender.authority and tender.authority.institution_name) else 'المصلحة المتعاقدة',
            'payment_method': payment_method,
            'status': 'initialized'
        }

    @classmethod
    def process_and_confirm_payment(cls, user, payment_id, card_number_last4="4590", ip_address="127.0.0.1"):
        """
        Executes simulated 3D-Secure confirmation and updates official audit logs and receipt.
        """
        try:
            payment = DocumentPayment.objects.get(id=payment_id, supplier=user)
        except DocumentPayment.DoesNotExist:
            raise ValueError("معاملة الدفع غير موجودة أو غير مصرح بالوصول إليها.")

        # Generate Approval Code & Official Receipt
        approval_code = f"AUTH-{uuid.uuid4().hex[:8].upper()}"
        receipt_no = cls.generate_receipt_number(payment.tender.id, payment.id)

        payment.status = 'completed'
        payment.approval_code = approval_code
        payment.receipt_number = receipt_no
        payment.save()

        # Institutional Audit Trail
        ProcurementAuditLog.log_action(
            user=user,
            action='PAY_DOCUMENT_FEE',
            resource_type='document_payment',
            resource_id=payment.id,
            details={
                'tender_id': payment.tender.id,
                'tender_title': payment.tender.title,
                'amount': str(payment.amount),
                'currency': 'DZD',
                'payment_method': payment.payment_method,
                'approval_code': approval_code,
                'receipt_number': receipt_no,
                'card_last4': card_number_last4,
                'gateway': 'SATIM/EPAY-ALGERIA-SANDBOX'
            },
            ip_address=ip_address
        )

        return {
            'success': True,
            'status': 'completed',
            'receipt_number': receipt_no,
            'approval_code': approval_code,
            'paid_at': payment.paid_at.strftime('%Y-%m-%d %H:%M:%S'),
            'tender_id': payment.tender.id,
            'download_url': f"/procurement/tenders/{payment.tender.id}/"
        }
