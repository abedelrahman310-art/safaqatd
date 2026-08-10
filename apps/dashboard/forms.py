from django import forms
from apps.procurement.models import Tender

class RegulatorFilterForm(forms.Form):
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date"})
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date"})
    )
    status = forms.ChoiceField(
        required=False,
        choices=[('', 'الكل')] + list(Tender.STATUS_CHOICES)
    )
    wilaya = forms.CharField(
        required=False
    )
    sector = forms.CharField(
        required=False
    )

    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data.get("date_from")
        date_to = cleaned_data.get("date_to")

        if date_from and date_to and date_from > date_to:
            raise forms.ValidationError("تاريخ البداية يجب أن يكون قبل أو يساوي تاريخ النهاية.")
        return cleaned_data
