from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse
import subprocess
import os
import zipfile
import shutil

from app.audit.audit_engine import (
    process_folder_pair,
    extract_tracking_number,
)

from app.audit.audit_excel_writer import write_excel_summary

router = APIRouter()


@router.post("/run")
def run_audit():
    subprocess.Popen(["python", r"D:\clinote-app\app\audit\audit_engine.py"])
    return {"status": "running"}


@router.post("/run-audit")
async def run_audit_zip(feedback_zip: UploadFile = File(...)):
    temp_root = "temp_feedback"
    if os.path.exists(temp_root):
        shutil.rmtree(temp_root)
    os.makedirs(temp_root, exist_ok=True)

    zip_path = os.path.join(temp_root, feedback_zip.filename)

    with open(zip_path, "wb") as f:
        f.write(await feedback_zip.read())

    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(temp_root)

    feedback_root = None
    for root, dirs, files in os.walk(temp_root):
        if any(d.startswith("0") or d.startswith("1") for d in dirs):
            feedback_root = root
            break

    if not feedback_root:
        return JSONResponse({"error": "No 0/1 folders found in ZIP"}, status_code=400)

    folders = [
        f for f in os.listdir(feedback_root)
        if os.path.isdir(os.path.join(feedback_root, f))
    ]

    mt_folders = [f for f in folders if f.startswith("1")]
    ed_folders = [f for f in folders if f.startswith("0")]

    all_rows = []
    unmatched = []

    for ed in ed_folders:
        core = ed[1:]
        mt = "1" + core

        mt_path = os.path.join(feedback_root, mt)
        ed_path = os.path.join(feedback_root, ed)

        if not os.path.isdir(mt_path):
            continue

        diffs, unmatched_files = process_folder_pair(
            mt_path, ed_path, extract_tracking_number(ed)
        )

        for d in diffs:
            all_rows.append({
                "tracking_number": d["tracking_number"],
                "patient": d["patient"],
                "typist": d["typist"],
                "typed": d["T"],
                "dictated": d["D"],
                "T": d["T"],
                "D": d["D"],
            })

        unmatched.extend(unmatched_files)

    excel_path = write_excel_summary(all_rows, unmatched)

    return FileResponse(
        excel_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=os.path.basename(excel_path)
    )