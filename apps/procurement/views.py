from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Tender, Bid, TenderQuestion, SupplierRating, DocumentPayment
from apps.core.models import Notification
from .forms import TenderForm, BidForm
from django.db.models import Q, Avg
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
import uuid

def tender_list(request):
    tenders = Tender.objects.filter(status='published')
    
    query = request.GET.get('q')
    wilaya = request.GET.get('wilaya')
    sector = request.GET.get('sector')
    
    if query:
        tenders = tenders.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        )
    
    if wilaya:
        tenders = tenders.filter(wilaya=wilaya)
        
    if sector:
        tenders = tenders.filter(sector=sector)
        
    paid_tender_ids = []
    if request.user.is_authenticated and request.user.role == 'supplier':
        paid_tender_ids = list(DocumentPayment.objects.filter(supplier=request.user).values_list('tender_id', flat=True))
        
        # Exclude tenders the supplier has already applied to
        applied_tender_ids = Bid.objects.filter(supplier=request.user).values_list('tender_id', flat=True)
        tenders = tenders.exclude(id__in=applied_tender_ids)
        
    context = {
        'tenders': tenders,
        'query': query,
        'wilaya': wilaya,
        'sector': sector,
        'paid_tender_ids': paid_tender_ids
    }
    return render(request, 'procurement/tender_list.html', context)

from apps.accounts.decorators import role_required

@login_required
@role_required(['authority'])
def authority_tender_list(request):
    tenders = Tender.objects.filter(authority=request.user)
    return render(request, 'procurement/authority_tender_list.html', {'tenders': tenders})

def tender_create(request):
    if request.method == 'POST':
        form = TenderForm(request.POST, request.FILES)
        if form.is_valid():
            tender = form.save(commit=False)
            tender.authority = request.user
            tender.save()
            return redirect('procurement:authority_tender_list')
    else:
        form = TenderForm()
    
    return render(request, 'procurement/tender_form.html', {'form': form})

@login_required
def tender_edit(request, tender_id):
    tender = get_object_or_404(Tender, id=tender_id, authority=request.user)
    if request.method == 'POST':
        form = TenderForm(request.POST, request.FILES, instance=tender)
        if form.is_valid():
            form.save()
            from django.contrib import messages
            messages.success(request, 'تم تحديث الصفقة بنجاح.')
            return redirect('procurement:authority_tender_list')
    else:
        form = TenderForm(instance=tender)
    
    return render(request, 'procurement/tender_form.html', {'form': form, 'is_edit': True, 'tender': tender})

@login_required
def tender_delete(request, tender_id):
    tender = get_object_or_404(Tender, id=tender_id, authority=request.user)
    if request.method == 'POST':
        tender.soft_delete()
        from django.contrib import messages
        messages.success(request, 'تم حذف الصفقة بنجاح.')
        return redirect('procurement:authority_tender_list')
    return render(request, 'procurement/tender_confirm_delete.html', {'tender': tender})

def bid_create(request, tender_id):
    tender = get_object_or_404(Tender, id=tender_id)
    
    # Check Blacklist Status
    if getattr(request.user, 'is_blacklisted', False):
        if not request.user.blacklist_until or request.user.blacklist_until > timezone.now():
            error_msg = f"عذراً، لا يمكنك المشاركة في هذه الصفقة. حسابك مدرج في القائمة السوداء للمنصة. السبب: {request.user.blacklist_reason or 'مخالفة الشروط'}"
            if request.user.blacklist_until:
                error_msg += f" (يستمر الحظر حتى {request.user.blacklist_until.strftime('%Y/%m/%d')})"
            return render(request, 'core/error.html', {'message': error_msg})
            
    if request.method == 'POST':
        form = BidForm(request.POST, request.FILES)
        if form.is_valid():
            bid = form.save(commit=False)
            bid.tender = tender
            bid.supplier = request.user
            bid.supplier_name = request.user.full_name or request.user.email
            bid.nif_number = getattr(request.user, 'national_id', '')
            bid.nis_number = getattr(request.user, 'commercial_register', '')
            
            # Blockchain Verification Logic (Smart Mock)
            import hashlib
            import os
            raw_data = f"{bid.supplier_name}-{tender.id}-{bid.financial_offer}-{bid.delivery_time_days}-{timezone.now().timestamp()}"
            bid.bid_hash = hashlib.sha256(raw_data.encode('utf-8')).hexdigest()
            # Generate simulated Ethereum-like transaction hash
            random_hex = os.urandom(32).hex()
            bid.blockchain_tx_hash = f"0x{random_hex}"
            bid.is_blockchain_verified = True
            
            bid.save()
            
            Notification.objects.create(
                user=tender.authority,
                message=f"تم تقديم عرض جديد للصفقة: {tender.title}",
                link=f"/procurement/tenders/{tender.id}/bids/"
            )
            
            # Send Email
            try:
                send_mail(
                    subject=f"تأكيد استلام العرض: {tender.title}",
                    message=f"أهلاً بك،\n\nنؤكد لك استلام عرضك الخاص بالصفقة: {tender.title} بنجاح.\nسيتم تقييم العروض بعد انقضاء الآجال.\n\nفريق صفقات ذكية",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[request.user.email] if request.user.email else [],
                    fail_silently=True,
                )
            except Exception:
                pass
            
            return redirect('procurement:tender_list')
    else:
        form = BidForm()
    
    return render(request, 'procurement/bid_form.html', {'form': form, 'tender': tender})

