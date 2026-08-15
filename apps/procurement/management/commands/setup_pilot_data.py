from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.procurement.models import Tender, Bid, AnnualBudget
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

class Command(BaseCommand):
    help = 'Setup pilot data for manual acceptance testing.'

    def handle(self, *args, **kwargs):
        self.stdout.write("Setting up pilot data...")
        
        # Create or get users
        authority_user, _ = User.objects.get_or_create(username='authority_pilot', defaults={'role': 'authority', 'full_name': 'Pilot Authority'})
        authority_user.set_password('password123')
        authority_user.save()
        
        committee_user, _ = User.objects.get_or_create(username='committee_pilot', defaults={'role': 'committee', 'full_name': 'Pilot Committee'})
        committee_user.set_password('password123')
        committee_user.save()
        
        supplier_user, _ = User.objects.get_or_create(username='supplier_pilot', defaults={'role': 'supplier', 'full_name': 'Pilot Supplier'})
        supplier_user.set_password('password123')
        supplier_user.save()
        
        # Create budget
        budget, _ = AnnualBudget.objects.get_or_create(year=2026, defaults={'total_budget': 1000000.0, 'authority': authority_user})
        
        # Create tender
        tender, _ = Tender.objects.get_or_create(
            title="Pilot Tender",
            defaults={
                'description': 'Tender for pilot testing.',
                'budget': 500000.0,
                'authority': authority_user,
                'deadline': timezone.now() - timedelta(days=1), # Expired so it can be opened
                'status': 'published'
            }
        )
        
        # Add committee member
        from apps.procurement.models import CommitteeMember
        CommitteeMember.objects.get_or_create(tender=tender, user=committee_user)
        
        # Create Bid
        Bid.objects.get_or_create(
            tender=tender,
            supplier=supplier_user,
            defaults={
                'supplier_name': supplier_user.full_name,
                'financial_offer': 50000.0,
                'status': 'pending'
            }
        )
        
        self.stdout.write(self.style.SUCCESS('Successfully set up pilot data!'))
