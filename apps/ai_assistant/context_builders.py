from django.utils import timezone
from apps.procurement.models import Tender, Bid
from apps.accounts.models import User

def build_central_admin_context(user):
    total_tenders = Tender.objects.count()
    active_tenders = Tender.objects.filter(status__in=['published', 'evaluating']).count()
    total_users = User.objects.count()
    total_suppliers = User.objects.filter(role='supplier').count()
    total_authorities = User.objects.filter(role='authority').count()
    
    return {
        "role_type": "central_admin",
        "role_context": "أنت تتحدث مع مدير مركزي (Central Admin). يجب عليك التركيز على الرقابة، والإحصائيات العامة، وسير العمليات في المنصة.",
        "data": {
            "إجمالي الصفقات في النظام": total_tenders,
            "الصلفقات النشطة (منشورة أو قيد التقييم)": active_tenders,
            "إجمالي المستخدمين": total_users,
            "عدد الموردين المسجلين": total_suppliers,
            "عدد المصالح المتعاقدة": total_authorities,
        }
    }

def build_authority_context(user):
    my_tenders = Tender.objects.filter(authority=user)
    total_my_tenders = my_tenders.count()
    draft_tenders = my_tenders.filter(status='draft').count()
    published_tenders = my_tenders.filter(status='published').count()
    
    # Bids for my tenders
    my_bids_count = Bid.objects.filter(tender__authority=user).count()
    
    return {
        "role_type": "authority",
        "role_context": f"أنت تتحدث مع ممثل لمصلحة متعاقدة ({user.display_name}). ركز على إدارة صفقاتهم، تقييم العروض، والمحاضر.",
        "data": {
            "إجمالي صفقاتي": total_my_tenders,
            "صفقاتي في وضع المسودة": draft_tenders,
            "صفقاتي المنشورة حالياً": published_tenders,
            "إجمالي العروض المستلمة لصفقاتي": my_bids_count,
        }
    }

def build_supplier_context(user):
    my_bids = Bid.objects.filter(supplier=user)
    total_my_bids = my_bids.count()
    accepted_bids = my_bids.filter(status='accepted').count()
    
    active_tenders = Tender.objects.filter(status='published')
    matching_opportunities = []
    
    if user.sector:
        matching_qs = active_tenders.filter(sector=user.sector)
    else:
        matching_qs = active_tenders.all()
        
    for t in matching_qs[:5]:
        matching_opportunities.append({
            "reference": str(t.id),
            "title": t.title,
            "authority": t.authority.display_name if t.authority else "غير محدد",
            "sector": t.sector or "غير محدد",
            "deadline": str(t.deadline),
            "estimated_competition": Bid.objects.filter(tender=t).count(),
            "required_documents": "دفتر الشروط، العرض المالي، العرض التقني، التصريح بالنزاهة",
            "eligibility_notes": "مؤهل مبدئياً" if not user.is_blacklisted else "ممنوع من المشاركة (قائمة سوداء)"
        })

    # Missing vs Available docs based on user model
    available_docs = []
    missing_docs = []
    if user.commercial_register_doc: available_docs.append("السجل التجاري")
    else: missing_docs.append("السجل التجاري")
    if user.tax_card_doc: available_docs.append("البطاقة الجبائية")
    else: missing_docs.append("البطاقة الجبائية")

    return {
        "role_type": "supplier",
        "role_context": f"أنت تتحدث مع متعامل اقتصادي/مورد ({user.display_name}). ركز على تقديم العروض، فرص المناقصات، والشفافية. القطاع الخاص به هو: {user.sector or 'غير محدد'}.",
        "data": {
            "supplier_profile": {
                "name": user.display_name,
                "business_activity": user.company_type or "غير محدد",
                "sectors": [user.sector] if user.sector else [],
                "qualifications": "معتمد" if user.commercial_register else "قيد الاعتماد",
                "wilayas": [user.wilaya] if user.wilaya else [],
                "previous_bids_count": total_my_bids,
                "previous_wins_count": accepted_bids,
                "completion_rate": f"{int((accepted_bids/total_my_bids)*100)}%" if total_my_bids > 0 else "0%",
                "missing_documents": missing_docs,
                "available_documents": available_docs
            },
            "matching_opportunities": matching_opportunities,
            "draft_form_fields": {
                "company_name": user.display_name,
                "registration_number": user.commercial_register or "",
                "tax_id": user.national_id or "",
                "address": user.wilaya or "",
                "legal_representative": user.full_name or "",
                "phone": "",
                "email": user.email or "",
                "banking_info": "",
                "offered_service": user.sector or "",
                "pricing_data": ""
            }
        }
    }

def get_context_for_user(user):
    if not user.is_authenticated:
        return None
        
    if user.role == 'central_admin':
        return build_central_admin_context(user)
    elif user.role == 'authority':
        return build_authority_context(user)
    elif user.role == 'supplier':
        return build_supplier_context(user)
        
    return None
