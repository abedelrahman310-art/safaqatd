import django_filters
from django import forms
from apps.procurement.models import Tender

class TenderFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(
        field_name='title', 
        lookup_expr='icontains', 
        label="عنوان الصفقة",
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'بحث بالعنوان...'})
    )
    wilaya = django_filters.CharFilter(
        field_name='wilaya', 
        lookup_expr='icontains', 
        label="الولاية",
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'اسم الولاية'})
    )
    status = django_filters.ChoiceFilter(
        field_name='status', 
        choices=Tender.STATUS_CHOICES,
        label="حالة الصفقة",
        widget=forms.Select(attrs={'class': 'form-input'})
    )
    sector = django_filters.CharFilter(
        field_name='sector',
        lookup_expr='icontains',
        label="القطاع",
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'قطاع...'})
    )
    date_from = django_filters.DateFilter(
        field_name='created_at',
        lookup_expr='gte',
        label="من تاريخ",
        widget=forms.DateInput(attrs={'class': 'form-input', 'type': 'date'})
    )
    date_to = django_filters.DateFilter(
        field_name='created_at',
        lookup_expr='lte',
        label="إلى تاريخ",
        widget=forms.DateInput(attrs={'class': 'form-input', 'type': 'date'})
    )

    class Meta:
        model = Tender
        fields = ['title', 'wilaya', 'status', 'sector', 'date_from', 'date_to']
