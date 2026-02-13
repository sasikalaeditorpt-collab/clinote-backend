import os
from openpyxl import Workbook
from openpyxl.styles import Alignment
from datetime import datetime

output_folder = "temp_output"
os.makedirs(output_folder, exist_ok=True)


def write_excel_summary(all_diffs, unmatched):
    timestamp = datetime.now().strftime("%m%d%y-%H%M")
    excel_path = os.path.join(output_folder, f"Feedback-{timestamp}.xlsx")

    wb = Workbook()
    ws = wb.active
    ws.title = "Audit Summary"

    ws.append(["Tracking Number", "Patient", "Typist", "Typed", "Dictated"])

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

        ws.append([tracking, patient, typist, "", ""])
        row_t = ws.max_row

        cell_t = ws.cell(row=row_t, column=4)
        cell_t.value = f"Typed: {typed_full}"
        cell_t.alignment = Alignment(wrap_text=False)

        ws.append(["", "", "", "", ""])
        row_d = ws.max_row

        cell_d = ws.cell(row=row_d, column=4)
        cell_d.value = f"Dictated: {dictated_full}"
        cell_d.alignment = Alignment(wrap_text=False)

        last_tracking = entry["tracking_number"]
        last_patient = entry["patient"]

    if unmatched:
        ws.append([])
        ws.append(["UNMATCHED FILES"])
        ws.append(["Tracking Number", "Folder", "Filename"])
        for u in unmatched:
            ws.append([u["tracking_number"], u["folder"], u["filename"]])

    wb.save(excel_path)
    return excel_path