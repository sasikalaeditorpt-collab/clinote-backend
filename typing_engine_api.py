from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router as health_router
from app.api.transcribe import router as transcribe_router
from app.api.audit import router as audit_router
from app.api.routes_style_engine import router as style_engine_router
from app.api.routes_doctors import router as doctors_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(transcribe_router)
app.include_router(audit_router)
app.include_router(style_engine_router)
app.include_router(doctors_router)