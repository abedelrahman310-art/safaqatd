import re
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
import logging

logger = logging.getLogger(__name__)

def check_rate_limit(ip_address: str, section: str = 'general'):
    """
    Apply a strict rate limit of 5 requests per minute per IP.
    """
    cache_key = f"rate_limit_ai_{section}_{ip_address}"
    requests = cache.get(cache_key, 0)
    
    if requests >= 5:
        logger.warning(f"Rate limit exceeded for IP: {ip_address}")
        raise PermissionDenied("تم تجاوز الحد المسموح من الطلبات. يرجى المحاولة لاحقاً.")
        
    cache.set(cache_key, requests + 1, timeout=60)

def validate_question_safety(question: str) -> bool:
    """
    Basic defense against prompt injection patterns.
    """
    if len(question) > 500:
        return False
        
    dangerous_patterns = [
        r"تجاهل",
        r"ignore",
        r"system prompt",
        r"instructions",
        r"api key",
        r"سرية",
        r"select \*",
        r"drop table"
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, question, re.IGNORECASE):
            logger.warning("Potential prompt injection detected.")
            return False
            
    return True
