import logging
from django.db import transaction
from django.core.exceptions import PermissionDenied, ValidationError
from django.utils import timezone
from apps.procurement.models import Tender, Bid, Award, Contract

logger = logging.getLogger(__name__)

@transaction.atomic
def approve_award_and_create_contract(user, tender_id, bid_id, decision_reference, awarded_amount, decision_document=None):
    """
    Business logic for approving an award, ensuring data integrity,
    locking records, and generating a contract automatically.
    """
    
    # 1. التحقق من صلاحية المستخدم
    if not user.has_perm('procurement.approve_award'):
        raise PermissionDenied("ليس لديك الصلاحية لاعتماد الإسناد.")
    
    # 2. قفل الصفقة والعرض (Select for Update لمنع Race Conditions)
    try:
        tender = Tender.objects.select_for_update().get(id=tender_id)
        bid = Bid.objects.select_for_update().get(id=bid_id, tender=tender)
    except Tender.DoesNotExist:
        raise ValidationError("الصفقة غير موجودة.")
    except Bid.DoesNotExist:
        raise ValidationError("العرض المحدد غير موجود ضمن هذه الصفقة.")
    
    # 3. التحقق من عدم وجود إسناد نهائي سابق لهذه الصفقة
    if hasattr(tender, 'award') and tender.award.status in ['approved', 'published']:
        raise ValidationError("يوجد إسناد نهائي معتمد مسبقاً لهذه الصفقة.")
    
    # 4. إنشاء الإسناد (Award)
    award, created = Award.objects.update_or_create(
        tender=tender,
        defaults={
            'winning_bid': bid,
            'awarded_by': user,
            'awarded_at': timezone.now(),
            'status': 'approved',
            'awarded_amount': awarded_amount,
            'decision_reference': decision_reference,
        }
    )
    if decision_document:
        award.decision_document = decision_document
        award.save(update_fields=['decision_document'])
        
    # 5. تحديث حالة الصفقة والعروض (Tender & Bids)
    from apps.core.models import Notification
    
    # Reject all other bids automatically and set the winning bid to accepted.
    losing_bids = Bid.objects.filter(tender=tender).exclude(id=bid_id)
    losing_bids.update(status='rejected')
    
    bid.status = 'accepted'
    bid.save(update_fields=['status'])

    # Send Notification to Winner
    Notification.objects.create(
        user=bid.supplier,
        title="تهانينا! فوز بصفقة",
        message=f"لقد تم اختيار عرضكم للصفقة: {tender.title}. يرجى مراجعة لوحة القيادة للاطلاع على مسودة العقد.",
        link=tender.get_absolute_url()
    )

    # Send Notification to Losers
    for loser in losing_bids:
        Notification.objects.create(
            user=loser.supplier,
            title="إشعار بخصوص تقييم عرضكم",
            message=f"نعتذر، لم يتم اختيار عرضكم للصفقة: {tender.title}. نتمنى لكم التوفيق في المناقصات القادمة.",
            link=tender.get_absolute_url()
        )

    # تحديث حالة الصفقة لتعكس انتهاء التقييم والانتقال للإسناد
    tender.status = 'closed'
    tender.save(update_fields=['status', 'updated_at'])
    
    # 6. إنشاء العقد (Contract) عند الحاجة (مسودة)
    contract_number = f"C-{tender.id}-{timezone.now().year}"
    
    if not hasattr(award, 'contract'):
        contract = Contract.objects.create(
            award=award,
            contract_number=contract_number,
            supplier=bid.supplier,
            authority=tender.authority,
            title=f"عقد الصفقة: {tender.title}",
            status='draft',
            total_value=awarded_amount,
            created_by=user,
        )
    else:
        contract = award.contract

    # 7. إنشاء Audit Log
    logger.info(
        f"AuditLog: User {user.id} approved Award for Tender {tender.id}. "
        f"Award ID: {award.id}, Contract ID: {contract.id}."
    )
    
    return award, contract
