from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required

User = get_user_model()

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('username')
        password = request.POST.get('password')
        role = request.POST.get('role')
        
        try:
            user_obj = User.objects.get(email=email)
            user = authenticate(request, username=user_obj.username, password=password)
        except User.DoesNotExist:
            user = None
            
        if user is not None:
            if getattr(user, 'is_blacklisted', False):
                from django.utils import timezone
                if not user.blacklist_until or user.blacklist_until > timezone.now():
                    error_msg = f"عذراً، تم حظر حسابك. السبب: {user.blacklist_reason or 'مخالفة الشروط'}"
                    if user.blacklist_until:
                        error_msg += f" (يستمر الحظر حتى {user.blacklist_until.strftime('%Y/%m/%d')})"
                    messages.error(request, error_msg)
                    return render(request, 'accounts/login.html')
                    
            login(request, user)
            if user.role == 'authority':
                return redirect('dashboard:authority')
            elif user.has_perm('accounts.view_central_dashboard'):
                return redirect('dashboard:regulator')
            else:
                return redirect('dashboard:supplier')
        else:
            messages.error(request, 'البريد الإلكتروني أو كلمة المرور غير صحيحة.')
            
    return render(request, 'accounts/login.html')

def register_supplier_view(request):
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password_confirm = request.POST.get('confirm_password')
        
        if password != password_confirm:
            messages.error(request, 'كلمات المرور غير متطابقة')
            return render(request, 'accounts/register_supplier.html')
            
        if User.objects.filter(email=email).exists():
            messages.error(request, 'هذا البريد الإلكتروني مسجل مسبقاً')
            return render(request, 'accounts/register_supplier.html')
            
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            role='supplier',
            full_name=full_name,
        )
        
        user.national_id = request.POST.get('national_id')
        user.commercial_register = request.POST.get('commercial_register')
        user.company_type = request.POST.get('company_type')
        user.sector = request.POST.get('sector')
        user.save()
        
        login(request, user)
        return redirect('dashboard:supplier')

    return render(request, 'accounts/register_supplier.html')

def register_authority_view(request):
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password_confirm = request.POST.get('confirm_password')
        
        if password != password_confirm:
            messages.error(request, 'كلمات المرور غير متطابقة')
            return render(request, 'accounts/register_authority.html')
            
        if User.objects.filter(email=email).exists():
            messages.error(request, 'هذا البريد الإلكتروني مسجل مسبقاً')
            return render(request, 'accounts/register_authority.html')
            
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            role='authority',
            full_name=full_name,
        )
        
        user.institution_name = request.POST.get('institution_name')
        user.tax_id = request.POST.get('tax_id')
        user.sector = request.POST.get('sector')
        user.save()
        
        login(request, user)
        return redirect('dashboard:authority')

    return render(request, 'accounts/register_authority.html')

def logout_view(request):
    logout(request)
    return redirect('core:index')

@login_required
def profile_view(request):
    if request.method == 'POST':
        user = request.user
        user.full_name = request.POST.get('full_name', user.full_name)
        user.wilaya = request.POST.get('wilaya', user.wilaya)
        user.company_type = request.POST.get('company_type', user.company_type)
        user.commercial_register = request.POST.get('commercial_register', user.commercial_register)
        user.national_id = request.POST.get('national_id', user.national_id)
        user.save()
        messages.success(request, "تم تحديث الملف الشخصي بنجاح!")
    return render(request, 'accounts/profile.html')

@login_required
def manage_blacklist(request):
    if request.user.role != 'authority':
        return redirect('dashboard:supplier')
        
    if request.method == 'POST':
        supplier_id = request.POST.get('supplier_id')
        action = request.POST.get('action')
        
        try:
            supplier = User.objects.get(id=supplier_id, role='supplier')
            if action == 'blacklist':
                supplier.is_blacklisted = True
                messages.success(request, f"تم إضافة {supplier.full_name} إلى القائمة السوداء بنجاح.")
            elif action == 'whitelist':
                supplier.is_blacklisted = False
                messages.success(request, f"تم إزالة {supplier.full_name} من القائمة السوداء بنجاح.")
            supplier.save()
        except User.DoesNotExist:
            messages.error(request, "لم يتم العثور على المتعامل.")
            
        return redirect('accounts:manage_blacklist')
        
    suppliers = User.objects.filter(role='supplier').order_by('full_name')
    return render(request, 'accounts/manage_blacklist.html', {'suppliers': suppliers})

from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm

@login_required
def settings_view(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important to keep the user logged in
            messages.success(request, 'تم تغيير كلمة المرور بنجاح!')
            return redirect('accounts:settings')
        else:
            messages.error(request, 'يرجى تصحيح الأخطاء أدناه.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'accounts/settings.html', {'form': form})
