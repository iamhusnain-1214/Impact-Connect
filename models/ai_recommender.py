import json
import google.generativeai as genai
from config import Config
from models.ngo import NGO

# ---------------------------------------------------------------------------
# Speed fixes for the AI recommender ("Gemini gives very slow answers"):
#
# 1. Model swapped from gemini-2.5-flash -> gemini-2.5-flash-lite. Flash-Lite
#    is Google's low-latency tier, built for exactly this kind of short
#    classification/ranking task - typically 2-3x faster time-to-first-token
#    than plain Flash, with negligible quality loss for "pick 3 of these 15".
# 2. genai.configure() was being called on every single request. It's cheap
#    but pointless repeated work - now done once at import time.
# 3. max_output_tokens is capped (200) since the response is always a short
#    JSON array - stops Gemini from ever running long on a rare verbose reply.
# 4. Context sent to Gemini is trimmed: fewer candidate NGOs (10 instead of
#    15) and descriptions truncated to 150 chars. Every extra token in the
#    prompt adds latency; Gemini doesn't need the full paragraph to judge
#    relevance, just enough to match the query.
# ---------------------------------------------------------------------------

_configured = False


def _ensure_configured():
    global _configured
    if not _configured:
        if not Config.GEMINI_API_KEY:
            raise RuntimeError(
                "GEMINI_API_KEY is not set. Check that .env exists in the project "
                "root and contains a valid key from https://aistudio.google.com"
            )
        genai.configure(api_key=Config.GEMINI_API_KEY)
        _configured = True


class AIRecommender:
    MODEL_NAME = "gemini-2.5-flash-lite"

    _model = None  # cached model instance, built once

    @classmethod
    def _get_model(cls):
        _ensure_configured()
        if cls._model is None:
            cls._model = genai.GenerativeModel(
                cls.MODEL_NAME,
                generation_config={
                    "max_output_tokens": 200,
                    "temperature": 0.3,
                    "response_mime_type": "application/json",
                },
            )
        return cls._model

    @staticmethod
    def build_context(query, limit=10):
        """
        Pull a small slice of verified NGOs as context. Trimmed field set
        and truncated descriptions keep the prompt short -> faster response.
        """
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
        model = AIRecommender._get_model()

        prompt = f"""You are a social impact advisor for a Pakistani NGO discovery platform.

User request: "{query}"

Available NGOs (JSON):
{json.dumps(context, ensure_ascii=False)}

Pick up to 3 best-matching NGOs. Return fewer if fewer are relevant.
Respond with ONLY a JSON array, no markdown, no commentary, in this exact shape:
[{{"ngo_id": <id>, "name": "<name>", "reason": "<one short sentence>"}}]
"""
        response = model.generate_content(prompt)
        return response.text

    @staticmethod
    def parse_response(raw_text):
        """Defensive cleanup in case Gemini still wraps JSON in ```fences."""
        cleaned = raw_text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            cleaned = cleaned.replace("json", "", 1).strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            print(f"[AI PARSE ERROR] Could not parse Gemini response: {raw_text}")
            return []

    @staticmethod
    def recommend(query):
        context = AIRecommender.build_context(query)
        if not context:
            return []
        raw = AIRecommender.call_llm(query, context)
        return AIRecommender.parse_response(raw)
