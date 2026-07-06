from django.db import models
from django.conf import settings
from simple_history.models import HistoricalRecords

class Tender(models.Model):
    STATUS_CHOICES = (
        ('draft', 'مسودة'),
        ('published', 'منشورة'),
        ('closed', 'مغلقة'),
        ('evaluating', 'قيد التقييم'),
    )

    title = models.CharField(max_length=200, verbose_name="عنوان الصفقة")
    authority = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tenders', verbose_name="المصلحة المتعاقدة", null=True, blank=True)
    description = models.TextField(verbose_name="التفاصيل")
    budget = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="الميزانية التقديرية (دج)")
    wilaya = models.CharField(max_length=100, blank=True, null=True, verbose_name="الولاية")
    sector = models.CharField(max_length=255, blank=True, null=True, verbose_name="قطاع النشاط")
    deadline = models.DateField(verbose_name="آخر أجل للتقديم")
    document = models.FileField(upload_to='tenders/documents/', null=True, blank=True, verbose_name="دفتر الشروط")
    document_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="رسوم سحب دفتر الشروط (دج)")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name="الحالة")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    history = HistoricalRecords()

    def __str__(self):
        return self.title

    @property
    def is_deadline_passed(self):
        from django.utils import timezone
        return timezone.now().date() > self.deadline

    class Meta:
        verbose_name = "صفقة"
        verbose_name_plural = "الصفقات"
        ordering = ['-created_at']

class Bid(models.Model):
    STATUS_CHOICES = (
        ('pending', 'قيد الدراسة'),
        ('accepted', 'مقبول'),
        ('rejected', 'مرفوض'),
    )

    tender = models.ForeignKey(Tender, on_delete=models.CASCADE, related_name='bids', verbose_name="الصفقة")
    supplier_name = models.CharField(max_length=200, verbose_name="اسم الشركة / المتعامل")
    nif_number = models.CharField(max_length=50, verbose_name="رقم التعريف الجبائي (NIF)", blank=True, null=True)
    nis_number = models.CharField(max_length=50, verbose_name="رقم التعريف الإحصائي (NIS)", blank=True, null=True)
    
    financial_offer = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="العرض المالي (دج)")
    financial_document = models.FileField(upload_to='bids/financial/', null=True, blank=True, verbose_name="ملف العرض المالي (PDF)")
    delivery_time_days = models.PositiveIntegerField(verbose_name="مدة الإنجاز (بالأيام)", blank=True, null=True)
    warranty_months = models.PositiveIntegerField(verbose_name="مدة الضمان (بالأشهر)", blank=True, null=True)
    
    technical_team_size = models.PositiveIntegerField(verbose_name="تعداد الطاقم التقني", blank=True, null=True)
    similar_projects_count = models.PositiveIntegerField(verbose_name="المشاريع المماثلة المنجزة", blank=True, null=True)
    technical_notes = models.TextField(verbose_name="ملاحظات العرض التقني", blank=True, null=True)
    technical_document = models.FileField(upload_to='bids/technical/', null=True, blank=True, verbose_name="ملف العرض التقني (PDF)")
    
    agreement = models.BooleanField(default=False, verbose_name="موافقة وتصريح شرفي")
    integrity_declaration = models.FileField(upload_to='bids/integrity/', null=True, blank=True, verbose_name="التصريح بالنزاهة (PDF)")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="حالة العرض")
    submitted_at = models.DateTimeField(auto_now_add=True)

    # Blockchain Verification Fields
    bid_hash = models.CharField(max_length=255, blank=True, null=True, verbose_name="البصمة المشفرة (Hash)")
    blockchain_tx_hash = models.CharField(max_length=255, blank=True, null=True, verbose_name="رقم معاملة البلوكتشين (TxHash)")
    is_blockchain_verified = models.BooleanField(default=False, verbose_name="موثق عبر البلوكتشين")
    
    # Bank Guarantee Fields
    bank_name = models.CharField(max_length=150, blank=True, null=True, verbose_name="البنك الضامن")
    bank_guarantee_file = models.FileField(upload_to='bids/guarantees/', blank=True, null=True, verbose_name="كفالة التعهد البنكية (PDF)")
    is_guarantee_verified = models.BooleanField(default=False, verbose_name="تم التحقق من الكفالة")

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