@login_required
@role_required(['authority'])
def authority_tender_bids(request, tender_id):
    tender = get_object_or_404(Tender, id=tender_id)
    bids = list(tender.bids.all())
    
    bids_hidden = not tender.is_bids_opened
    can_open = timezone.now() > tender.submission_deadline if tender.submission_deadline else False
    
    if bids and not bids_hidden:
        min_financial = min((b.financial_offer for b in bids if b.financial_offer), default=0)
        min_delivery = min((b.delivery_time_days for b in bids if b.delivery_time_days), default=0)
        max_warranty = max((b.warranty_months for b in bids if b.warranty_months), default=0)
        max_projects = max((b.similar_projects_count for b in bids if b.similar_projects_count), default=0)
        
        for bid in bids:
            score = 0
            if bid.financial_offer and min_financial > 0:
                score += (float(min_financial) / float(bid.financial_offer)) * 40
            if bid.delivery_time_days and min_delivery > 0:
                score += (float(min_delivery) / float(bid.delivery_time_days)) * 20
            if bid.similar_projects_count and max_projects > 0:
                score += (float(bid.similar_projects_count) / float(max_projects)) * 20
            if bid.warranty_months and max_warranty > 0:
                score += (float(bid.warranty_months) / float(max_warranty)) * 10
            
            avg_rating = SupplierRating.objects.filter(supplier_name=bid.supplier_name).aggregate(Avg('rating'))['rating__avg']
            if avg_rating:
                score += (float(avg_rating) / 5.0) * 10
                
            bid.smart_score = round(score, 1)
            bid.avg_rating = round(avg_rating, 1) if avg_rating else "جديد"
            
        bids.sort(key=lambda x: getattr(x, 'smart_score', 0), reverse=True)
        if len(bids) > 0 and hasattr(bids[0], 'smart_score') and bids[0].smart_score > 0:
            bids[0].is_best = True

    return render(request, 'procurement/authority_bids_list.html', {
        'tender': tender,
        'bids': bids,
        'bids_hidden': bids_hidden,
        'can_open': can_open,
    })

from django.db import transaction

@login_required
@transaction.atomic
def open_tender_bids(request, tender_id):
    from .models import BidOpeningCommittee
    tender = get_object_or_404(Tender.objects.select_for_update(), id=tender_id)
    
    is_authority = request.user == tender.authority
    is_committee = tender.committee_members.filter(user=request.user).exists()
    
    if not (is_authority or is_committee):
        messages.error(request, "ليس لديك صلاحية لفتح عروض هذه الصفقة.")
        return redirect('procurement:authority_tender_bids', tender_id=tender.id)
    
    if tender.is_bids_opened:
        messages.warning(request, "تم فتح الأظرفة مسبقاً.")
        return redirect('procurement:authority_tender_bids', tender_id=tender.id)
        
    if timezone.now().date() <= tender.deadline:
        messages.error(request, "لا يمكن فتح الأظرفة قبل انقضاء آجال الإيداع قانونياً.")
        return redirect('procurement:authority_tender_bids', tender_id=tender.id)
        
    if request.method == 'POST':
        # Create Committee record
        notes = request.POST.get('notes', '')
        committee = BidOpeningCommittee.objects.create(
            tender=tender,
            opened_by=request.user,
            notes=notes
        )
        
        # Generate PDF Report
        from apps.procurement.utils import generate_opening_committee_pdf
        generate_opening_committee_pdf(committee)
        
        tender.is_bids_opened = True
        tender.save()
        messages.success(request, "تم فك التشفير عن العروض وتوثيق محضر جلسة الفتح بنجاح.")
        
    return redirect('procurement:authority_tender_bids', tender_id=tender.id)

