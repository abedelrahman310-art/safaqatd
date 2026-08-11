from django.contrib.auth.mixins import AccessMixin
from django.shortcuts import redirect
from django.contrib import messages

class SupplierRequiredMixin(AccessMixin):
    """Verify that the current user is authenticated and is a supplier."""
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
            
        if request.user.role != 'supplier':
            messages.error(request, "عذراً، هذه الصفحة مخصصة للمتعاملين الاقتصاديين فقط.")
            return redirect('core:home')
            
        if getattr(request.user, 'is_blacklisted', False):
            messages.error(request, "عذراً، حسابك مدرج في القائمة السوداء ولا يمكنك التقديم على الصفقات.")
            return redirect('core:home')
            
        return super().dispatch(request, *args, **kwargs)
