from groq import Groq
from groq import APIConnectionError, APIError, RateLimitError
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
import os
import json
from typing import List, Dict
from backend.utils.logging import get_logger
from datetime import datetime

logger = get_logger("llm_service")

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

class LLMService:
    
    SYSTEM_PROMPT_TEMPLATE = """You are an AI booking assistant for {business_name}.
Your goal is to politely answer customer questions and help them book an appointment.

Context:
Today's Date: {current_time}
Services: {services}
Hours: {hours}
FAQ: {faq_context}

Be extremely concise, friendly, and helpful. Do not hallucinate services that are not listed.
"""

    @staticmethod
    def _get_booking_tools():
        """Define Groq strictly-typed native Tool schemas."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "book_appointment",
                    "description": "Triggered when a user explicitly requests to book an appointment.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "service": {
                                "type": "string",
                                "description": "The exact service name requested."
                            },
                            "datetime": {
                                "type": "string",
                                "description": "The exact date and time in ISO format (YYYY-MM-DDTHH:MM)."
                            }
                        },
                        "required": ["service"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "cancel_appointment",
                    "description": "Triggered when a user requests to cancel an existing appointment.",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "faq_response",
                    "description": "Triggered when a user just greets you, or asks a general question about hours, location, prices, or policies.",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            }
        ]

    @staticmethod
    @retry(
        wait=wait_exponential(multiplier=1.5, min=2, max=15),
        stop=stop_after_attempt(4),
        retry=retry_if_exception_type((APIConnectionError, APIError, RateLimitError))
    )
    def classify_intent(user_message: str, chat_history: List[Dict], business_ctx: dict) -> dict:
        """Uses Groq Native Tool Calling to extract strict JSON intent parameters."""
        if not client: 
            return {"intent": "unknown", "service": None, "datetime": None}
        
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        # In a real SaaS setup, business_ctx["services_offered"] is now coming from the DB as a list of dicts.
        system_content = LLMService.SYSTEM_PROMPT_TEMPLATE.format(
            current_time=now_str,
            business_name=business_ctx.get("name", "our business"),
            services=json.dumps(business_ctx.get("services_offered", {})),
            hours=json.dumps(business_ctx.get("operating_hours", {})),
            faq_context=business_ctx.get("faq_context", "")
        )
        
        messages = [{"role": "system", "content": system_content}]
        for msg in chat_history:
            messages.append({"role": msg["role"], "content": msg["message_content"]})
            
        messages.append({"role": "user", "content": user_message})
        
        logger.debug(f"Attempting native tool call extraction for msg: {user_message[:30]}...")
        
        start_time = time.time()
        response = client.chat.completions.create(
            messages=messages,
            model="llama3-8b-8192", 
            temperature=0.0,
            tools=LLMService._get_booking_tools(),
            tool_choice="auto" 
        )
        latency = time.time() - start_time
        
        message_resp = response.choices[0].message
        usage = response.usage.model_dump() if hasattr(response, "usage") else {}
        
        # Parse Native Tool Calls
        result = {
            "intent": "faq", 
            "service": None, 
            "datetime": None,
            "metrics": {
                "latency": latency,
                "usage": usage
            }
        }

        if message_resp.tool_calls:
            tool_call = message_resp.tool_calls[0]
            function_name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)
            
            logger.info(f"LLM Tool Calling Success: {function_name} with {args} [Latency: {latency:.2f}s]")
            
            if function_name == "book_appointment":
                result.update({
                    "intent": "booking_request",
                    "service": args.get("service"),
                    "datetime": args.get("datetime")
                })
            elif function_name == "cancel_appointment":
                result["intent"] = "cancel_booking"
            elif function_name == "faq_response":
                result["intent"] = "faq"
        else:
            logger.info(f"No explicit tools called, mapping to FAQ. [Latency: {latency:.2f}s]")
                
        return result

    @staticmethod
    @retry(
        wait=wait_exponential(multiplier=1.5, min=2, max=15),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type((APIConnectionError, APIError, RateLimitError))
    )
    def generate_response(business_ctx: dict, chat_history: List[Dict], user_message: str) -> str:
        """Generates conversational FAQ responses directly."""
        if not client: return "I am currently offline. Please try again later."
        
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        system_content = LLMService.SYSTEM_PROMPT_TEMPLATE.format(
            current_time=now_str,
            business_name=business_ctx.get("name", "our business"),
            services=json.dumps(business_ctx.get("services_offered", {})),
            hours=json.dumps(business_ctx.get("operating_hours", {})),
            faq_context=business_ctx.get("faq_context", "")
        )
        
        messages = [{"role": "system", "content": system_content}]
        for msg in chat_history:
            messages.append({"role": msg["role"], "content": msg["message_content"]})
        messages.append({"role": "user", "content": user_message})
        
        try:
            response = client.chat.completions.create(
                messages=messages,
                model="llama3-70b-8192", 
                temperature=0.4,
                max_tokens=256
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"LLM Generation Error: {e}")
            raise
