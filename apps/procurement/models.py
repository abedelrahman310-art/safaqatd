from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from simple_history.models import HistoricalRecords

class AnnualBudget(models.Model):
    year = models.PositiveIntegerField(verbose_name="السنة المالية")
    sector = models.CharField(max_length=255, verbose_name="القطاع")
    total_budget = models.DecimalField(
        max_digits=15, decimal_places=2, 
        validators=[MinValueValidator(0.01)],
        verbose_name="الميزانية الإجمالية (دج)"
    )
    authority = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='budgets', verbose_name="المصلحة المتعاقدة", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "ميزانية سنوية"
        verbose_name_plural = "الميزانيات السنوية"
        unique_together = ('year', 'sector', 'authority')

    def __str__(self):
        return f"ميزانية {self.sector} - {self.year}"

class PlannedProject(models.Model):
    title = models.CharField(max_length=255, verbose_name="اسم المشروع المبرمج")
    budget = models.ForeignKey(AnnualBudget, on_delete=models.CASCADE, related_name='planned_projects', verbose_name="الميزانية المرتبطة")
    estimated_value = models.DecimalField(
        max_digits=12, decimal_places=2, 
        validators=[MinValueValidator(0.01)],
        verbose_name="القيمة التقديرية (دج)"
    )
    expected_launch_date = models.DateField(verbose_name="تاريخ الإطلاق المتوقع", null=True, blank=True)
    is_launched = models.BooleanField(default=False, verbose_name="تم الإطلاق (تحول إلى صفقة)")
    tender = models.ForeignKey('Tender', on_delete=models.SET_NULL, null=True, blank=True, related_name='from_planned_project', verbose_name="الصفقة الفعلية المرتبطة")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "مشروع مبرمج"
        verbose_name_plural = "المشاريع المبرمجة"

    def __str__(self):
        return self.title

class ActiveManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)
        
    def visible_to(self, user):
        """
        Filters tenders visible to the given user. 
        For central_admin, it returns all. 
        For authority, it returns their own tenders.
        """
        qs = self.get_queryset()
        if user.is_authenticated:
            if user.has_perm('accounts.audit_all_tenders'):
                return qs
            elif getattr(user, 'role', None) == 'authority':
                return qs.filter(authority=user)
            elif getattr(user, 'role', None) == 'supplier':
                return qs.filter(status__in=['published', 'evaluating', 'closed'])
        return qs.none()

class Tender(models.Model):
    STATUS_CHOICES = (
        ('draft', 'مسودة'),
        ('published', 'منشورة'),
        ('closed', 'مغلقة'),
        ('evaluating', 'قيد التقييم'),
    )
    
    TENDER_TYPES = (
        ('open', 'طلب العروض المفتوح'),
        ('minimum_capacity', 'طلب العروض مع اشتراط قدرات دنيا'),
        ('restricted', 'طلب العروض المحدود'),
        ('contest', 'المسابقة'),
        ('negotiation', 'التفاوض'),
        ('mutual', 'بالتراضي'),
    )

    title = models.CharField(max_length=200, verbose_name="عنوان الصفقة")
    authority = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tenders', verbose_name="المصلحة المتعاقدة", null=True, blank=True)
    description = models.TextField(verbose_name="التفاصيل")
    budget = models.DecimalField(
        max_digits=12, decimal_places=2, 
        validators=[MinValueValidator(0.01)],
        verbose_name="الميزانية التقديرية (دج)"
    )
    wilaya = models.CharField(max_length=100, blank=True, null=True, verbose_name="الولاية")
    sector = models.CharField(max_length=255, blank=True, null=True, verbose_name="قطاع النشاط")
    deadline = models.DateField(verbose_name="آخر أجل للتقديم")
    document = models.FileField(upload_to='tenders/documents/', null=True, blank=True, verbose_name="دفتر الشروط")
    document_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="رسوم سحب دفتر الشروط (دج)")
    tender_type = models.CharField(max_length=50, choices=TENDER_TYPES, default='open', verbose_name="نوع الصفقة")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name="الحالة")
    is_bids_opened = models.BooleanField(default=False, verbose_name="تم فتح العروض")
    ai_cahier_result = models.JSONField(null=True, blank=True, verbose_name="نتيجة دفتر الشروط AI")
    is_deleted = models.BooleanField(default=False, verbose_name="محذوف؟")
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = ActiveManager()
    all_objects = models.Manager()

    history = HistoricalRecords()

    def __str__(self):
        return self.title

    def soft_delete(self):
        from django.utils import timezone
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()

    @property
    def is_deadline_passed(self):
        from django.utils import timezone
        return timezone.now().date() > self.deadline

    class Meta:
        verbose_name = "صفقة"
        verbose_name_plural = "الصفقات"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['wilaya', 'sector']),
            models.Index(fields=['is_deleted']),
        ]

