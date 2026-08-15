import json
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import PermissionDenied
from .services import AIService
from .safety import check_rate_limit, validate_question_safety

logger = logging.getLogger(__name__)

# CSRF Exempt is used ONLY for the public landing page guide for simplicity in this phase.
# Future sections MUST use CSRF and LoginRequired.
@csrf_exempt
def ai_assistant_view(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    if not AIService.is_provider_available():
        return JsonResponse({"error": "AI provider not available"}, status=503)

    client_ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
    
    try:
        check_rate_limit(client_ip, section='general')
    except PermissionDenied as e:
        return JsonResponse({"error": str(e)}, status=429)

    try:
        data = json.loads(request.body)
        question = data.get("question", "").strip()
        
        if not question:
            return JsonResponse({"error": "السؤال مطلوب"}, status=400)
            
        if not validate_question_safety(question):
            return JsonResponse({"error": "عذراً، لا يمكنني الإجابة على هذا السؤال نظراً لسياسة الأمان."}, status=400)

        # Call service
        response_data = AIService.generate_guide_response(question)
        return JsonResponse(response_data)
        
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        logger.error(f"Error in ai_assistant_view: {str(e)}")
        return JsonResponse({"error": "حدث خطأ داخلي. يرجى المحاولة لاحقاً."}, status=500)

from django.contrib.auth.decorators import login_required
from .context_builders import get_context_for_user

@login_required
def secure_ai_assistant_view(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    if not AIService.is_provider_available():
        return JsonResponse({"error": "AI provider not available"}, status=503)

    user = request.user
    
    try:
        # We can use a different section for authenticated users, e.g., using user_id instead of ip
        check_rate_limit(f"user_{user.id}", section='secure')
    except PermissionDenied as e:
        return JsonResponse({"error": str(e)}, status=429)

    try:
        data = json.loads(request.body)
        question = data.get("question", "").strip()
        
        if not question:
            return JsonResponse({"error": "السؤال مطلوب"}, status=400)
            
        if not validate_question_safety(question):
            return JsonResponse({"error": "عذراً، لا يمكنني الإجابة على هذا السؤال نظراً لسياسة الأمان."}, status=400)

        # Build context
        context_dict = get_context_for_user(user)
        if not context_dict:
            # Fallback to general guide if no context available for role
            response_data = AIService.generate_guide_response(question)
        else:
            response_data = AIService.generate_role_based_response(question, context_dict)
            
        return JsonResponse(response_data)
        
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        logger.error(f"Error in secure_ai_assistant_view: {str(e)}")
        return JsonResponse({"error": "حدث خطأ داخلي. يرجى المحاولة لاحقاً."}, status=500)
