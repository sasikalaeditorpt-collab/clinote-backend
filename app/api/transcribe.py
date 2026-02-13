from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from docx import Document
from docx.shared import Pt
import tempfile

from app.services.whisper_service import transcribe_audio
from app.services.style_engine import StyleEngineService
from app.services.docx_builder import build_styled_docx
from app.services.doctor_profiles import DoctorProfileService
from app.core.logging_config import setup_logging

logger = setup_logging()
router = APIRouter()

@router.post("/transcribe-docx")
async def transcribe_docx(
    doctor_id: str = Form(...),
    file: UploadFile = File(...)
):
    logger.info(f"Received file: {file.filename} for doctor {doctor_id}")

    # Validate doctor has samples
    if not DoctorProfileService.has_samples(doctor_id):
        raise HTTPException(
            status_code=400,
            detail="This doctor does not have enough style samples."
        )

    # Save uploaded audio
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    logger.info("Audio saved, starting transcription")

    # Whisper transcription
    raw_text = transcribe_audio(tmp_path)

    logger.info("Transcription complete, applying style engine")

    # Apply style engine
    styled_text = StyleEngineService.apply(
        doctor_id=doctor_id,
        raw_draft=raw_text
    )

    logger.info("Style engine applied, generating styled DOCX")

    # Build styled DOCX
    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp_docx:
        build_styled_docx(
            styled_text=styled_text,
            template_path=None,
            output_path=tmp_docx.name
        )
        docx_path = tmp_docx.name

    logger.info(f"Styled DOCX created at {docx_path}")

    return FileResponse(
        docx_path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=f"{doctor_id}_styled_draft.docx"
    )