from apps.procurement.validators import validate_file_mimetype
import uuid
import os

def secure_upload_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4().hex}.{ext}"
    return os.path.join('bids', 'secure', filename)

class Bid(models.Model):
    STATUS_CHOICES = (
        ('pending', 'قيد الدراسة'),
        ('accepted', 'مقبول'),
        ('rejected', 'مرفوض'),
    )

    tender = models.ForeignKey(Tender, on_delete=models.CASCADE, related_name='bids', verbose_name="الصفقة")
    supplier = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='submitted_bids', verbose_name="المتعامل", null=True, blank=True)
    supplier_name = models.CharField(max_length=200, verbose_name="اسم الشركة / المتعامل")
    nif_number = models.CharField(max_length=50, verbose_name="رقم التعريف الجبائي (NIF)", blank=True, null=True)
    nis_number = models.CharField(max_length=50, verbose_name="رقم التعريف الإحصائي (NIS)", blank=True, null=True)
    
    financial_offer = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="العرض المالي (دج)")
    financial_document = models.FileField(upload_to=secure_upload_path, validators=[validate_file_mimetype], null=True, blank=True, verbose_name="ملف العرض المالي (PDF)")
    delivery_time_days = models.PositiveIntegerField(verbose_name="مدة الإنجاز (بالأيام)", blank=True, null=True)
    warranty_months = models.PositiveIntegerField(verbose_name="مدة الضمان (بالأشهر)", blank=True, null=True)
    
    technical_team_size = models.PositiveIntegerField(verbose_name="تعداد الطاقم التقني", blank=True, null=True)
    similar_projects_count = models.PositiveIntegerField(verbose_name="المشاريع المماثلة المنجزة", blank=True, null=True)
    technical_notes = models.TextField(verbose_name="ملاحظات العرض التقني", blank=True, null=True)
    technical_document = models.FileField(upload_to=secure_upload_path, validators=[validate_file_mimetype], null=True, blank=True, verbose_name="ملف العرض التقني (PDF)")
    
    agreement = models.BooleanField(default=False, verbose_name="موافقة وتصريح شرفي")
    integrity_declaration = models.FileField(upload_to=secure_upload_path, validators=[validate_file_mimetype], null=True, blank=True, verbose_name="التصريح بالنزاهة (PDF)")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="حالة العرض")
    submitted_at = models.DateTimeField(auto_now_add=True)

    # Blockchain Verification Fields
    bid_hash = models.CharField(max_length=255, blank=True, null=True, verbose_name="البصمة المشفرة (Hash)")
    blockchain_tx_hash = models.CharField(max_length=255, blank=True, null=True, verbose_name="رقم معاملة البلوكتشين (TxHash)")
    is_blockchain_verified = models.BooleanField(default=False, verbose_name="موثق عبر البلوكتشين")
    
    # Bank Guarantee Fields
    bank_name = models.CharField(max_length=150, blank=True, null=True, verbose_name="البنك الضامن")
    bank_guarantee_file = models.FileField(upload_to=secure_upload_path, validators=[validate_file_mimetype], blank=True, null=True, verbose_name="كفالة التعهد البنكية (PDF)")
    is_guarantee_verified = models.BooleanField(default=False, verbose_name="تم التحقق من الكفالة")

    # Soft Delete Fields
    is_deleted = models.BooleanField(default=False, verbose_name="محذوف؟")
    deleted_at = models.DateTimeField(null=True, blank=True)

    # Real AI Result
    ai_evaluation_result = models.JSONField(blank=True, null=True, verbose_name="التقييم الآلي المبدئي")

    objects = ActiveManager()
    all_objects = models.Manager()

    history = HistoricalRecords()

    def soft_delete(self):
        from django.utils import timezone
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()

    def save(self, *args, **kwargs):
        from apps.core.utils import encrypt_file_content, generate_file_hash
        from django.core.files.base import ContentFile
        import os

        # Flag to prevent infinite recursion if we need to save again
        if getattr(self, '_saving_encrypted', False):
            super().save(*args, **kwargs)
            return

        is_new = self.pk is None
        
        # We process files only when they are uploaded/modified
        files_to_encrypt = []
        if self.financial_document and not getattr(self.financial_document, '_encrypted', False):
            files_to_encrypt.append('financial_document')
        if self.technical_document and not getattr(self.technical_document, '_encrypted', False):
            files_to_encrypt.append('technical_document')

        # Generate hash based on financial doc if present
        if 'financial_document' in files_to_encrypt:
            file_content = self.financial_document.read()
            self.bid_hash = generate_file_hash(file_content)
            # Remove fake blockchain logic, keep just hash for integrity
            self.blockchain_tx_hash = "SHA-256 Hash recorded"
            self.is_blockchain_verified = False # It's just a hash now, not blockchain
            self.financial_document.seek(0)

        super().save(*args, **kwargs)

        # Now encrypt and overwrite
        if files_to_encrypt:
            self._saving_encrypted = True
            for field_name in files_to_encrypt:
                file_field = getattr(self, field_name)
                file_content = file_field.read()
                encrypted_content = encrypt_file_content(file_content)
                
                # Save the encrypted content back
                file_name = os.path.basename(file_field.name)
                file_field.save(file_name, ContentFile(encrypted_content), save=False)
                setattr(file_field, '_encrypted', True)
            
            self.save()
            self._saving_encrypted = False

    history = HistoricalRecords()

    def __str__(self):
        return f"عرض {self.supplier_name} للصفقة {self.tender.title}"

    class Meta:
        verbose_name = "عرض"
        verbose_name_plural = "العروض"
        ordering = ['-submitted_at']

