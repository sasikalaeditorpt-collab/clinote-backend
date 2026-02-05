from fastapi import FastAPI, UploadFile, File
import whisper
from docx import Document
from docx.shared import Pt
import tempfile

app = FastAPI()

# Load Whisper model once at startup
model = whisper.load_model("medium")

@app.post("/transcribe-docx")
async def transcribe_docx(file: UploadFile = File(...)):
    # Save uploaded audio to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    # Transcribe audio
    result = model.transcribe(tmp_path)
    text = result["text"]

    # Create DOCX
    doc = Document()
    style = doc.styles["Normal"]
    font = style.font
    font.name = "Times New Roman"
    font.size = Pt(12)

    for line in text.split("\n"):
        doc.add_paragraph(line.strip())

    # Save DOCX to temp file and return it
    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp_docx:
        doc.save(tmp_docx.name)
        tmp_docx.seek(0)
        return tmp_docx.read()