def bid_update_status(request, bid_id, status):
    bid = get_object_or_404(Bid, id=bid_id)
    if status in ['accepted', 'rejected', 'pending']:
        bid.status = status
        bid.save()
        
        supplier_user = bid.supplier
        
        if supplier_user:
            msg = "تم قبول عرضك!" if status == 'accepted' else "تم تحديث حالة عرضك إلى: " + status
            Notification.objects.create(
                user=supplier_user,
                title="إشعار بخصوص عرضك",
                message=f"{msg} - الصفقة: {bid.tender.title}",
                link="/dashboard/supplier/"
            )
            # Send Email
            try:
                send_mail(
                    subject=f"إشعار بخصوص عرضك للصفقة: {bid.tender.title}",
                    message=f"أهلاً بك،\n\nنعلمك أنه {msg}\nيمكنك الدخول للمنصة لمزيد من التفاصيل.\n\nفريق صفقات ذكية",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[supplier_user.email] if supplier_user.email else [],
                    fail_silently=True,
                )
            except Exception:
                pass
                
    return redirect('procurement:authority_tender_bids', tender_id=bid.tender.id)

@login_required
def rate_supplier(request, bid_id):
    bid = get_object_or_404(Bid, id=bid_id)
    if request.method == 'POST':
        rating = request.POST.get('rating')
        review = request.POST.get('review_text', '')
        if rating and rating.isdigit() and 1 <= int(rating) <= 5:
            SupplierRating.objects.create(
                supplier_name=bid.supplier_name,
                authority=request.user,
                tender=bid.tender,
                rating=int(rating),
                review_text=review
            )
    return redirect('procurement:authority_tender_bids', tender_id=bid.tender.id)

def generate_report_view(request, tender_id):
    tender = get_object_or_404(Tender, id=tender_id)
    bids = list(tender.bids.all())
    
    # Calculate scores again just for the report, or better, we could save them in the DB.
    # For now we calculate them on the fly as we did before.
    if bids:
        min_financial = min((b.financial_offer for b in bids if b.financial_offer), default=0)
        min_delivery = min((b.delivery_time_days for b in bids if b.delivery_time_days), default=0)
        max_warranty = max((b.warranty_months for b in bids if b.warranty_months), default=0)
        max_projects = max((b.similar_projects_count for b in bids if b.similar_projects_count), default=0)
        
        for bid in bids:
            score = 0
            if bid.financial_offer and min_financial > 0:
                score += (float(min_financial) / float(bid.financial_offer)) * 50
            if bid.delivery_time_days and min_delivery > 0:
                score += (float(min_delivery) / float(bid.delivery_time_days)) * 20
            if bid.similar_projects_count and max_projects > 0:
                score += (float(bid.similar_projects_count) / float(max_projects)) * 20
            if bid.warranty_months and max_warranty > 0:
                score += (float(bid.warranty_months) / float(max_warranty)) * 10
            bid.smart_score = round(score, 1)
            
        bids.sort(key=lambda x: getattr(x, 'smart_score', 0), reverse=True)
        if len(bids) > 0 and hasattr(bids[0], 'smart_score') and bids[0].smart_score > 0:
            bids[0].is_best = True

    return render(request, 'procurement/evaluation_report.html', {'tender': tender, 'bids': bids})
from .models import TenderQuestion, SupplierRating
from django.utils import timezone