class TenderQuestion(models.Model):
    tender = models.ForeignKey(Tender, on_delete=models.CASCADE, related_name='questions', verbose_name="الصفقة")
    supplier = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='asked_questions', verbose_name="المتعامل السائل")
    question_text = models.TextField(verbose_name="نص السؤال")
    answer_text = models.TextField(blank=True, null=True, verbose_name="إجابة المصلحة")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ السؤال")
    answered_at = models.DateTimeField(blank=True, null=True, verbose_name="تاريخ الإجابة")

    def __str__(self):
        return f"سؤال حول: {self.tender.title}"

class SupplierRating(models.Model):
    supplier_name = models.CharField(max_length=200, verbose_name="اسم الشركة / المتعامل")
    authority = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='given_ratings', verbose_name="المصلحة المقيمة")
    tender = models.ForeignKey(Tender, on_delete=models.CASCADE, related_name='ratings', verbose_name="الصفقة")
    rating = models.IntegerField(choices=[(1,'1'),(2,'2'),(3,'3'),(4,'4'),(5,'5')], verbose_name="التقييم")
    review_text = models.TextField(blank=True, null=True, verbose_name="المراجعة والملاحظات")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"تقييم {self.supplier_name} - {self.rating} نجوم"

class DocumentPayment(models.Model):
    tender = models.ForeignKey(Tender, on_delete=models.CASCADE, related_name='payments', verbose_name="الصفقة")
    supplier = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='document_payments', verbose_name="المتعامل")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="المبلغ المدفوع (دج)")
    transaction_id = models.CharField(max_length=100, unique=True, verbose_name="رقم العملية")
    paid_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الدفع")

    def __str__(self):
        return f"دفع {self.supplier.full_name} للصفقة {self.tender.title}"

    class Meta:
        verbose_name = "دفع دفتر الشروط"
        verbose_name_plural = "مدفوعات دفاتر الشروط"
        unique_together = ('tender', 'supplier')

