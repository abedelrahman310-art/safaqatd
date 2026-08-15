from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy, reverse
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages

from .models import Contract, ContractAmendment
from .forms import ContractActionForm, ContractAmendmentForm

class ContractListView(LoginRequiredMixin, ListView):
    model = Contract
    template_name = 'procurement/contract_list.html'
    context_object_name = 'contracts'
    paginate_by = 10

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()
        if user.role == 'authority':
            return qs.filter(authority=user).select_related('award', 'supplier')
        elif user.role == 'supplier':
            return qs.filter(supplier=user).select_related('award', 'authority')
        elif user.is_staff or user.has_perm('procurement.view_system_reports'):
            return qs.select_related('award', 'supplier', 'authority')
        return qs.none()


class ContractDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Contract
    template_name = 'procurement/contract_detail.html'
    context_object_name = 'contract'

    def test_func(self):
        user = self.request.user
        contract = self.get_object()
        if user.role == 'authority' and contract.authority == user:
            return True
        if user.role == 'supplier' and contract.supplier == user:
            return True
        if user.is_staff or user.has_perm('procurement.view_system_reports'):
            return True
        return False


class ContractUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Contract
    form_class = ContractActionForm
    template_name = 'procurement/contract_form.html'
    
    def test_func(self):
        contract = self.get_object()
        return self.request.user.has_perm('procurement.change_contract') and contract.authority == self.request.user and contract.status == 'draft'

    def get_success_url(self):
        return reverse('procurement:contract_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, "تم حفظ بيانات العقد بنجاح.")
        return super().form_valid(form)


class ContractApproveView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Contract
    fields = []
    template_name = 'procurement/contract_approve.html'

    def test_func(self):
        contract = self.get_object()
        return self.request.user.has_perm('procurement.approve_contract') and contract.authority == self.request.user and contract.status == 'draft'
    
    def form_valid(self, form):
        contract = form.save(commit=False)
        contract.status = 'active'
        contract.approved_by = self.request.user
        contract.save()
        messages.success(self.request, "تم تفعيل العقد بنجاح وأصبح سارياً.")
        return redirect('procurement:contract_detail', pk=contract.pk)


class ContractAmendmentCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = ContractAmendment
    form_class = ContractAmendmentForm
    template_name = 'procurement/contract_amendment_form.html'

    def test_func(self):
        self.contract = get_object_or_404(Contract, pk=self.kwargs['contract_id'])
        return self.request.user.has_perm('procurement.add_contractamendment') and self.contract.authority == self.request.user and self.contract.status == 'active'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['contract'] = self.contract
        return context

    def form_valid(self, form):
        amendment = form.save(commit=False)
        amendment.contract = self.contract
        amendment.submitted_by = self.request.user
        amendment.previous_value = self.contract.total_value
        amendment.previous_end_date = self.contract.end_date
        amendment.save()
        messages.success(self.request, "تم رفع طلب الملحق للمراجعة بنجاح.")
        return redirect('procurement:contract_detail', pk=self.contract.pk)
