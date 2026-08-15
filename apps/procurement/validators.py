import os
import filetype
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

def validate_file_mimetype(file):
    """
    Validate that the uploaded file is a PDF, ZIP, or RAR based on its magic bytes using filetype.
    Prevents malicious uploads masked with fake extensions.
    """
    valid_mime_types = [
        'application/pdf',
        'application/zip',
        'application/x-rar-compressed',
        'application/x-zip-compressed'
    ]
    
    # Read the first 2048 bytes of the file for magic numbers
    file_data = file.read(2048)
    # Reset file pointer after reading
    file.seek(0)
    
    # Detect MIME type
    kind = filetype.guess(file_data)
    
    if kind is None or kind.mime not in valid_mime_types:
        detected_mime = kind.mime if kind else 'unknown'
        raise ValidationError(
            _('نوع الملف غير مدعوم أو أن المحتوى مزور. يُسمح فقط بملفات PDF أو ZIP. (نوع الملف المكتشف: %(mime_type)s)'),
            params={'mime_type': detected_mime},
        )

def validate_file_size(file):
    max_size_mb = 20
    if file.size > max_size_mb * 1024 * 1024:
        raise ValidationError(_(f'حجم الملف يتجاوز الحد الأقصى المسموح به ({max_size_mb}MB).'))
