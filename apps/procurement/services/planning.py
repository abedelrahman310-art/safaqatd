from decimal import Decimal
from django.db.models import Sum
from apps.procurement.models import AnnualBudget, PlannedProject, Tender, ProcurementAuditLog

class ProcurementPlanningService:
    """
    Service layer for Algerian Public Procurement Planning (Law 23-12 / LOLF 18-15).
    """

    # Legal thresholds under Law 23-12 (Thresholds for Simple Consultation vs Tender)
    CONSULTATION_THRESHOLD_WORKS_SUPPLIES = Decimal('12000000.00')  # 12 Million DZD
    CONSULTATION_THRESHOLD_SERVICES_STUDIES = Decimal('6000000.00')  # 6 Million DZD

    @classmethod
    def check_fragmentation_risk(cls, budget, planned_project):
        """
        Validates whether adding/modifying this project risks illegal contract fragmentation
        (Fractionnement des besoins) under Law 23-12.
        """
        nature = planned_project.procurement_nature
        estimated_val = Decimal(str(planned_project.estimated_value))

        # Check total estimated value for same nature in this plan
        existing_total = budget.planned_projects.filter(
            procurement_nature=nature
        ).exclude(id=planned_project.id if planned_project.id else None).aggregate(
            Sum('estimated_value')
        )['estimated_value__sum'] or Decimal('0.00')

        combined_total = existing_total + estimated_val

        threshold = cls.CONSULTATION_THRESHOLD_WORKS_SUPPLIES if nature in ['works', 'supplies'] else cls.CONSULTATION_THRESHOLD_SERVICES_STUDIES
        
        warning = None
        if planned_project.planned_procedure == 'consultation' and combined_total > threshold:
            warning = (
                f"تنبيه قانوني (المادة 13 من القانون 23-12): مجموع الحاجات المبرمجة لنشاط ({planned_project.get_procurement_nature_display()}) "
                f"يبلغ {combined_total:,.2f} دج متجاوزاً السقف القانوني للاستشارة ({threshold:,.2f} دج). "
                f"يُرجى إدراج العملية ضمن إجراء الصفقة العمومية (طلب عروض) لتفادي خطر تجزئة الحاجات."
            )

        return {
            'has_risk': warning is not None,
            'warning_message': warning,
            'combined_total': float(combined_total),
            'threshold': float(threshold)
        }

    @classmethod
    def convert_project_to_tender(cls, user, project_id):
        """
        Transforms a planned operation into an official draft tender with one click.
        """
        project = PlannedProject.objects.select_related('budget', 'budget__authority').get(id=project_id)
        
        if project.is_launched and project.tender:
            return project.tender

        # Create new Tender instance pre-filled from planning
        tender_type_map = {
            'open': 'open',
            'minimum_capacity': 'minimum_capacity',
            'restricted': 'restricted',
            'contest': 'contest',
            'negotiation': 'negotiation',
            'consultation': 'open',
        }

        new_tender = Tender.objects.create(
            title=project.title,
            authority=project.budget.authority,
            description=f"صفقة عمومية منبثقة عن المخطط التقديري السنوي لسنة {project.budget.year}.\nرقم العملية: {project.operation_code or 'غير محدد'}\nرقم رخصة البرنامج (AP): {project.ap_number or 'غير محدد'}",
            budget=project.estimated_value,
            sector=project.budget.sector,
            wilaya=getattr(project.budget.authority, 'wilaya', '16'),
            deadline=project.expected_launch_date or (project.created_at.date()),
            tender_type=tender_type_map.get(project.planned_procedure, 'open'),
            status='draft',
        )

        project.is_launched = True
        project.tender = new_tender
        project.save()

        # Audit Trail
        ProcurementAuditLog.log_action(
            user=user,
            action='LAUNCH_TENDER_FROM_PLAN',
            resource_type='planned_project',
            resource_id=project.id,
            details={
                'project_title': project.title,
                'tender_id': new_tender.id,
                'budget_year': project.budget.year,
                'estimated_value': str(project.estimated_value)
            }
        )

        return new_tender
