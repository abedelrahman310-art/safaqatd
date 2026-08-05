import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from apps.procurement.models import Tender, Bid

@login_required
@permission_required('accounts.view_central_dashboard', raise_exception=True)
def regulator_dashboard(request):
    total_tenders = Tender.objects.count()
    total_bids = Bid.objects.count()
    total_users = get_user_model().objects.count()
    active_suppliers = get_user_model().objects.filter(role='supplier').count()
    
    tenders_by_wilaya = {}
    for t in Tender.objects.all():
        w = t.wilaya
        tenders_by_wilaya[w] = tenders_by_wilaya.get(w, 0) + 1
        
    context = {
        'total_tenders': total_tenders,
        'total_bids': total_bids,
        'total_users': total_users,
        'active_suppliers': active_suppliers,
        'tenders_by_wilaya': json.dumps(tenders_by_wilaya),
    }
    return render(request, 'dashboard/regulator_dashboard.html', context)

@login_required
@permission_required('accounts.manage_all_users', raise_exception=True)
def regulator_users_list(request):
    User = get_user_model()
    # Exclude superusers and the current regulator from the list to prevent accidental self-ban
    users = User.objects.exclude(is_superuser=True).exclude(id=request.user.id).order_by('-date_joined')
    
    return render(request, 'dashboard/regulator_users.html', {'users': users})

@login_required
@permission_required('accounts.manage_all_users', raise_exception=True)
def toggle_user_status(request, user_id):
    if request.method == 'POST':
        User = get_user_model()
        target_user = get_object_or_404(User, id=user_id)
        
        # Prevent banning superusers or oneself
        if target_user.is_superuser or target_user == request.user:
            messages.error(request, 'لا يمكن تعديل حالة هذا المستخدم.')
        else:
            target_user.is_active = not target_user.is_active
            target_user.save()
            status_msg = "تم تفعيل" if target_user.is_active else "تم حظر"
            messages.success(request, f'{status_msg} حساب {target_user.get_full_name() or target_user.username} بنجاح.')
            
    return redirect('dashboard:regulator_users')

@login_required
@permission_required('accounts.audit_all_tenders', raise_exception=True)
def regulator_audit_list(request):
    tenders = Tender.objects.all().order_by('-created_at')
    return render(request, 'dashboard/regulator_audit.html', {'tenders': tenders})
