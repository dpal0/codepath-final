import os
import json
import base64
from datetime import datetime
import google.generativeai as genai
from PIL import Image
import io

from dotenv import load_dotenv
load_dotenv()

genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-3.1-flash-lite-preview")

SYSTEM_PROMPT = """You are a food analysis assistant. Given a food image and an optional user note, 
return ONLY a valid JSON object with these exact fields:

{
  "dish": "name of the dish or food item",
  "estimated_calories": <integer, your best estimate>,
  "portion": "small | medium | large | unknown",
  "meal_time_guess": "breakfast | lunch | dinner | snack | unknown",
  "confidence": "high | medium | low",
  "note_calories_explicit": <integer if user wrote calories in their note, else null>,
  "note_portion_explicit": "<portion string if user wrote it, else null>",
  "note_dish_explicit": "<dish name if user wrote it, else null>"
}

Rules:
- If the user note contains explicit calorie info (e.g. "600 cal", "~500 calories"), extract it into note_calories_explicit
- If the note names the dish explicitly, use that in note_dish_explicit
- If the note mentions portion size, extract it into note_portion_explicit
- For estimated_calories: prefer note_calories_explicit if provided, otherwise estimate from image
- For meal_time_guess: infer from the timestamp context provided and visual cues
- Return ONLY the JSON object, no markdown, no explanation, no backticks"""


def analyze_food(image_bytes: bytes, note: str, timestamp: datetime) -> dict:
    """
    Send food image + note to Gemini, return structured parsed result.
    Returns dict with parsed fields, or {"error": "..."} on failure.
    """
    try:
        image = Image.open(io.BytesIO(image_bytes))

        hour = timestamp.hour
        time_context = f"The photo was taken at {timestamp.strftime('%I:%M %p')} (hour {hour})."

        note_context = f"User note: {note.strip()}" if note and note.strip() else "User provided no note."

        prompt = f"""{SYSTEM_PROMPT}

{time_context}
{note_context}

Analyze the food in this image."""

        response = model.generate_content([prompt, image])
        raw = response.text.strip()

        # Strip markdown fences if model adds them despite instructions
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        parsed = json.loads(raw)

        # If note had explicit calories, use those as final calorie count
        if parsed.get("note_calories_explicit"):
            parsed["estimated_calories"] = parsed["note_calories_explicit"]

        return parsed

    except json.JSONDecodeError as e:
        return {"error": f"JSON parse failed: {e}. Raw response: {response.text[:200]}"}
    except Exception as e:
        return {"error": str(e)}