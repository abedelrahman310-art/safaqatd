import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from apps.procurement.models import Tender, Bid, TenderAppeal, BidOpeningCommittee

class Command(BaseCommand):
    help = 'Cleans up orphaned files in the media directory that have no database reference.'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', default=True, help='Run in dry-run mode without deleting.')
        parser.add_argument('--confirm', action='store_true', help='Confirm actual deletion.')
        parser.add_argument('--older-than-days', type=int, default=30, help='Grace period in days.')
        parser.add_argument('--report', type=str, help='Path to save JSON report.')

    def handle(self, *args, **options):
        dry_run = options['dry_run'] and not options['confirm']
        grace_days = options['older_than_days']
        report_path = options['report']
        
        media_root = Path(settings.MEDIA_ROOT)
        if not media_root.exists():
            self.stdout.write(self.style.WARNING(f"Media root {media_root} does not exist."))
            return

        # 1. Gather all file paths from DB
        db_files = set()
        
        for t in Tender.all_objects.all():
            if t.document:
                try: db_files.add(Path(t.document.path).resolve())
                except: pass
            
        for b in Bid.all_objects.all():
            if b.financial_document:
                try: db_files.add(Path(b.financial_document.path).resolve())
                except: pass
            if b.technical_document:
                try: db_files.add(Path(b.technical_document.path).resolve())
                except: pass
            if b.integrity_declaration:
                try: db_files.add(Path(b.integrity_declaration.path).resolve())
                except: pass
            if b.bank_guarantee_file:
                try: db_files.add(Path(b.bank_guarantee_file.path).resolve())
                except: pass
            
        for a in TenderAppeal.objects.all():
            if a.attachment:
                try: db_files.add(Path(a.attachment.path).resolve())
                except: pass
            
        for c in BidOpeningCommittee.objects.all():
            if c.report_file:
                try: db_files.add(Path(c.report_file.path).resolve())
                except: pass

        # 2. Iterate through MEDIA_ROOT
        scanned_count = 0
        orphaned_candidates = []
        deleted_count = 0
        
        cutoff_date = timezone.now() - timedelta(days=grace_days)
        
        for file_path in media_root.rglob('*'):
            if file_path.is_file():
                scanned_count += 1
                try:
                    resolved_path = file_path.resolve()
                    if resolved_path not in db_files:
                        # Check age
                        from datetime import timezone as dt_timezone
                        mtime = datetime.fromtimestamp(resolved_path.stat().st_mtime, tz=dt_timezone.utc)
                        if mtime < cutoff_date:
                            orphaned_candidates.append(str(resolved_path))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error processing {file_path}: {e}"))

        report_data = {
            "timestamp": timezone.now().isoformat(),
            "actor": "system_admin",
            "dry_run": dry_run,
            "scanned_files": scanned_count,
            "orphaned_candidates": len(orphaned_candidates),
            "deleted_files": 0,
            "files": []
        }

        if dry_run:
            self.stdout.write(self.style.SUCCESS(f"[DRY-RUN] Found {len(orphaned_candidates)} orphaned files older than {grace_days} days out of {scanned_count} scanned."))
            report_data["files"] = [{"path": p, "status": "candidate"} for p in orphaned_candidates]
        else:
            self.stdout.write(self.style.WARNING(f"Deleting {len(orphaned_candidates)} orphaned files..."))
            for path_str in orphaned_candidates:
                try:
                    os.remove(path_str)
                    deleted_count += 1
                    report_data["files"].append({"path": path_str, "status": "deleted"})
                except Exception as e:
                    report_data["files"].append({"path": path_str, "status": f"error: {str(e)}"})
            report_data["deleted_files"] = deleted_count
            self.stdout.write(self.style.SUCCESS(f"Successfully deleted {deleted_count} files."))

        if report_path:
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)
            self.stdout.write(self.style.SUCCESS(f"Report saved to {report_path}"))
