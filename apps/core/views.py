from django.shortcuts import render, redirect

def index(request):
    return render(request, 'core/home.html')

from django.contrib.auth.decorators import login_required
from .models import Notification

def about(request):
    return render(request, 'core/about.html')

@login_required
def mark_notifications_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return redirect(request.META.get('HTTP_REFERER', 'core:index'))

@login_required
def notifications_list(request):
    notifications = request.user.notifications.all().order_by('-created_at')
    return render(request, 'core/notifications_list.html', {'all_notifications': notifications})
