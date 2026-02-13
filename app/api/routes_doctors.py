from fastapi import APIRouter
from app.services.doctor_profiles import DoctorProfileService

router = APIRouter()

@router.get("/list-doctors")
def list_doctors():
    return {"doctors": DoctorProfileService.list_doctors()}

@router.get("/sample-count")
def sample_count(doctor_id: str):
    files = DoctorProfileService._list_sample_files(doctor_id)
    return {"count": len(files)}

@router.get("/has-samples")
def has_samples(doctor_id: str):
    return {"has_samples": DoctorProfileService.has_samples(doctor_id)}