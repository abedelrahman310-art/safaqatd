from django.shortcuts import redirect
from django.core.exceptions import PermissionDenied

class RegulatorRequiredMixin:
    required_role = "regulator"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("login")

        if getattr(request.user, "role", None) != self.required_role:
            raise PermissionDenied

        return super().dispatch(request, *args, **kwargs)
