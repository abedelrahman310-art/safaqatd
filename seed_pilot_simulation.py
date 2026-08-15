import os
import sys
import django
from django.utils import timezone
from datetime import timedelta

# Set standard output encoding to utf-8 for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.accounts.models import User
from apps.procurement.models import AnnualBudget, PlannedProject, Tender, Bid, ProcurementAuditLog

def seed_simulation():
    print("=== Starting Pilot Simulation Data Seeding ===")
    
    # 1. Password for test accounts
    DEFAULT_PWD = "Pilot2026Password!"
    
    # Authority User (مديرية التجهيزات العمومية لولاية الجزائر)
    auth_user, _ = User.objects.get_or_create(
        username="wilaya_algiers",
        defaults={
            "email": "equipements.algiers@mpt.gov.dz",
            "role": "authority",
            "full_name": "مديرية التجهيزات العمومية - ولاية الجزائر",
            "institution_name": "مديرية التجهيزات العمومية لولاية الجزائر",
            "sector": "الأشغال العمومية والمنشآت",
            "wilaya": "الجزائر",
            "is_active": True,
        }
    )
    auth_user.set_password(DEFAULT_PWD)
    auth_user.save()
    
    # 2. Suppliers (متعاملون اقتصاديون)
    suppliers_data = [
        {"username": "cosider_tp", "name": "مجمع كوسيدار للأشغال العمومية", "email": "contact@cosider-tp.dz", "rc": "16/00-0012345B26", "type": "شركة ذات أسهم SPA"},
        {"username": "algerie_telecom_services", "name": "اتصالات الجزائر للتجهيزات الذكية", "email": "bids@algerietelecom.dz", "rc": "16/00-0098765B26", "type": "مؤسسة عمومية اقتصادية EPE"},
        {"username": "batimetal_dz", "name": "شركة باتيميتال للهياكل المعدنية", "email": "soumission@batimetal.dz", "rc": "16/00-0055443B26", "type": "شركة ذات مسؤولية محدودة SARL"},
    ]
    
    supplier_objs = []
    for s_info in suppliers_data:
        s_user, _ = User.objects.get_or_create(
            username=s_info["username"],
            defaults={
                "email": s_info["email"],
                "role": "supplier",
                "full_name": s_info["name"],
                "commercial_register": s_info["rc"],
                "company_type": s_info["type"],
                "wilaya": "الجزائر",
                "is_active": True,
            }
        )
        s_user.set_password(DEFAULT_PWD)
        s_user.save()
        supplier_objs.append(s_user)

    # 3. Regulator User (المفتشية العامة للمالية)
    reg_user, _ = User.objects.get_or_create(
        username="regulator_igf",
        defaults={
            "email": "audit.marches@igf.gov.dz",
            "role": "central_admin",
            "full_name": "المفتشية العامة للمالية والرقابة المركزية",
            "is_active": True,
            "is_staff": True,
        }
    )
    reg_user.set_password(DEFAULT_PWD)
    reg_user.save()

    # 4. Annual Budget & Procurement Plan
    budget, _ = AnnualBudget.objects.get_or_create(
        authority=auth_user,
        year=2026,
        sector="الأشغال العمومية والبنى التحتية",
        defaults={
            "total_budget": 150000000.00,
            "budget_type": "wilaya",
            "status": "approved",
            "notes": "المخطط التقديري السنوي لولاية الجزائر معتمد وفق أحكام القانون رقم 23-12",
        }
    )

    # 5. Planned Projects
    proj1, _ = PlannedProject.objects.get_or_create(
        budget=budget,
        title="مشروع تهيئة وتوسعة محاور الطرق الكبرى - الشطر الجنوبي",
        defaults={
            "operation_code": "OP-2026-ALG-01",
            "ap_number": "AP-16/2026/044",
            "procurement_nature": "works",
            "planned_procedure": "open_tender",
            "estimated_value": 45000000.00,
            "estimated_quarter": 1,
            "expected_launch_date": timezone.now().date(),
        }
    )

    proj2, _ = PlannedProject.objects.get_or_create(
        budget=budget,
        title="تجهيز الشبكة المحلية ومراكز البيانات الإدارية بالعتاد الرقمي",
        defaults={
            "operation_code": "OP-2026-ALG-02",
            "ap_number": "AP-16/2026/089",
            "procurement_nature": "supplies",
            "planned_procedure": "open_tender",
            "estimated_value": 28000000.00,
            "estimated_quarter": 2,
            "expected_launch_date": timezone.now().date() + timedelta(days=30),
        }
    )

    # 6. Live Tender with Sealed Bids
    tender1, _ = Tender.objects.get_or_create(
        authority=auth_user,
        title="مشروع إنجاز المنشأة الفنية وجسر العبور على الطريق الوطني رقم 01",
        defaults={
            "description": "طلب عروض مفتوح مع اشتراط قدرات دنيا لإنجاز جسر خرساني مسبق الإجهاد وفق المعايير التقنية ومطابقة للمرسوم 23-12.",
            "budget": 42000000.00,
            "sector": "construction",
            "status": "published",
            "deadline": timezone.now() + timedelta(days=15),
            "wilaya": "الجزائر",
        }
    )
    proj1.is_launched = True
    proj1.tender = tender1
    proj1.save()

    # Create Sealed Bids for suppliers
    bid_amounts = [39500000.00, 41200000.00, 38800000.00]
    for idx, supp in enumerate(supplier_objs):
        Bid.objects.get_or_create(
            tender=tender1,
            supplier=supp,
            defaults={
                "supplier_name": supp.display_name,
                "financial_offer": bid_amounts[idx],
                "status": "pending",
                "delivery_time_days": 180,
                "warranty_months": 24,
                "similar_projects_count": 8,
                "bank_name": "البنك الوطني الجزائري BNA",
                "is_guarantee_verified": True,
                "agreement": True,
            }
        )

    # 7. Completed Tender with Opened Bids for Committee Evaluation
    tender2, _ = Tender.objects.get_or_create(
        authority=auth_user,
        title="مشروع التجهيز الرقمي لمقر المقاطعة الإدارية - المرحلة 01",
        defaults={
            "description": "استشارة معلنة لتوريد خوادم وتجهيزات أمان معلوماتي مطابقة للسيادة الرقمية.",
            "budget": 11500000.00,
            "sector": "tech",
            "status": "opened",
            "deadline": timezone.now() - timedelta(days=2),
            "wilaya": "الجزائر",
        }
    )

    # Bids with evaluation
    b1, _ = Bid.objects.get_or_create(
        tender=tender2,
        supplier=supplier_objs[1],
        defaults={
            "supplier_name": supplier_objs[1].display_name,
            "financial_offer": 9800000.00,
            "delivery_time_days": 45,
            "warranty_months": 36,
            "status": "accepted",
            "agreement": True,
        }
    )
    b2, _ = Bid.objects.get_or_create(
        tender=tender2,
        supplier=supplier_objs[2],
        defaults={
            "supplier_name": supplier_objs[2].display_name,
            "financial_offer": 10900000.00,
            "delivery_time_days": 60,
            "warranty_months": 24,
            "status": "pending",
            "agreement": True,
        }
    )

    # Log action in audit log
    ProcurementAuditLog.log_action(
        user=auth_user,
        action="SEED_SIMULATION_DATA",
        resource_type="TENDER_SIMULATION",
        resource_id=str(tender1.id),
        details={"message": "تم بنجاح توليد بيانات محاكاة تشغيلية شاملة للمنصة"}
    )

    print("\n✅ تم بنجاح إنشاء بيانات المحاكاة الحقيقية!")
    print("==================================================")
    print("🔑 بيانات الحسابات الموحدة:")
    print(f"كلمة المرور المشتركة لجميع الحسابات التجريبية: {DEFAULT_PWD}")
    print("--------------------------------------------------")
    print("1. المصلحة المتعاقدة: wilaya_algiers")
    print("2. المتعامل الاقتصادي 1 (كوسيدار): cosider_tp")
    print("3. المتعامل الاقتصادي 2 (اتصالات الجزائر): algerie_telecom_services")
    print("4. المتعامل الاقتصادي 3 (باتيميتال): batimetal_dz")
    print("5. الإدارة المركزية والرقابة: regulator_igf")
    print("==================================================")

if __name__ == '__main__':
    seed_simulation()
