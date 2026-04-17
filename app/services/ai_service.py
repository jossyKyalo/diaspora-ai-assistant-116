import json
import re
from groq import Groq
from flask import current_app

def _get_client():
    return Groq(api_key=current_app.config["GROQ_API_KEY"])

def _call_llm(prompt: str) -> str:
    client = _get_client()

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "system",
                "content": "You are a strict JSON generator. Output ONLY valid JSON. No explanations."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.2
    )

    return response.choices[0].message.content.strip()

INTENT_SYSTEM_PROMPT = """
You are an AI assistant for Vunoh Global, a platform that helps Kenyans living abroad manage tasks back home.

Your job is to analyze a customer request and extract structured information from it.

You must return ONLY a valid JSON object with no markdown, no explanation, no code fences.

The JSON must have exactly these fields:
- "intent": one of ["send_money", "hire_service", "verify_document", "airport_transfer", "check_status"]
- "entities": an object containing any of these fields that are present in the message:
    - "amount": string (e.g. "KES 15000" or "15000")
    - "recipient": string (name or description of who receives money or service)
    - "location": string (area or town in Kenya)
    - "document_type": string (e.g. "land title deed", "national ID", "birth certificate")
    - "service_type": string (e.g. "cleaning", "legal consultation", "errand")
    - "urgency": string (e.g. "urgent", "this Friday", "end of month")
    - "service_date": string (any date or time mentioned)
    - "notes": string (any other relevant context)
- "confidence": a number between 0 and 1 indicating how confident you are in the intent classification

Rules:
- If a field is not present in the message, omit it from entities entirely.
- Do not add fields that are not listed above.
- Return ONLY the JSON object. Nothing else.
"""

STEPS_SYSTEM_PROMPT = """
You are an operations coordinator at Vunoh Global, a diaspora services platform in Kenya.

Given a task intent and its extracted details, generate a clear sequence of fulfillment steps.

Return ONLY a valid JSON array of step objects. No markdown, no explanation.

Each step object must have:
- "step_number": integer starting from 1
- "title": short action title (max 6 words)
- "description": one sentence describing what happens in this step
- "owner": who does this step — one of ["Customer", "Finance Team", "Operations Team", "Legal Team", "Logistics Team", "System"]

Return ONLY the JSON array. Nothing else.
"""

MESSAGES_SYSTEM_PROMPT = """
You are writing confirmation messages for Vunoh Global, a platform helping Kenyans in the diaspora manage tasks back home.

Given a task summary, generate three confirmation messages for three different channels.

Return ONLY a valid JSON object with exactly these three keys: "whatsapp", "email", "sms"

Rules for each format:

whatsapp:
- Conversational and warm, like a message from a helpful friend
- Use line breaks naturally
- 1-2 emojis maximum, only where they feel natural
- Include the task code
- 3-6 lines total

email:
- Professional and structured
- Start with "Dear [Customer],"
- Include task code, intent summary, next steps
- End with a professional sign-off: "Warm regards, Vunoh Global Team"
- 8-15 lines

sms:
- Under 160 characters total
- Include task code and the single most important next action
- No emojis
- Plain and direct

Return ONLY the JSON object. Nothing else.
"""


def extract_intent(user_message: str) -> dict:
    prompt = f"{INTENT_SYSTEM_PROMPT}\n\nCustomer message:\n{user_message}"
    raw = _call_llm(prompt) 
    return safe_json_loads(raw)

def generate_steps(intent: str, entities: dict, task_code: str) -> list:
    summary = f"Task code: {task_code}\nIntent: {intent}\nDetails: {json.dumps(entities, indent=2)}"
    prompt = f"{STEPS_SYSTEM_PROMPT}\n\nTask summary:\n{summary}"
    
    raw = _call_llm(prompt) 
    return safe_json_loads(raw)


def generate_messages(intent: str, entities: dict, task_code: str, risk_label: str) -> dict:
    summary = (
        f"Task code: {task_code}\n"
        f"Intent: {intent}\n"
        f"Risk level: {risk_label}\n"
        f"Details: {json.dumps(entities, indent=2)}"
    )

    prompt = f"{MESSAGES_SYSTEM_PROMPT}\n\nTask summary:\n{summary}"

    raw = _call_llm(prompt) 
    return safe_json_loads(raw)


def _strip_code_fences(text: str) -> str:
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()

def safe_json_loads(raw: str):
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        cleaned = _strip_code_fences(raw)
        return json.loads(cleaned)