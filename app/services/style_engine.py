from typing import List
import os
from openai import OpenAI

from app.services.doctor_profiles import DoctorProfileService


def _cleanup_text(text: str) -> str:
    lines = [line.strip() for line in text.splitlines()]
    cleaned = []
    for line in lines:
        if line == "" and (not cleaned or cleaned[-1] == ""):
            continue
        cleaned.append(line)
    return "\n".join(cleaned).strip()


def _build_prompt(style_samples: List[str], raw_draft: str) -> str:
    samples_block = "\n\n--- EDITED SAMPLE ---\n\n".join(style_samples)

    prompt = f"""
You are a clinical documentation editor.

Rewrite the RAW DRAFT into a clean, professional clinical note.
Match the style, structure, tone, formatting, and clinical conventions shown in the EDITED SAMPLES.
Preserve all clinical meaning.
Do not invent new findings.
Fix grammar, punctuation, and formatting.
Follow the paragraph structure and sectioning patterns in the samples.

EDITED SAMPLES:
{samples_block}

RAW DRAFT:
{raw_draft}

Now produce the FINAL EDITED NOTE only.
"""
    return prompt.strip()


class StyleEngineService:
    @staticmethod
    def _get_style_samples_for_doctor(doctor_id: str) -> List[str]:
        return DoctorProfileService.get_style_samples(doctor_id)

    @staticmethod
    def apply(doctor_id: str, raw_draft: str) -> str:
        # Clean raw draft
        raw_draft = _cleanup_text(raw_draft)

        # Load style samples
        style_samples = StyleEngineService._get_style_samples_for_doctor(doctor_id)
        if not style_samples:
            return raw_draft

        # Build prompt
        prompt = _build_prompt(style_samples, raw_draft)

        # Create OpenAI client *inside* the function (safe for Render)
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        # Call the model
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert clinical documentation editor."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )

        styled_text = response.choices[0].message.content.strip()
        return styled_text