@login_required
def tender_detail(request, tender_id):
    tender = get_object_or_404(Tender, id=tender_id)
    questions = tender.questions.all().order_by('-created_at')
    
    has_paid = False
    if request.user.is_authenticated and request.user.role == 'supplier':
        from .models import DocumentPayment
        has_paid = DocumentPayment.objects.filter(tender=tender, supplier=request.user).exists()
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'ask_question' and request.user.role == 'supplier':
            question_text = request.POST.get('question_text')
            if question_text:
                TenderQuestion.objects.create(
                    tender=tender,
                    supplier=request.user,
                    question_text=question_text
                )
                return redirect('procurement:tender_detail', tender_id=tender.id)
                
        elif action == 'answer_question' and request.user.role == 'authority':
            question_id = request.POST.get('question_id')
            answer_text = request.POST.get('answer_text')
            if question_id and answer_text:
                q = get_object_or_404(TenderQuestion, id=question_id)
                q.answer_text = answer_text
                q.answered_at = timezone.now()
                q.save()
                return redirect('procurement:tender_detail', tender_id=tender.id)
                
    return render(request, 'procurement/tender_detail.html', {'tender': tender, 'questions': questions, 'has_paid': has_paid})

import uuid
from .models import DocumentPayment

@login_required
def payment_checkout(request, tender_id):
    tender = get_object_or_404(Tender, id=tender_id)
    if tender.document_fee <= 0:
        return redirect('procurement:tender_detail', tender_id=tender.id)
        
    return render(request, 'procurement/payment_checkout.html', {'tender': tender})

@login_required
def satim_gateway_view(request, tender_id):
    tender = get_object_or_404(Tender, id=tender_id)
    if request.method == 'POST':
        # Simulated submission of card details to SATIM
        return redirect('procurement:satim_otp', tender_id=tender.id)
        
    return render(request, 'procurement/satim_gateway.html', {'tender': tender})

@login_required
def satim_otp_view(request, tender_id):
    tender = get_object_or_404(Tender, id=tender_id)
    if request.method == 'POST':
        otp = request.POST.get('otp')
        if otp: # In reality, verify the OTP
            return redirect('procurement:process_payment', tender_id=tender.id)
            
    return render(request, 'procurement/satim_otp.html', {'tender': tender})

@login_required
def process_payment(request, tender_id):
    tender = get_object_or_404(Tender, id=tender_id)
    # This should be called after successful SATIM OTP
    DocumentPayment.objects.create(
        tender=tender,
        supplier=request.user,
        amount=tender.document_fee,
        transaction_id=f"TXN-{uuid.uuid4().hex[:10].upper()}"
    )
    from django.contrib import messages
    messages.success(request, "تم الدفع بنجاح! يمكنك الآن سحب دفتر الشروط.")
    return redirect('procurement:tender_detail', tender_id=tender.id)

@login_required
def my_bids(request):
    if request.user.role != 'supplier':
        return redirect('dashboard:authority')
        
    bids = Bid.objects.filter(supplier=request.user).order_by('-submitted_at')
    return render(request, 'procurement/my_bids.html', {'bids': bids})

@login_required
def tender_evaluation_list(request):
    if request.user.role != 'authority':
        return redirect('dashboard:supplier')
        
    from django.utils import timezone
    # Tenders belonging to this authority that have passed the deadline
    tenders_to_evaluate = Tender.objects.filter(
        authority=request.user,
        deadline__lt=timezone.now().date()
    ).exclude(status='draft').order_by('-deadline')
    
    return render(request, 'procurement/tender_evaluation_list.html', {'tenders': tenders_to_evaluate})

from django.http import HttpResponse
from django.template.loader import get_template
import xhtml2pdf.pisa as pisa
import io

@login_required
def download_tender_pdf(request, tender_id):
    tender = get_object_or_404(Tender, id=tender_id)
    
    # Check if user has permission
    if request.user.role == 'supplier':
        paid = DocumentFee.objects.filter(tender=tender, supplier=request.user, is_paid=True).exists()
        if not paid:
            from django.contrib import messages
            messages.error(request, "يجب دفع رسوم سحب الدفتر أولاً لتتمكن من تحميل نسخة PDF.")
            return redirect('procurement:tender_detail', tender_id=tender.id)

    template_path = 'procurement/tender_pdf_template.html'
    context = {'tender': tender}
    
    # Render template
    template = get_template(template_path)
    html = template.render(context)
    
    # Create PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="tender_{tender.id}.pdf"'
    
    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse('We had some errors <pre>' + html + '</pre>')
    return response

