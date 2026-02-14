# app/api/convert_to_pdf.py

import os
import shutil
import subprocess
import tempfile
from datetime import datetime
from typing import List

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse

router = APIRouter(tags=["ConvertToPdf"])

ALLOWED_EXTENSIONS = {".doc", ".docx", ".xls", ".xlsx"}


def run_soffice_convert(input_path: str, output_dir: str, target: str = "pdf"):
    """
    Run LibreOffice headless conversion.
    """
    cmd = [
        "soffice",
        "--headless",
        "--convert-to",
        target,
        "--outdir",
        output_dir,
        input_path,
    ]
    try:
        subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"LibreOffice conversion failed for {input_path}: "
            f"{e.stderr.decode(errors='ignore')}"
        )


@router.post("/pdf")
async def convert_to_pdf(
    files: List[UploadFile] = File(..., description="Upload multiple files")
):
    """
    Accept multiple .doc/.docx/.xls/.xlsx files,
    convert all to PDF using LibreOffice,
    bundle into a single ZIP,
    and return it as a download.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded.")

    work_dir = tempfile.mkdtemp(prefix="convertpdf_")
    input_dir = os.path.join(work_dir, "input")
    output_dir = os.path.join(work_dir, "output")
    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    try:
        # Save uploaded files
        saved_files = []
        for f in files:
            filename = f.filename or ""
            ext = os.path.splitext(filename)[1].lower()

            if ext not in ALLOWED_EXTENSIONS:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported file type: {filename}",
                )

            dest_path = os.path.join(input_dir, filename)
            with open(dest_path, "wb") as out_f:
                out_f.write(await f.read())
            saved_files.append(dest_path)

        # Convert all to PDF
        for path in saved_files:
            ext = os.path.splitext(path)[1].lower()

            # Optional: .doc → .docx first
            if ext == ".doc":
                run_soffice_convert(path, input_dir, target="docx")
                path = os.path.splitext(path)[0] + ".docx"

            run_soffice_convert(path, output_dir, target="pdf")

        # Create ZIP
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_name = f"converted_{timestamp}.zip"
        zip_path = os.path.join(work_dir, zip_name)

        shutil.make_archive(
            base_name=os.path.splitext(zip_path)[0],
            format="zip",
            root_dir=output_dir,
        )

        return FileResponse(
            zip_path,
            media_type="application/zip",
            filename=zip_name,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)