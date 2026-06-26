"""Core document classification + extraction pipeline.

For each document image:
1. Send it to Gemini with a prompt describing all 10 known document types
   and their required fields, asking it to classify AND extract in one call.
2. Run regex format-validation on any field that has a checkable pattern
   (Aadhaar number, PAN, IFSC, dates, etc.) and downgrade confidence if the
   model's answer doesn't match the expected format.
3. Flag any field below CONFIDENCE_THRESHOLD, and any document classified
   as "unsupported" (not one of the 10 known types).
"""
import json
import os
import re
from pathlib import Path

from google import genai
from google.genai import types
from dotenv import load_dotenv

from schemas import DOCUMENT_TYPES, CONFIDENCE_THRESHOLD, HANDWRITTEN_TYPES

load_dotenv()
client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))

MODEL_NAME = "gemini-2.5-flash"  # free tier, multimodal, strong at handwriting/OCR


def _build_prompt() -> str:
    type_list = "\n".join(
        f'- "{key}" ({info["label"]}): fields = {list(info["fields"].keys())}'
        for key, info in DOCUMENT_TYPES.items()
    )
    return f"""You are a document classification and extraction system for an
insurance company's onboarding pipeline. You will be shown ONE document image.

Known document types and the fields to extract for each:
{type_list}

Instructions:
1. Classify the document as exactly one of the keys above, OR "unsupported"
   if it clearly doesn't match any of them.
2. If it's a known type, extract ALL fields listed for that type. For each
   field, give:
   - "value": the extracted text (string), or null if genuinely not present/illegible
   - "confidence": your honest confidence (0.0 to 1.0) that the value is
     EXACTLY correct - be conservative, especially for handwritten text,
     cursive, smudges, or ambiguous characters (e.g. is that a 0 or O? a 1 or 7?)
   - "legible": true if the source text was clearly readable, false if you
     had to guess/infer due to poor handwriting, image quality, or occlusion
3. If "unsupported", return empty fields.
4. Never guess a plausible-looking value with high confidence just because it
   fits a pattern - if you're not sure, say so with a low confidence score.

Respond with ONLY valid JSON, no markdown formatting, in this exact shape:
{{
  "document_type": "<one of the keys above, or 'unsupported'>",
  "type_confidence": <0.0 to 1.0>,
  "fields": {{
    "<field_name>": {{"value": <string or null>, "confidence": <0.0-1.0>, "legible": <true/false>}}
  }}
}}
"""


PROMPT = _build_prompt()


def classify_and_extract(image_path: Path) -> dict:
    """Sends one document image to Gemini, returns the raw parsed JSON result."""
    image_bytes = image_path.read_bytes()
    mime_type = "image/png" if image_path.suffix.lower() == ".png" else "image/jpeg"

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=[
            PROMPT,
            types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
        ],
        config=types.GenerateContentConfig(
            temperature=0,
            response_mime_type="application/json",
        ),
    )
    return json.loads(response.text)


def apply_format_validation(doc_type: str, fields: dict) -> dict:
    """Cross-checks each field's value against its expected regex format (if
    any). If the model's value doesn't match the expected format, the field's
    confidence is capped low and a validation note is attached - this catches
    cases where the model is confidently wrong, not just visibly unsure.
    """
    if doc_type not in DOCUMENT_TYPES:
        return fields

    patterns = DOCUMENT_TYPES[doc_type]["fields"]
    for field_name, field_data in fields.items():
        pattern = patterns.get(field_name)
        value = field_data.get("value")
        if pattern and value:
            cleaned = value.strip()
            if not re.match(pattern, cleaned):
                field_data["confidence"] = min(field_data.get("confidence", 0), 0.4)
                field_data["validation_note"] = (
                    f"Value '{cleaned}' does not match expected format for {field_name}"
                )
        field_data.setdefault("validation_note", None)
    return fields


def process_document(image_path: Path) -> dict:
    """Runs the full pipeline for one document and returns a structured result
    ready to be saved as JSON, including which fields/doc need human review.
    """
    result = classify_and_extract(image_path)
    doc_type = result.get("document_type", "unsupported")
    fields = result.get("fields", {})
    fields = apply_format_validation(doc_type, fields)

    flagged_fields = [
        {
            "field": name,
            "value": data.get("value"),
            "confidence": data.get("confidence"),
            "reason": (
                data.get("validation_note")
                or ("illegible" if not data.get("legible", True) else "low_confidence")
            ),
        }
        for name, data in fields.items()
        if data.get("confidence", 0) < CONFIDENCE_THRESHOLD
    ]

    doc_flagged = doc_type == "unsupported" or result.get("type_confidence", 1) < CONFIDENCE_THRESHOLD

    return {
        "file": image_path.name,
        "document_type": doc_type,
        "type_confidence": result.get("type_confidence"),
        "is_handwritten_type": doc_type in HANDWRITTEN_TYPES,
        "fields": fields,
        "flagged_fields": flagged_fields,
        "document_flagged_for_review": doc_flagged or bool(flagged_fields),
        "flag_reason": (
            "Document type not recognised as one of the 10 known types"
            if doc_type == "unsupported"
            else (f"{len(flagged_fields)} field(s) below confidence threshold" if flagged_fields else None)
        ),
    }