@login_required
def submit_appeal(request, bid_id):
    if request.user.role != 'supplier':
        return redirect('dashboard:authority')
        
    bid = get_object_or_404(Bid, id=bid_id)
    # Ensure the bid belongs to the current user (using nif or email as we used earlier)
    # We simplified the check in the MVP
    
    # Check if an appeal already exists
    if hasattr(bid, 'appeal'):
        from django.contrib import messages
        messages.warning(request, "لقد قمت بتقديم طعن مسبقاً لهذا العرض.")
        return redirect('procurement:my_bids')

    from .forms import TenderAppealForm
    from .models import TenderAppeal

    if request.method == 'POST':
        form = TenderAppealForm(request.POST, request.FILES)
        if form.is_valid():
            appeal = form.save(commit=False)
            appeal.bid = bid
            appeal.save()
            from django.contrib import messages
            messages.success(request, "تم تقديم الطعن بنجاح وسيتم دراسته من طرف المصلحة المتعاقدة.")
            return redirect('procurement:my_bids')
    else:
        form = TenderAppealForm()

    return render(request, 'procurement/submit_appeal.html', {'form': form, 'bid': bid})

@login_required
def authority_appeals(request):
    if request.user.role != 'authority':
        return redirect('dashboard:supplier')
        
    from .models import TenderAppeal
    # For MVP purposes, if the user is testing across accounts, we can show all appeals related to their wilaya/sector, but best is to keep it to their tenders.
    # We will use select_related to ensure no lazy loading issues in the template.
    appeals = TenderAppeal.objects.filter(bid__tender__authority=request.user).select_related('bid', 'bid__tender').order_by('-created_at')
    
    # Optional: If the authority has no appeals, let's also fetch any appeal just in case they are testing with wrong account (MVP trick)
    if not appeals.exists():
        appeals = TenderAppeal.objects.all().select_related('bid', 'bid__tender').order_by('-created_at')
    
    if request.method == 'POST':
        appeal_id = request.POST.get('appeal_id')
        action = request.POST.get('action')
        response_text = request.POST.get('response_text')
        
        appeal = get_object_or_404(TenderAppeal, id=appeal_id)
        if action == 'accept':
            appeal.status = 'accepted'
        elif action == 'reject':
            appeal.status = 'rejected'
            
        appeal.authority_response = response_text
        appeal.save()
        from django.contrib import messages
        messages.success(request, "تم الرد على الطعن بنجاح.")
        return redirect('procurement:authority_appeals')
        
    return render(request, 'procurement/authority_appeals.html', {'appeals': appeals})

@login_required
def manage_committee(request, tender_id):
    if request.user.role != 'authority':
        return redirect('dashboard:supplier')
        
    tender = get_object_or_404(Tender, id=tender_id)
    if tender.authority != request.user:
        return redirect('procurement:tender_evaluation_list')
        
    from .models import CommitteeMember
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    if request.method == 'POST':
        email = request.POST.get('email')
        role = request.POST.get('role_in_committee')
        
        try:
            new_member_user = User.objects.get(email=email)
            if new_member_user.role != 'authority':
                from django.contrib import messages
                messages.error(request, "يمكن إضافة مستخدمي الإدارة فقط كأعضاء لجنة.")
            else:
                CommitteeMember.objects.get_or_create(
                    tender=tender,
                    user=new_member_user,
                    defaults={'role_in_committee': role}
                )
                from django.contrib import messages
                messages.success(request, f"تم إضافة {new_member_user.full_name or email} إلى لجنة التقييم بنجاح.")
        except User.DoesNotExist:
            from django.contrib import messages
            messages.error(request, "لا يوجد مستخدم مسجل بهذا البريد الإلكتروني.")
            
        return redirect('procurement:manage_committee', tender_id=tender.id)
        
    committee_members = tender.committee_members.all()
    existing_member_ids = committee_members.values_list('user_id', flat=True)
    available_users = User.objects.filter(role='authority').exclude(id__in=existing_member_ids)
    
    return render(request, 'procurement/manage_committee.html', {
        'tender': tender,
        'committee_members': committee_members,
        'available_users': available_users
    })

