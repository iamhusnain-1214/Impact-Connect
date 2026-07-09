import json
import httpx
from groq import Groq
from config import Config
from models.ngo import NGO

_client = None


def _get_client():
    global _client
    if _client is None:
        if not Config.GROQ_API_KEY:
            raise RuntimeError(
                "GROQ_API_KEY is not set. Check that .env exists in the project "
                "root and contains a valid key from https://console.groq.com/keys"
            )
        _client = Groq(
            api_key=Config.GROQ_API_KEY,
            timeout=httpx.Timeout(30.0, connect=10.0),
            max_retries=3,
        )
    return _client


class AIRecommender:
    MODEL_NAME = "llama-3.3-70b-versatile"

    @staticmethod
    def build_context(query, limit=10):
        ngos = NGO.get_all(verified_only=True)[:limit]
        return [
            {
                "ngo_id": n["ngo_id"],
                "name": n["name"],
                "city": n["city"],
                "categories": n["categories"],
                "description": (n["description"] or "")[:150],
            }
            for n in ngos
        ]

    @staticmethod
    def call_llm(query, context):
        client = _get_client()

        prompt = f"""You are a social impact advisor for a Pakistani NGO discovery platform.

User request: "{query}"

Available NGOs (JSON):
{json.dumps(context, ensure_ascii=False)}

Pick up to 3 best-matching NGOs. Return fewer if fewer are relevant.
Respond with ONLY a JSON array, no markdown, no commentary, in this exact shape:
[{{"ngo_id": <id>, "name": "<n>", "reason": "<one short sentence>"}}]
"""
        response = client.chat.completions.create(
            model=AIRecommender.MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.3,
        )
        return response.choices[0].message.content

    @staticmethod
    def parse_response(raw_text):
        cleaned = raw_text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            cleaned = cleaned.replace("json", "", 1).strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            print(f"[AI PARSE ERROR] Could not parse model response: {raw_text}")
            return []

    @staticmethod
    def recommend(query):
        context = AIRecommender.build_context(query)
        if not context:
            return []
        try:
            raw = AIRecommender.call_llm(query, context)
        except Exception as e:
            print(f"[AI ERROR] Groq call failed: {e}")
            return []
        return AIRecommender.parse_response(raw)