from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router as health_router
from app.api.transcribe import router as transcribe_router
from app.api.audit import router as audit_router
from app.api.routes_style_engine import router as style_engine_router
from app.api.routes_doctors import router as doctors_router

from app.services.doctor_profiles import DoctorProfileService

app = FastAPI()

# ------------------------------------------------------------
# CORS CONFIGURATION
# ------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*",  # optional, but safe for development
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
app.include_router(audit_router)
app.include_router(style_engine_router)
app.include_router(doctors_router)

# ------------------------------------------------------------
# DIRECT UPLOAD ENDPOINT (NEW)
# ------------------------------------------------------------
@app.post("/doctors/{doctor_id}/samples/upload")
async def upload_sample(doctor_id: str, file: UploadFile = File(...)):
    """
    Upload a .docx sample directly into GCS under:
    gs://clinote-style-samples/<doctor_id>/<filename>
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