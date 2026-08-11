from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView, TemplateView
from apps.procurement.models import Tender, Bid
from apps.core.mixins import SupplierRequiredMixin

class SupplierDashboardView(SupplierRequiredMixin, TemplateView):
    template_name = 'suppliers/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        supplier = self.request.user
        
        # Dashboard stats
        context['my_bids_count'] = Bid.objects.filter(supplier=supplier).count()
        context['available_tenders_count'] = Tender.objects.filter(status__in=['published', 'evaluating']).count()
        context['accepted_bids_count'] = Bid.objects.filter(supplier=supplier, status='accepted').count()
        
        # Recent available tenders
        context['recent_tenders'] = Tender.objects.filter(status='published').order_by('-created_at')[:5]
        
        return context

class AvailableTendersListView(SupplierRequiredMixin, ListView):
    model = Tender
    template_name = 'suppliers/tenders_list.html'
    context_object_name = 'tenders'
    paginate_by = 10
    
    def get_queryset(self):
        qs = super().get_queryset().select_related('authority').filter(status__in=['published', 'evaluating'])
        
        # Basic filtering logic
        search_query = self.request.GET.get('q')
        if search_query:
            qs = qs.filter(title__icontains=search_query)
            
        sector = self.request.GET.get('sector')
        if sector:
            qs = qs.filter(sector__icontains=sector)
            
        return qs.order_by('-created_at')
        
    def get_template_names(self):
        # HTMX support for seamless pagination and searching
        if self.request.htmx:
            return ['suppliers/partials/_tenders_table.html']
        return [self.template_name]

class TenderDetailView(SupplierRequiredMixin, DetailView):
    model = Tender
    template_name = 'suppliers/tender_detail.html'
    context_object_name = 'tender'
    
    def get_queryset(self):
        from django.db.models import Exists, OuterRef
        bids = Bid.objects.filter(tender=OuterRef('pk'), supplier=self.request.user)
        # Supplier can only view published or evaluating tenders
        return super().get_queryset().filter(status__in=['published', 'evaluating']).annotate(has_bid=Exists(bids))
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # has_bid is populated via annotation in get_queryset
        context['has_bid'] = getattr(self.object, 'has_bid', False)
        return context
