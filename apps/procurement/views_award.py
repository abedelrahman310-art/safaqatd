from django.views.generic import ListView, DetailView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.contrib import messages
from django.core.exceptions import ValidationError

from .models import Award, Tender, Bid
from .forms import AwardActionForm
from .services import approve_award_and_create_contract

class AwardListView(LoginRequiredMixin, ListView):
    model = Award
    template_name = 'procurement/award_list.html'
    context_object_name = 'awards'
    paginate_by = 10

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()
        if user.role == 'authority':
            return qs.filter(tender__authority=user).select_related('tender', 'winning_bid')
        elif user.role == 'supplier':
            return qs.filter(winning_bid__supplier=user, status__in=['approved', 'published']).select_related('tender')
        elif user.is_staff or user.has_perm('procurement.view_system_reports'):
            return qs.select_related('tender', 'winning_bid')
        return qs.none()


class AwardDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Award
    template_name = 'procurement/award_detail.html'
    context_object_name = 'award'

    def test_func(self):
        user = self.request.user
        award = self.get_object()
        if user.role == 'authority' and award.tender.authority == user:
            return True
        if user.role == 'supplier' and award.winning_bid.supplier == user and award.status in ['approved', 'published']:
            return True
        if user.is_staff or user.has_perm('procurement.view_system_reports'):
            return True
        return False


class AwardApproveView(LoginRequiredMixin, UserPassesTestMixin, FormView):
    template_name = 'procurement/award_approve.html'
    form_class = AwardActionForm

    def test_func(self):
        if not self.request.user.has_perm('procurement.approve_award'):
            return False
        tender_id = self.kwargs.get('tender_id')
        return Tender.objects.filter(id=tender_id, authority=self.request.user).exists()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tender'] = get_object_or_404(Tender, pk=self.kwargs['tender_id'])
        context['bid'] = get_object_or_404(Bid, pk=self.kwargs['bid_id'])
        return context

    def form_valid(self, form):
        user = self.request.user
        tender_id = self.kwargs['tender_id']
        bid_id = self.kwargs['bid_id']
        awarded_amount = form.cleaned_data['awarded_amount']
        decision_reference = form.cleaned_data['decision_reference']

        try:
            award, contract = approve_award_and_create_contract(
                user=user,
                tender_id=tender_id,
                bid_id=bid_id,
                decision_reference=decision_reference,
                awarded_amount=awarded_amount
            )
            # If form has a document, save it
            if form.cleaned_data.get('decision_document'):
                award.decision_document = form.cleaned_data['decision_document']
                award.save(update_fields=['decision_document'])
                
            messages.success(self.request, f"تم اعتماد الإسناد وإنشاء مسودة العقد رقم {contract.contract_number} بنجاح.")
            return redirect('procurement:award_detail', pk=award.pk)
        except ValidationError as e:
            form.add_error(None, e.message)
            return self.form_invalid(form)
        except Exception as e:
            messages.error(self.request, "حدث خطأ غير متوقع أثناء الاعتماد.")
            return self.form_invalid(form)
