import hashlib
from datetime import timedelta
from apps.procurement.models import Tender, Bid
from apps.ai_regulator.models import CollusionAlert


class CollusionDetectionEngine:
    """
    محرك فحص ورصد شبهات التواطؤ، عروض التغطية، والتطابق الرقمي
    """

    @classmethod
    def scan_tender(cls, tender: Tender):
        """
        إجراء فحص شامل لكافة العروض المودعة لصفقة معينة
        """
        bids = tender.bids.select_related('supplier').all()
        alerts = []

        if bids.count() < 2:
            return alerts

        # 1. فحص توقيت الإيداع المتزامن (Rapid Succession Submission)
        sorted_bids = sorted(bids, key=lambda b: b.submitted_at or b.created_at)
        for i in range(len(sorted_bids) - 1):
            b1 = sorted_bids[i]
            b2 = sorted_bids[i+1]
            t1 = b1.submitted_at or b1.created_at
            t2 = b2.submitted_at or b2.created_at
            
            diff_seconds = abs((t2 - t1).total_seconds())
            if diff_seconds < 180:  # إيداع فارقه الزمني أقل من 3 دقائق
                alert, _ = CollusionAlert.objects.get_or_create(
                    tender=tender,
                    alert_type='submission_timing',
                    defaults={
                        'severity': 'medium',
                        'risk_score': 65,
                        'evidence_summary': f"تم تسجيل إيداع متزامن بفارق {int(diff_seconds)} ثانية بين العارضين ({b1.supplier_name or b1.supplier.username}) و ({b2.supplier_name or b2.supplier.username}).",
                        'evidence_data': {
                            'bids': [b1.id, b2.id],
                            'diff_seconds': diff_seconds,
                            'time_1': t1.isoformat(),
                            'time_2': t2.isoformat(),
                        }
                    }
                )
                alert.involved_suppliers.add(b1.supplier, b2.supplier)
                alerts.append(alert)

        # 2. فحص البصمة الرقمية للوثائق وتكرار الـ Hash
        hash_map = {}
        for bid in bids:
            b_hash = bid.bid_hash or ''
            if b_hash:
                prefix = b_hash[:16]
                if prefix in hash_map:
                    other_bid = hash_map[prefix]
                    alert, _ = CollusionAlert.objects.get_or_create(
                        tender=tender,
                        alert_type='doc_metadata',
                        defaults={
                            'severity': 'high',
                            'risk_score': 90,
                            'evidence_summary': f"تطابق في البصمة الرقمية للملفات المرفقة بين ({bid.supplier_name or bid.supplier.username}) و ({other_bid.supplier_name or other_bid.supplier.username}) مما يدل على إنشاء الملفات من نفس المصدر.",
                            'evidence_data': {
                                'matched_hash_prefix': prefix,
                                'bids': [bid.id, other_bid.id],
                            }
                        }
                    )
                    alert.involved_suppliers.add(bid.supplier, other_bid.supplier)
                    alerts.append(alert)
                else:
                    hash_map[prefix] = bid

        return alerts
