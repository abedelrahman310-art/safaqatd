import json
import logging
from django.utils import timezone

logger = logging.getLogger('product_analytics')

def log_event(event_name, request=None, actor_role=None, org_id=None, entity_type=None, entity_id=None, status="success", failure_category=None):
    event = {
        "timestamp": timezone.now().isoformat(),
        "event_name": event_name,
        "status": status,
    }
    
    if request:
        event["request_id"] = getattr(request, 'request_id', None)
        if request.user.is_authenticated:
            event["actor_role"] = actor_role or getattr(request.user, 'role', 'unknown')
            event["org_id"] = org_id or request.user.id
            
    if entity_type:
        event["entity_type"] = entity_type
    if entity_id:
        event["entity_id"] = entity_id
    if failure_category:
        event["failure_category"] = failure_category

    logger.info(json.dumps(event))
