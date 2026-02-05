from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse
from openai import OpenAI
from docx import Document
from docx.shared import Pt
import tempfile
import os

app = FastAPI()
client = OpenAI()  # Uses OPENAI_API_KEY from environment


@app.post("/transcribe-docx")
async def transcribe_docx(file: UploadFile = File(...)):
    # Save uploaded audio to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    # Send audio to OpenAI Whisper API
    with open(tmp_path, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
        )

    text = transcript.text

    # Create DOCX
    doc = Document()
    style = doc.styles["Normal"]
    font = style.font
    font.name = "Times New Roman"
    font.size = Pt(12)

    for line in text.split("\n"):
        line = line.strip()
        if line:
            doc.add_paragraph(line)

    # Save DOCX to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp_docx:
        doc.save(tmp_docx.name)
        docx_path = tmp_docx.name

    # Stream DOCX back to client
    def iterfile():
        with open(docx_path, "rb") as f:
            yield from f
        os.remove(docx_path)
        os.remove(tmp_path)

    return StreamingResponse(
        iterfile(),
        media_type=(
            "application/vnd.openxmlformats-officedocument."
            "wordprocessingml.document"
        ),
        headers={
            "Content-Disposition": 'attachment; filename="transcription.docx"'
        },
    )