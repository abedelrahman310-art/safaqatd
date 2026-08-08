from django.core.exceptions import PermissionDenied
from functools import wraps

def role_required(allowed_roles):
    """
    Decorator for views that checks whether a user has a specific role.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                from django.contrib.auth.views import redirect_to_login
                return redirect_to_login(request.get_full_path())
                
            if request.user.role not in allowed_roles:
                raise PermissionDenied("ليس لديك الصلاحية الكافية للوصول إلى هذه الصفحة.")
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
