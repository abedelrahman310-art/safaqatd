import os
import logging
from typing import Dict, Any
import json
from .schemas import GuideResponseSchema
from .prompts import SYSTEM_PROMPT, get_role_based_prompt

logger = logging.getLogger(__name__)

try:
    from google import genai
    from google.genai import types
except (ImportError, Exception, SystemError):
    genai = None

class AIService:
    @staticmethod
    def is_provider_available() -> bool:
        if not genai:
            return False
        if not os.environ.get("GEMINI_API_KEY"):
            return False
        return True

    @classmethod
    def generate_guide_response(cls, question: str) -> dict:
        """
        Generates a response using the General Guide System Prompt (No Context).
        """
        return cls._generate_response(question, SYSTEM_PROMPT)

    @classmethod
    def generate_role_based_response(cls, question: str, context_dict: dict) -> dict:
        """
        Generates a response using the Role-Based System Prompt.
        """
        system_prompt = get_role_based_prompt(context_dict)
        return cls._generate_response(question, system_prompt)

    @classmethod
    def _generate_response(cls, question: str, system_instruction: str) -> dict:
        """
        Internal method to generate responses with a specific system instruction.
        """
        if not cls.is_provider_available():
            raise Exception("AI Provider not available.")

        try:
            client = genai.Client()
            secure_question = f"[UNTRUSTED_USER_INPUT]\n{question}\n[/UNTRUSTED_USER_INPUT]"
            
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=secure_question,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    response_schema=GuideResponseSchema,
                    temperature=0.2,
                ),
            )
            
            if not response.text:
                raise Exception("Empty response from AI Provider.")
                
            return json.loads(response.text)
            
        except Exception as e:
            logger.error(f"Error calling AI Provider: {str(e)}")
            raise Exception("فشل الاتصال بالمزود.")
