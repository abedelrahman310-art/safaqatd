import os
from io import BytesIO
from django.conf import settings
from django.core.files.base import ContentFile
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import arabic_reshaper
from bidi.algorithm import get_display

import hashlib

def generate_opening_committee_pdf(committee):
    """
    Generate a PDF report for the Bid Opening Committee using reportlab.
    Supports Arabic text via arabic-reshaper and python-bidi.
    """
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # Register an Arabic font (fallback to a standard one if not found, but Arial works on Windows if path is correct)
    font_path = os.path.join(settings.BASE_DIR, 'static', 'fonts', 'Tajawal-Regular.ttf')
    # If standard font doesn't exist, just use Helvetica and try best
    try:
        if os.path.exists(font_path):
            pdfmetrics.registerFont(TTFont('ArabicFont', font_path))
            c.setFont('ArabicFont', 14)
        else:
            # Try Windows default Arial
            arial_path = 'C:\\Windows\\Fonts\\arial.ttf'
            if os.path.exists(arial_path):
                pdfmetrics.registerFont(TTFont('ArabicFont', arial_path))
                c.setFont('ArabicFont', 14)
            else:
                c.setFont('Helvetica', 14)
    except Exception:
        c.setFont('Helvetica', 14)

    def draw_arabic_text(text, x, y):
        try:
            reshaped_text = arabic_reshaper.reshape(str(text))
            bidi_text = get_display(reshaped_text)
            c.drawRightString(x, y, bidi_text)
        except Exception:
            c.drawRightString(x, y, str(text))

    # Header
    draw_arabic_text("الجمهورية الجزائرية الديمقراطية الشعبية", width / 2 + 100, height - 50)
    draw_arabic_text("محضر فتح الأظرفة وتقييم العروض", width / 2 + 100, height - 100)
    
    # Details
    c.setFontSize(12)
    y = height - 150
    draw_arabic_text(f"عنوان الصفقة: {committee.tender.title}", width - 50, y)
    y -= 30
    draw_arabic_text(f"المصلحة المتعاقدة: {committee.tender.authority.full_name if committee.tender.authority else 'غير محدد'}", width - 50, y)
    y -= 30
    
    # Date formatting
    from django.utils.timezone import localtime
    local_time = localtime(committee.opened_at)
    date_str = local_time.strftime("%Y-%m-%d %H:%M:%S")
    draw_arabic_text(f"تاريخ وساعة الفتح: {date_str}", width - 50, y)
    y -= 30
    
    draw_arabic_text(f"رئيس الجلسة: {committee.opened_by.full_name if committee.opened_by else 'غير محدد'}", width - 50, y)
    y -= 50
    
    # Bids
    draw_arabic_text("العروض المستلمة:", width - 50, y)
    y -= 30
    
    for idx, bid in enumerate(committee.tender.bids.all()):
        draw_arabic_text(f"{idx + 1}. المتعامل: {bid.supplier_name} - العرض المالي: {bid.financial_offer} دج", width - 70, y)
        y -= 20
        
        file_hash = "غير متوفر"
        if bid.financial_document:
            try:
                bid.financial_document.open('rb')
                file_hash = hashlib.sha256(bid.financial_document.read()).hexdigest()
                bid.financial_document.close()
            except Exception:
                pass
                
        c.setFont('Helvetica', 10)
        c.drawString(50, y, f"SHA-256: {file_hash}")
        c.setFont('ArabicFont', 12) if 'ArabicFont' in pdfmetrics.getRegisteredFontNames() else c.setFont('Helvetica', 12)
        y -= 25
        if y < 100:
            c.showPage()
            c.setFont('ArabicFont', 12) if 'ArabicFont' in pdfmetrics.getRegisteredFontNames() else c.setFont('Helvetica', 12)
            y = height - 50

    y -= 20
    draw_arabic_text("ملاحظات اللجنة:", width - 50, y)
    y -= 30
    draw_arabic_text(committee.notes or "لا توجد ملاحظات.", width - 70, y)
    
    y -= 50
    draw_arabic_text("توقيع رئيس الجلسة", width - 100, y)
    
    c.save()
    
    pdf_value = buffer.getvalue()
    buffer.close()
    
    pdf_hash = hashlib.sha256(pdf_value).hexdigest()
    committee.report_hash = pdf_hash
    
    filename = f"opening_report_{committee.id}.pdf"
    committee.report_file.save(filename, ContentFile(pdf_value), save=True)
