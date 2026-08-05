from django import forms
from .models import Tender, Bid, TenderAppeal

class TenderForm(forms.ModelForm):
    class Meta:
        model = Tender
        fields = ['title', 'description', 'budget', 'tender_type', 'wilaya', 'sector', 'deadline', 'document', 'document_fee', 'status']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'أدخل عنوان الصفقة...'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'تفاصيل وشروط الصفقة...'}),
            'budget': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'مثال: 1500000.00'}),
            'wilaya': forms.Select(choices=[
                ('', '-- اختر الولاية --'),
                ('16', '16 - الجزائر العاصمة'),
                ('31', '31 - وهران'),
                ('25', '25 - قسنطينة'),
                ('30', '30 - ورقلة'),
                ('47', '47 - غرداية'),
                ('other', 'أخرى...'),
            ], attrs={'class': 'form-control'}),
            'sector': forms.Select(choices=[
                ('', '-- اختر القطاع --'),
                ('tech', 'إعلام آلي واتصالات'),
                ('construction', 'بناء وأشغال عمومية'),
                ('services', 'خدمات واستشارات'),
                ('equipment', 'توريد معدات وتجهيزات'),
                ('other', 'قطاع آخر'),
            ], attrs={'class': 'form-control'}),
            'deadline': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'document': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'document_fee': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'مثال: 5000.00 (0 تعني مجاني)'}),
            'tender_type': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }

class BidForm(forms.ModelForm):
    class Meta:
        model = Bid
        fields = [
            'financial_offer', 'financial_document', 'delivery_time_days', 'warranty_months',
            'technical_team_size', 'similar_projects_count', 'technical_notes', 'technical_document',
            'bank_name', 'bank_guarantee_file',
            'agreement', 'integrity_declaration'
        ]
        widgets = {
            'bank_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'اسم البنك الذي أصدر الكفالة...'}),
            'supplier_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'أدخل اسم شركتك...'}),
            'nif_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'مثال: 000012345678900'}),
            'nis_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'مثال: 000012345678900'}),
            'financial_offer': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'مثال: 1450000.00'}),
            'delivery_time_days': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'مثال: 45'}),
            'warranty_months': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'مثال: 12'}),
            'technical_team_size': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'مثال: 15'}),
            'similar_projects_count': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'مثال: 3'}),
            'technical_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'أضف أي تفاصيل أو ملاحظات تقنية...'}),
            'agreement': forms.CheckboxInput(attrs={'style': 'transform: scale(1.5); margin-left: 10px;'}),
        }

class TenderAppealForm(forms.ModelForm):
    class Meta:
        model = TenderAppeal
        fields = ['reason', 'attachment']
        widgets = {
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'اكتب مبررات الطعن بشكل واضح ومفصل...'}),
            'attachment': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': '.pdf,.doc,.docx'}),
        }
