# force render redeploy — header cleanup + color support

import os
from openpyxl import Workbook
from openpyxl.styles import Alignment
from openpyxl.cell.rich_text import CellRichText, TextBlock
from openpyxl.styles import Font
from datetime import datetime

output_folder = "temp_output"
os.makedirs(output_folder, exist_ok=True)


def build_rich_text_cell(word_runs):
    """
    word_runs = [
        ("She says the ", None),
        ("#19", "FF0000"),   # red
        (" is loose.", None)
    ]
    """
    blocks = []
    for text, color in word_runs:
        if color:
            blocks.append(TextBlock(text, Font(color=color)))
        else:
            blocks.append(TextBlock(text, Font(color="000000")))
    return CellRichText(*blocks)


def write_excel_summary(all_diffs, unmatched):
    timestamp = datetime.now().strftime("%m%d%y-%H%M")
    excel_path = os.path.join(output_folder, f"Feedback-{timestamp}.xlsx")

    wb = Workbook()
    ws = wb.active
    ws.title = "Audit Summary"

    # ⭐ UPDATED HEADER — remove "Typed" and "Dictated"
    ws.append(["Tracking Number", "Patient", "Typist", "", ""])

    ws.column_dimensions["A"].width = 20
    ws.column_dimensions["B"].width = 20
    ws.column_dimensions["C"].width = 12
    ws.column_dimensions["D"].width = 60
    ws.column_dimensions["E"].width = 60

    last_tracking = None
    last_patient = None

    for entry in all_diffs:
        tracking = entry["tracking_number"] if entry["tracking_number"] != last_tracking else ""
        patient = entry["patient"] if entry["patient"] != last_patient else ""
        typist = entry.get("typist", "")

        typed_full = entry.get("typed", "")
        dictated_full = entry.get("dictated", "")

        # ⭐ These come from your diff engine (fallback = plain text)
        typed_runs = entry.get("typed_runs", [(typed_full, None)])
        dictated_runs = entry.get("dictated_runs", [(dictated_full, None)])

        # Row for Typed
        ws.append([tracking, patient, typist, "", ""])
        row_t = ws.max_row

        cell_t = ws.cell(row=row_t, column=4)
        cell_t.value = build_rich_text_cell(typed_runs)
        cell_t.alignment = Alignment(wrap_text=False)

        # Row for Dictated
        ws.append(["", "", "", "", ""])
        row_d = ws.max_row

        cell_d = ws.cell(row=row_d, column=4)
        cell_d.value = build_rich_text_cell(dictated_runs)
        cell_d.alignment = Alignment(wrap_text=False)

        last_tracking = entry["tracking_number"]
        last_patient = entry["patient"]

    # Unmatched section
    if unmatched:
        ws.append([])
        ws.append(["UNMATCHED FILES"])
        ws.append(["Tracking Number", "Folder", "Filename"])
        for u in unmatched:
            ws.append([u["tracking_number"], u["folder"], u["filename"]])

    wb.save(excel_path)
    return excel_path