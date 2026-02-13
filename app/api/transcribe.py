from fastapi import APIRouter, UploadFile, File
from fastapi.responses import FileResponse
from docx import Document
from docx.shared import Pt
import tempfile

from app.services.whisper_service import transcribe_audio
from app.core.logging_config import setup_logging

logger = setup_logging()
router = APIRouter()

@router.post("/transcribe-docx")
async def transcribe_docx(file: UploadFile = File(...)):
    logger.info(f"Received file: {file.filename}")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    logger.info("Audio saved, starting transcription")

    text = transcribe_audio(tmp_path)

    logger.info("Transcription complete, generating DOCX")

    doc = Document()
    style = doc.styles["Normal"]
    font = style.font
    font.name = "Times New Roman"
    font.size = Pt(12)

    for line in text.split("\n"):
        doc.add_paragraph(line.strip())

    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp_docx:
        doc.save(tmp_docx.name)
        docx_path = tmp_docx.name

    logger.info(f"DOCX created at {docx_path}")

    return FileResponse(
        docx_path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename="transcription.docx"
    )