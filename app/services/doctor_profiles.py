print("LOADING doctor_profiles.py FROM:", __file__)
from typing import List
from google.cloud import storage
from docx import Document
import io

BUCKET_NAME = "clinote-style-samples"
PREFIX_ROOT = ""


class DoctorProfileService:

    @staticmethod
    def _get_gcs_client() -> storage.Client:
        return storage.Client()

    @staticmethod
    def list_doctors() -> List[str]:
        """
        Returns all doctor IDs by listing folder names under:
        gs://clinote-style-samples/<doctor_id>/
        """
        client = DoctorProfileService._get_gcs_client()
        bucket = client.bucket(BUCKET_NAME)

        iterator = bucket.list_blobs(prefix=PREFIX_ROOT, delimiter="/")

        doctor_ids = []
        for page in iterator.pages:
            for prefix in page.prefixes:
                # Example prefix: "1234/"
                doctor_id = prefix.rstrip("/")
                if doctor_id.isdigit():
                    doctor_ids.append(doctor_id)

        return sorted(doctor_ids)

    @staticmethod
    def _list_sample_files(doctor_id: str) -> List[str]:
        """
        Returns all .docx object names under:
        <doctor_id>/
        """
        client = DoctorProfileService._get_gcs_client()
        bucket = client.bucket(BUCKET_NAME)

        prefix = f"{PREFIX_ROOT}{doctor_id}/"
        print("DEBUG PREFIX USED:", prefix)

        iterator = bucket.list_blobs(prefix=prefix)

        files = []
        for blob in iterator:
            name = blob.name.lower()
            if name.endswith(".docx"):
                files.append(blob.name)

        return files

    @staticmethod
    def _read_docx_from_gcs(blob) -> str:
        """
        Downloads a .docx file from GCS and extracts text.
        """
        data = blob.download_as_bytes()
        file_stream = io.BytesIO(data)
        doc = Document(file_stream)

        lines = []
        for para in doc.paragraphs:
            text = para.text.strip()
            if text:
                lines.append(text)

        return "\n".join(lines).strip()

    @staticmethod
    def get_style_samples(doctor_id: str) -> List[str]:
        """
        Loads all .docx samples from:
        gs://clinote-style-samples/<doctor_id>/
        """
        client = DoctorProfileService._get_gcs_client()
        bucket = client.bucket(BUCKET_NAME)

        file_names = DoctorProfileService._list_sample_files(doctor_id)
        if not file_names:
            return []

        samples = []
        for name in file_names:
            blob = bucket.blob(name)
            try:
                text = DoctorProfileService._read_docx_from_gcs(blob)
                if text:
                    samples.append(text)
            except Exception:
                continue

        return samples

    # ------------------------------------------------------------
    # NEW METHOD — REQUIRED FOR UPLOAD ENDPOINT
    # ------------------------------------------------------------
    @staticmethod
    def upload_sample(doctor_id: str, file_name: str, file_bytes: bytes) -> str:
        """
        Uploads a .docx file to:
        gs://clinote-style-samples/<doctor_id>/<file_name>
        """
        client = DoctorProfileService._get_gcs_client()
        bucket = client.bucket(BUCKET_NAME)

        object_name = f"{doctor_id}/{file_name}"
        blob = bucket.blob(object_name)
        blob.upload_from_string(file_bytes)

        print("DEBUG UPLOAD PATH:", object_name)

        return object_name

    # ------------------------------------------------------------
    # Obsolete local‑filesystem functions (kept as no‑ops)
    # ------------------------------------------------------------
    @staticmethod
    def get_doctor_folder(doctor_id: str):
        return None

    @staticmethod
    def create_doctor(doctor_id: str) -> None:
        return None

    @staticmethod
    def save_style_samples(doctor_id: str, filenames: List[str]) -> None:
        return None

    @staticmethod
    def has_samples(doctor_id: str) -> bool:
        """
        Returns True if <doctor_id>/ contains at least one .docx file.
        """
        return len(DoctorProfileService._list_sample_files(doctor_id)) > 0