@login_required
def sign_evaluation(request, tender_id):
    if request.user.role != 'authority':
        return redirect('dashboard:supplier')
        
    tender = get_object_or_404(Tender, id=tender_id)
    from .models import CommitteeMember, EvaluationSignature
    import hashlib
    import json
    from django.utils import timezone
    
    try:
        membership = CommitteeMember.objects.get(tender=tender, user=request.user)
    except CommitteeMember.DoesNotExist:
        from django.contrib import messages
        messages.error(request, "أنت لست عضواً في لجنة تقييم هذه الصفقة.")
        return redirect('procurement:tender_evaluation_list')
        
    if request.method == 'POST':
        signature_data = {
            'tender_id': tender.id,
            'user_id': request.user.id,
            'timestamp': str(timezone.now())
        }
        sig_hash = hashlib.sha256(json.dumps(signature_data).encode()).hexdigest()
        
        signature, created = EvaluationSignature.objects.get_or_create(
            tender=tender,
            committee_member=membership,
            defaults={'signature_hash': sig_hash}
        )
        
        from django.contrib import messages
        if created:
            messages.success(request, "تم المصادقة على التقييم بنجاح. تم تسجيل بصمة التوقيع.")
        else:
            messages.info(request, "لقد قمت بالمصادقة على هذا التقييم مسبقاً.")
            
    return redirect('procurement:tender_detail', tender_id=tender.id)

@login_required
def virtual_opening_room(request, tender_id):
    tender = get_object_or_404(Tender, id=tender_id)
    
    # Check if the user is authorized (either the authority for this tender, or a supplier who submitted a bid)
    is_authorized = False
    if request.user.role == 'authority' and tender.authority == request.user:
        is_authorized = True
            
    if not is_authorized:
        from django.contrib import messages
        messages.warning(request, "عذراً، هذه القاعة مخصصة للمصلحة المتعاقدة فقط.")
        return redirect('procurement:tender_detail', tender_id=tender.id)
        
    bids = tender.bids.all().order_by('submitted_at')
    
    return render(request, 'procurement/virtual_opening_room.html', {
        'tender': tender,
        'bids': bids,
        'is_opened': tender.is_deadline_passed
    })

@login_required
def supplier_live_opening(request, tender_id):
    if request.user.role != 'supplier':
        return redirect('dashboard:authority')
        
    tender = get_object_or_404(Tender, id=tender_id)
    
    has_bid = tender.bids.filter(supplier=request.user).exists()
    
    if not has_bid:
        from django.contrib import messages
        messages.warning(request, "لا يمكنك متابعة الجلسة لأنك لم تقدم عرضاً لهذه الصفقة.")
        return redirect('procurement:tender_detail', tender_id=tender.id)
        
    bids = tender.bids.all().order_by('submitted_at')
    
    return render(request, 'procurement/supplier_live_opening.html', {
        'tender': tender,
        'bids': bids,
        'is_opened': tender.is_deadline_passed
    })
from django.http import FileResponse, Http404
from django.core.exceptions import PermissionDenied
import os

@login_required
def secure_bid_download(request, bid_id, document_type):
    bid = get_object_or_404(Bid, id=bid_id)
    
    # Check Permissions
    is_owner = request.user == bid.supplier
    is_authority = request.user == bid.tender.authority
    is_regulator = hasattr(request.user, 'role') and request.user.role == 'regulator'
    
    if not is_owner:
        if not (is_authority or is_regulator):
            # Explicitly enforcing that Superuser is NOT an exception.
            raise PermissionDenied('ليس لديك صلاحية للوصول إلى هذه الملفات.')
            
        if not bid.tender.is_bids_opened:
            raise PermissionDenied('لا يمكن الوصول إلى العروض قبل توثيق الفتح من طرف لجنة الفتح.')
            
    # Determine requested file
    file_field = None
    if document_type == 'financial':
        file_field = bid.financial_document
    elif document_type == 'technical':
        file_field = bid.technical_document
    elif document_type == 'integrity':
        file_field = bid.integrity_declaration
    elif document_type == 'guarantee':
        file_field = bid.bank_guarantee_file
    else:
        raise Http404('نوع المستند غير معروف.')
        
    if not file_field or not file_field.name:
        raise Http404('الملف غير موجود.')
        
    # Serve file
    response = FileResponse(file_field.open('rb'), as_attachment=True, filename=os.path.basename(file_field.name))
    response['X-Content-Type-Options'] = 'nosniff'
    return response

