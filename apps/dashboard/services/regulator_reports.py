import csv
import io
from django.http import HttpResponse
from apps.procurement.models import Tender

# Try to import reportlab, if not present fallback gracefully
try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    import arabic_reshaper
    from bidi.algorithm import get_display
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False

class RegulatorReportsService:
    
    @staticmethod
    def generate_csv_report(queryset):
        """
        Generates a CSV report from a Tender queryset.
        """
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="regulator_tenders_report.csv"'
        
        # Add BOM for UTF-8 Excel compatibility
        response.write('\ufeff'.encode('utf8'))
        
        writer = csv.writer(response)
        writer.writerow([
            'المعرف', 'العنوان', 'الولاية', 'القطاع', 
            'الحالة', 'النوع', 'تاريخ النشر', 'الموعد النهائي'
        ])
        
        for tender in queryset:
            writer.writerow([
                tender.id,
                tender.title,
                tender.wilaya or 'غير محدد',
                tender.sector or 'غير محدد',
                tender.get_status_display(),
                tender.get_tender_type_display(),
                tender.created_at.strftime('%Y-%m-%d %H:%M') if tender.created_at else '',
                tender.deadline.strftime('%Y-%m-%d %H:%M') if tender.deadline else '',
            ])
            
        return response

    @staticmethod
    def generate_pdf_report(queryset):
        """
        Generates a simple PDF report from a Tender queryset.
        Returns a CSV fallback if reportlab is not installed.
        """
        if not HAS_REPORTLAB:
            return RegulatorReportsService.generate_csv_report(queryset)
            
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=A4)
        
        # Note: Proper Arabic support in ReportLab requires registering an Arabic TTF font.
        # This is a generic implementation. In production, provide a valid TTF path.
        # pdfmetrics.registerFont(TTFont('ArabicFont', 'path/to/arial.ttf'))
        # p.setFont('ArabicFont', 12)
        
        width, height = A4
        y = height - 50
        
        def write_arabic(text, x, y):
            # Reshape and apply bidi algorithm
            reshaped_text = arabic_reshaper.reshape(text)
            bidi_text = get_display(reshaped_text)
            p.drawString(x, y, bidi_text)

        p.setFont('Helvetica-Bold', 16)
        p.drawString(200, y, "Regulator Tenders Report")
        y -= 30
        
        p.setFont('Helvetica', 10)
        p.drawString(50, y, "ID | Title | Status | Deadline")
        y -= 20
        
        for tender in queryset[:50]: # Limit to 50 for this basic PDF
            if y < 50:
                p.showPage()
                y = height - 50
                p.setFont('Helvetica', 10)
            
            # Using ascii fallback for PDF if no arabic font is setup, 
            # ideally we use the write_arabic function with a TTF font.
            title = tender.title[:30] if tender.title else ''
            line = f"{tender.id} | {title} | {tender.status} | {tender.deadline.strftime('%Y-%m-%d') if tender.deadline else ''}"
            p.drawString(50, y, line)
            y -= 15
            
        p.showPage()
        p.save()
        
        buffer.seek(0)
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="regulator_tenders_report.pdf"'
        return response
