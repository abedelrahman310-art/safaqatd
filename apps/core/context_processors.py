from .models import Notification

def notifications(request):
    if request.user.is_authenticated:
        user_notifications = Notification.objects.filter(user=request.user)
        unread_count = user_notifications.filter(is_read=False).count()
        # Fetch top 5 recent notifications for the dropdown
        recent_notifications = user_notifications[:5]
        return {
            'notifications': recent_notifications,
            'unread_notifications_count': unread_count,
        }
    return {}
