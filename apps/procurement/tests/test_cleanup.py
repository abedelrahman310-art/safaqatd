import os
from datetime import datetime, timedelta
from pathlib import Path
from django.test import TestCase
from django.conf import settings
from django.core.management import call_command
from django.core.files.uploadedfile import SimpleUploadedFile
from apps.procurement.models import Tender
from django.contrib.auth import get_user_model
User = get_user_model()

class CleanupCommandTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="test_auth", email="test_auth@example.com", password="password")
        self.media_root = Path(settings.MEDIA_ROOT)
        self.media_root.mkdir(parents=True, exist_ok=True)
        
        # Create a real tender with an attached file
        self.tender = Tender.objects.create(
            title="Test Tender",
            authority=self.user,
            description="Test desc",
            budget=1000.0,
            deadline="2026-12-31"
        )
        
        file_content = b"Test Content"
        attached_file = SimpleUploadedFile("attached_file.pdf", file_content)
        self.tender.document.save("attached_file.pdf", attached_file)
        
        self.attached_path = Path(self.tender.document.path)
        
        # Create an orphaned file (recent)
        self.orphaned_recent_path = self.media_root / "recent_orphan.pdf"
        self.orphaned_recent_path.write_bytes(b"Recent Orphan")
        
        # Create an orphaned file (old)
        self.orphaned_old_path = self.media_root / "old_orphan.pdf"
        self.orphaned_old_path.write_bytes(b"Old Orphan")
        
        # Mock mtime for old orphan
        from datetime import timezone as dt_timezone
        old_time = (datetime.now(tz=dt_timezone.utc) - timedelta(days=40)).timestamp()
        os.utime(self.orphaned_old_path, (old_time, old_time))

    def tearDown(self):
        if self.attached_path.exists(): self.attached_path.unlink()
        if self.orphaned_recent_path.exists(): self.orphaned_recent_path.unlink()
        if self.orphaned_old_path.exists(): self.orphaned_old_path.unlink()

    def test_dry_run_does_not_delete(self):
        call_command('cleanup_orphaned_files', '--dry-run', older_than_days=30)
        self.assertTrue(self.attached_path.exists())
        self.assertTrue(self.orphaned_recent_path.exists())
        self.assertTrue(self.orphaned_old_path.exists())
        
    def test_confirm_deletes_old_orphaned_only(self):
        call_command('cleanup_orphaned_files', '--confirm', older_than_days=30)
        self.assertTrue(self.attached_path.exists())
        self.assertTrue(self.orphaned_recent_path.exists())
        self.assertFalse(self.orphaned_old_path.exists())
