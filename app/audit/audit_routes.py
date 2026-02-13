from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse
import subprocess
import os
import zipfile
import shutil

from .audit_engine import process_folder_pair, extract_tracking_number, write_excel_summary

router = APIRouter()

AUDIT_DIR = r"D:\AuditEngine\Monthly"
AUDIT_ENGINE = r"D:\clinote-app\app\audit\audit_engine.py"


# ------------------------------------------------------------
# OLD DESKTOP WORKFLOW (unchanged)
# ------------------------------------------------------------
@router.post("/run")
def run_audit():
    subprocess.Popen(["python", AUDIT_ENGINE])
    return {"status": "running"}


@router.get("/reports")
def list_reports():
    if not os.path.isdir(AUDIT_DIR):
        raise HTTPException(status_code=404, detail="Audit directory not found")

    files = [f for f in os.listdir(AUDIT_DIR) if f.lower().endswith(".xlsx")]
    files.sort(reverse=True)
    return {"reports": files}


@router.get("/report/{filename}")
def download_report(filename: str):
    path = os.path.join(AUDIT_DIR, filename)

    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Report not found")

    return FileResponse(
        path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=filename
    )


# ------------------------------------------------------------
# NEW WEB WORKFLOW (ZIP → JSON + Excel)
# ------------------------------------------------------------
@router.post("/run-audit")
async def run_audit_zip(feedback_zip: UploadFile = File(...)):
    temp_root = "temp_feedback"
    if os.path.exists(temp_root):
        shutil.rmtree(temp_root)
    os.makedirs(temp_root, exist_ok=True)

    zip_path = os.path.join(temp_root, feedback_zip.filename)

    # Save uploaded ZIP
    with open(zip_path, "wb") as f:
        f.write(await feedback_zip.read())

    # Unzip
    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(temp_root)

    # Locate folder containing 0xxxx / 1xxxx pairs
    feedback_root = None
    for root, dirs, files in os.walk(temp_root):
        if any(d.startswith("0") or d.startswith("1") for d in dirs):
            feedback_root = root
            break

    if not feedback_root:
        return JSONResponse({"error": "No 0/1 folders found in ZIP"}, status_code=400)

    folders = [f for f in os.listdir(feedback_root) if os.path.isdir(os.path.join(feedback_root, f))]
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
                "typist": "PM",
                "typed": f"Typed: {d['T']}",
                "dictated": f"Dictated: {d['D']}",
            })

        unmatched.extend(unmatched_files)

    # Write Excel summary
    excel_path = write_excel_summary(all_rows, unmatched)

    return {
        "rows": all_rows,
        "excel_url": f"/report/{os.path.basename(excel_path)}"
    }