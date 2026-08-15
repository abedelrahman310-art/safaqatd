import re

with open('d:/mvp2026/project_root/apps/procurement/models.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    'models.FileField(upload_to=secure_upload_path, verbose_name="العرض التقني")',
    'models.FileField(upload_to=secure_upload_path, verbose_name="العرض التقني", validators=[validate_file_mimetype, validate_file_size])'
)
content = content.replace(
    'models.FileField(upload_to=secure_upload_path, verbose_name="العرض المالي")',
    'models.FileField(upload_to=secure_upload_path, verbose_name="العرض المالي", validators=[validate_file_mimetype, validate_file_size])'
)
content = content.replace(
    'document = models.FileField(upload_to=\'tenders/documents/\', null=True, blank=True, verbose_name="دفتر الشروط")',
    'document = models.FileField(upload_to=\'tenders/documents/\', null=True, blank=True, verbose_name="دفتر الشروط", validators=[validate_file_mimetype, validate_file_size])'
)

with open('d:/mvp2026/project_root/apps/procurement/models.py', 'w', encoding='utf-8') as f:
    f.write(content)
