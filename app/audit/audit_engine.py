import os
import re
import difflib
from datetime import datetime
from docx import Document
from openpyxl import Workbook
import sys

if sys.platform == "win32":
    import pythoncom
    import win32com.client

from app.audit.audit_excel_writer import write_excel_summary

# ------------------------------------------------------------
# CONFIGURATION
# ------------------------------------------------------------
output_folder = r"D:\AuditEngine\Monthly"
os.makedirs(output_folder, exist_ok=True)


# ------------------------------------------------------------
# TRACKING NUMBER EXTRACTION
# ------------------------------------------------------------
def extract_tracking_number(folder_name):
    core = folder_name[1:]
    parts = core.split("-")
    prefix = parts[0]
    timestamp = parts[-1]
    return prefix + timestamp


# ------------------------------------------------------------
# HELPERS
# ------------------------------------------------------------
def extract_last_name(filename):
    if "," in filename:
        return filename.split(",")[0]
    return filename.split("-")[0]


def read_docx_text(path):
    try:
        doc = Document(path)
        return "\n".join([p.text for p in doc.paragraphs])
    except Exception:
        return ""


def extract_typist_initials(text):
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    if not lines:
        return ""
    last = lines[-1]
    m = re.search(r'/([A-Za-z]{1,3})$', last)
    return m.group(1).upper() if m else ""


# ------------------------------------------------------------
# DOC → DOCX CONVERSION
# ------------------------------------------------------------
def convert_doc_to_docx(doc_path):
    doc_path = os.path.abspath(doc_path)

    if doc_path.lower().endswith(".docx"):
        return doc_path

    if doc_path.lower().endswith(".doc"):
        docx_path = doc_path + "x"

        if os.path.exists(docx_path):
            return docx_path

        try:
            pythoncom.CoInitialize()
            word = win32com.client.DispatchEx("Word.Application")
            word.Visible = False

            doc = word.Documents.Open(doc_path, ReadOnly=True)
            doc.SaveAs(docx_path, FileFormat=12)

            doc.Close()
            word.Quit()

            del word
            pythoncom.CoUninitialize()

            return docx_path

        except Exception as e:
            print(f"Failed to convert {doc_path} to .docx: {e}")
            return None

    return None


def remove_doc_duplicates(files):
    cleaned = []
    docx_basenames = {f[:-5] for f in files if f.lower().endswith(".docx")}
    for f in files:
        if f.lower().endswith(".doc"):
            base = f[:-4]
            if base in docx_basenames:
                continue
        cleaned.append(f)
    return cleaned


# ------------------------------------------------------------
# MINIMAL DIFFERENCE EXTRACTOR
# ------------------------------------------------------------
def extract_minimal_change(mt_sentence, ed_sentence, context_words=5):
    mt_words = mt_sentence.split()
    ed_words = ed_sentence.split()

    matcher = difflib.SequenceMatcher(None, mt_words, ed_words)
    diffs = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag != "equal":
            mt_block = " ".join(mt_words[i1:i2]).strip()
            ed_block = " ".join(ed_words[j1:j2]).strip()
            diffs.append((i1, i2, j1, j2, mt_block, ed_block))

    if not diffs:
        return "", ""

    mt_snippets = []
    ed_snippets = []

    for i1, i2, j1, j2, mt_block, ed_block in diffs:
        mt_before = " ".join(mt_words[max(0, i1 - context_words):i1])
        mt_after = " ".join(mt_words[i2:i2 + context_words])
        mt_snippet = f"{mt_before} {mt_block} {mt_after}".strip()
        mt_snippets.append(mt_snippet)

        ed_before = " ".join(ed_words[max(0, j1 - context_words):j1])
        ed_after = " ".join(ed_words[j2:j2 + context_words])
        ed_snippet = f"{ed_before} {ed_block} {ed_after}".strip()
        ed_snippets.append(ed_snippet)

    return " | ".join(mt_snippets), " | ".join(ed_snippets)


# ------------------------------------------------------------
# SENTENCE COMPARATOR
# ------------------------------------------------------------
def compare_sentences(mt_text, ed_text):
    mt_sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', mt_text) if s.strip()]
    ed_sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', ed_text) if s.strip()]

    diffs = []
    for mt in mt_sentences:
        best_match = None
        best_ratio = 0
        for ed in ed_sentences:
            ratio = difflib.SequenceMatcher(None, mt, ed).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_match = ed
        if best_ratio < 1.0:
            t_change, d_change = extract_minimal_change(mt, best_match)
            diffs.append({"T": t_change, "D": d_change})
    return diffs


# ------------------------------------------------------------
# PROCESS FOLDER PAIR
# ------------------------------------------------------------
def process_folder_pair(mt_folder, ed_folder, tracking_number):
    mt_files = [f for f in os.listdir(mt_folder) if f.lower().endswith((".doc", ".docx"))]
    ed_files = [f for f in os.listdir(ed_folder) if f.lower().endswith((".doc", ".docx"))]

    diffs_output = []
    unmatched = []

    for mt_file in mt_files:
        mt_path = os.path.join(mt_folder, mt_file)
        mt_docx = convert_doc_to_docx(mt_path)
        if not mt_docx:
            unmatched.append({"tracking_number": tracking_number, "folder": "MT", "filename": mt_file})
            continue

        mt_text = read_docx_text(mt_docx)

        best_match = None
        best_ratio = 0
        for ed_file in ed_files:
            ratio = difflib.SequenceMatcher(None, mt_file, ed_file).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_match = ed_file

        if best_ratio < 0.70:
            unmatched.append({"tracking_number": tracking_number, "folder": "MT", "filename": mt_file})
            continue

        ed_path = os.path.join(ed_folder, best_match)
        ed_docx = convert_doc_to_docx(ed_path)
        if not ed_docx:
            unmatched.append({"tracking_number": tracking_number, "folder": "ED", "filename": best_match})
            continue

        ed_text = read_docx_text(ed_docx)
        typist = extract_typist_initials(ed_text)

        ed_text = read_docx_text(ed_docx)
        differences = compare_sentences(mt_text, ed_text)
        last_name = extract_last_name(mt_file)

        for d in differences:
            diffs_output.append({
                "tracking_number": tracking_number,
                "patient": last_name,
                "typist": typist,
                "T": d["T"],
                "D": d["D"]
            })

    return diffs_output, unmatched


# ------------------------------------------------------------
# MAIN ENGINE (desktop workflow)
# ------------------------------------------------------------
if __name__ == "__main__":
    feedback_root = r"D:\AuditEngine\Feedback"

    all_diffs = []
    unmatched = []

    folders = [f for f in os.listdir(feedback_root) if os.path.isdir(os.path.join(feedback_root, f))]

    mt_folders = [f for f in folders if f.startswith("1")]
    ed_folders = [f for f in folders if f.startswith("0")]

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

        all_diffs.extend(diffs)
        unmatched.extend(unmatched_files)

    write_excel_summary(all_diffs, unmatched)

    # Desktop-only notification block
    from app.audit.audit_state import set_finished
    from app.audit.audit_events import broadcast
    from app.audit.audit_routes import cleanup_reports

    monthly_dir = r"D:\AuditEngine\Monthly"
    files = [f for f in os.listdir(monthly_dir) if f.lower().endswith(".xlsx")]

    if files:
        latest = sorted(files, reverse=True)[0]
        set_finished(latest)
        broadcast(f'{{"status":"finished","report":"{latest}"}}')
        cleanup_reports()