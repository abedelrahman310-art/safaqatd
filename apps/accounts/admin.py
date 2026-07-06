from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ['email', 'username', 'role', 'full_name', 'wilaya', 'is_staff']
    fieldsets = UserAdmin.fieldsets + (
        ('معلومات إضافية', {'fields': ('role', 'full_name', 'wilaya')}),
        ('معلومات المتعامل الاقتصادي', {'fields': ('national_id', 'commercial_register', 'company_type')}),
        ('معلومات المصلحة المتعاقدة', {'fields': ('institution_name', 'sector')}),
    )

admin.site.register(User, CustomUserAdmin)
