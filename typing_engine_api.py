from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# ------------------------------------------------------------
# IMPORT ROUTERS
# ------------------------------------------------------------
from app.api.health import router as health_router
from app.api.transcribe import router as transcribe_router
from app.api.audit import router as audit_router
from app.api.routes_style_engine import router as style_engine_router
from app.api.routes_doctors import router as doctors_router

# NEW ROUTERS
from app.api.convert_doc_to_docx import router as doc_to_docx_router
from app.api.convert_to_pdf import router as convert_to_pdf_router

from app.services.doctor_profiles import DoctorProfileService

# ------------------------------------------------------------
# CREATE APP
# ------------------------------------------------------------
app = FastAPI()

# ------------------------------------------------------------
# CORS CONFIGURATION
# ------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------
# ROUTERS
# ------------------------------------------------------------
app.include_router(health_router)
app.include_router(transcribe_router)
app.include_router(audit_router, prefix="/audit")
app.include_router(style_engine_router)
app.include_router(doctors_router)

# NEW ROUTERS
app.include_router(doc_to_docx_router, prefix="/doc-to-docx", tags=["DocToDocx"])
app.include_router(convert_to_pdf_router, prefix="/convert", tags=["ConvertToPdf"])

# ------------------------------------------------------------
# DIRECT SAMPLE UPLOAD ENDPOINT
# ------------------------------------------------------------
@app.post("/doctors/{doctor_id}/samples/upload")
async def upload_sample(doctor_id: str, file: UploadFile = File(...)):
    """
    Upload a .docx sample directly into GCS under:
    gs://<bucket>/<doctor_id>/samples/<filename>
    """
    try:
        content = await file.read()

        object_name = DoctorProfileService.upload_sample(
            doctor_id,
            file.filename,
            content
        )

        return {"uploaded": object_name}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))