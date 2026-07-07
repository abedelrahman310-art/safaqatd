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
            login(request, user)
            if user.role == 'authority':
                return redirect('dashboard:authority')
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

from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from .models import QRLoginSession
import qrcode
import base64
from io import BytesIO
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

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

# ==========================================
# QR CODE LOGIN SYSTEM
# ==========================================

def qr_login_page(request):
    """Generates a QR code on the desktop screen."""
    # Create a new QR session token
    qr_session = QRLoginSession.objects.create()
    
    # Generate QR Code pointing to the authorize URL
    auth_url = request.build_absolute_uri(f'/accounts/qr-login/authorize/{qr_session.token}/')
    
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(auth_url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    qr_image = base64.b64encode(buffer.getvalue()).decode()
    
    context = {
        'qr_image': qr_image,
        'token': qr_session.token,
    }
    return render(request, 'accounts/qr_login.html', context)

def qr_login_status(request, token):
    """AJAX endpoint polled by the desktop to check if the phone approved the login."""
    try:
        qr_session = QRLoginSession.objects.get(token=token)
        if qr_session.is_approved and qr_session.user:
            # The phone approved it! Log the desktop user in.
            login(request, qr_session.user, backend='django.contrib.auth.backends.ModelBackend')
            
            from django.urls import reverse
            if qr_session.user.role == 'authority':
                redirect_url = reverse('dashboard:authority')
            else:
                redirect_url = reverse('dashboard:supplier')
                
            return JsonResponse({'status': 'approved', 'redirect_url': redirect_url})
        return JsonResponse({'status': 'pending'})
    except QRLoginSession.DoesNotExist:
        return JsonResponse({'status': 'expired'})

@login_required
def qr_login_authorize(request, token):
    """The page that opens on the phone when the QR is scanned."""
    try:
        qr_session = QRLoginSession.objects.get(token=token)
        if qr_session.is_approved:
            return render(request, 'accounts/qr_authorize.html', {'status': 'already_approved'})
            
        context = {
            'token': token,
            'status': 'pending'
        }
        return render(request, 'accounts/qr_authorize.html', context)
    except QRLoginSession.DoesNotExist:
        return render(request, 'accounts/qr_authorize.html', {'status': 'invalid'})

@login_required
@csrf_exempt
def qr_login_process(request, token):
    """The backend action triggered when the user clicks 'Approve' on their phone."""
    if request.method == 'POST':
        try:
            qr_session = QRLoginSession.objects.get(token=token)
            if not qr_session.is_approved:
                qr_session.user = request.user
                qr_session.is_approved = True
                qr_session.save()
            return JsonResponse({'success': True})
        except QRLoginSession.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Invalid token'})
    return JsonResponse({'success': False})