class TenderAppeal(models.Model):
    STATUS_CHOICES = (
        ('pending', 'قيد الدراسة'),
        ('accepted', 'مقبول (مؤسس)'),
        ('rejected', 'مرفوض (غير مؤسس)'),
    )
    bid = models.OneToOneField('Bid', on_delete=models.CASCADE, related_name='appeal', verbose_name="العرض")
    reason = models.TextField(verbose_name="مضمون الطعن")
    attachment = models.FileField(upload_to='appeals/docs/', blank=True, null=True, verbose_name="الملف المرفق للطعن (اختياري)")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ تقديم الطعن")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="حالة الطعن")
    authority_response = models.TextField(blank=True, null=True, verbose_name="رد المصلحة المتعاقدة")

    def __str__(self):
        return f"طعن من {self.bid.supplier_name} حول الصفقة {self.bid.tender.title}"

    class Meta:
        verbose_name = "طعن"
        verbose_name_plural = "الطعون"

class CommitteeMember(models.Model):
    tender = models.ForeignKey(Tender, on_delete=models.CASCADE, related_name='committee_members', verbose_name="الصفقة")
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='committee_roles', verbose_name="عضو اللجنة")
    role_in_committee = models.CharField(max_length=100, default='عضو مقيّم', verbose_name="الصفة في اللجنة (رئيس، عضو، مقرر)")
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.full_name or self.user.email} - {self.role_in_committee} ({self.tender.title})"

    class Meta:
        verbose_name = "عضو لجنة التقييم"
        verbose_name_plural = "أعضاء لجان التقييم"
        unique_together = ('tender', 'user')

class EvaluationSignature(models.Model):
    tender = models.ForeignKey(Tender, on_delete=models.CASCADE, related_name='signatures', verbose_name="الصفقة")
    committee_member = models.ForeignKey(CommitteeMember, on_delete=models.CASCADE, related_name='signatures', verbose_name="عضو اللجنة")
    signed_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ وتوقيت المصادقة")
    signature_hash = models.CharField(max_length=255, blank=True, null=True, verbose_name="البصمة الرقمية للتوقيع (Hash)")

    def __str__(self):
        return f"توقيع {self.committee_member.user.full_name} على {self.tender.title}"

    class Meta:
        verbose_name = "توقيع التقييم"
        verbose_name_plural = "تواقيع التقييم"
        unique_together = ('tender', 'committee_member')

class BidOpeningCommittee(models.Model):
    tender = models.OneToOneField('Tender', on_delete=models.CASCADE, related_name='opening_committee', verbose_name='الصفقة')
    opened_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name='رئيس الجلسة')
    opened_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ وساعة الفتح')
    notes = models.TextField(verbose_name='ملاحظات المحضر', blank=True, null=True)
    report_file = models.FileField(upload_to='bids/reports/', blank=True, null=True, verbose_name='ملف المحضر (PDF)')
    report_version = models.PositiveIntegerField(default=1, verbose_name="رقم الإصدار")
    is_finalized = models.BooleanField(default=False, verbose_name="محضر نهائي معتمد")
    report_hash = models.CharField(max_length=255, blank=True, null=True, verbose_name="بصمة المحضر (SHA-256)")
    is_valid = models.BooleanField(default=True, verbose_name='محضر صالح')

    class Meta:
        verbose_name = 'محضر لجنة الفتح'
        verbose_name_plural = 'محاضر لجان الفتح'

    def __str__(self):
        return f'محضر فتح - {self.tender.title}'

    def save(self, *args, **kwargs):
        from django.core.exceptions import ValidationError
        if self.pk:
            old_instance = BidOpeningCommittee.objects.get(pk=self.pk)
            if old_instance.is_finalized:
                raise ValidationError("لا يمكن تعديل محضر الفتح بعد اعتماده نهائياً.")
        super().save(*args, **kwargs)

