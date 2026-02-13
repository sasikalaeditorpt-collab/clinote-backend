from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from typing import List
from pathlib import Path
import tempfile

from app.services.doctor_profiles import DoctorProfileService
from app.services.style_engine import StyleEngineService
from app.services.docx_builder import build_styled_docx

router = APIRouter(prefix="/style", tags=["style-engine"])


@router.get("/doctors")
def get_doctors():
    return DoctorProfileService.list_doctors()


@router.post("/doctor/create")
async def create_doctor_profile(doctor_id: str = Form(...)):
    DoctorProfileService.create_doctor(doctor_id)
    return {"status": "ok", "doctor_id": doctor_id}


@router.post("/doctor/{doctor_id}/samples")
async def upload_style_samples(
    doctor_id: str,
    files: List[UploadFile] = File(...),
):
    filenames = [f.filename for f in files]
    DoctorProfileService.save_style_samples(doctor_id, filenames)
    return {"status": "ok", "doctor_id": doctor_id, "files": filenames}


@router.post("/doctor/{doctor_id}/generate")
async def generate_styled_doc(
    doctor_id: str,
    raw_draft: str = Form(...),
):
    if not DoctorProfileService.has_samples(doctor_id):
        raise HTTPException(status_code=400, detail="No style samples for this doctor")

    styled = StyleEngineService.apply(
        doctor_id=doctor_id,
        raw_draft=raw_draft,
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / f"{doctor_id}_styled_report.docx"
        build_styled_docx(
            styled_text=styled,
            template_path=None,
            output_path=output_path
        )
        return FileResponse(
            path=str(output_path),
            filename=output_path.name,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )