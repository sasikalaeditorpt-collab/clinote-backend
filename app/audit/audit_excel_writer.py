import os
from datetime import datetime
from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from openpyxl.styles import Alignment


def autosize_columns(ws):
    for column_cells in ws.columns:
        max_length = 0
        column = column_cells[0].column
        for cell in column_cells:
            if cell.value:
                max_length = max(max_length, len(str(cell.value)))
        ws.column_dimensions[get_column_letter(column)].width = max_length + 2


def write_excel_summary(all_rows, unmatched):
    """
    Final legacy format:

    A: Tracking Number (only on first row of group)
    B: Patient
    C: Typist (initials only, blank if none)
    D: Multi-line cell:
           Dictated: <dictated>
           Typed: <typed>
    """

    wb = Workbook()
    ws = wb.active
    ws.title = "Audit Summary"

    # Header row
    headers = ["Tracking Number", "Patient", "Typist", "Diff"]
    ws.append(headers)

    for cell in ws[1]:
        cell.alignment = Alignment(horizontal="center", vertical="center")

    last_tracking = None

    for row in all_rows:
        tracking = row.get("tracking_number", "")
        patient = row.get("patient", "")
        typist = row.get("typist") or ""

        typed = row.get("typed") or row.get("T") or ""
        dictated = row.get("dictated") or row.get("D") or ""

        # Multi-line cell with prefixes
        diff_block = f"Dictated: {dictated}\nTyped: {typed}"

        # Only show tracking number on first row of group
        tracking_cell = tracking if tracking != last_tracking else ""

        ws.append([
            tracking_cell,
            patient,
            typist,
            diff_block
        ])

        # Ensure multi-line display
        ws[f"D{ws.max_row}"].alignment = Alignment(wrap_text=True)

        last_tracking = tracking

    autosize_columns(ws)

    # Optional unmatched sheet
    if unmatched:
        ws2 = wb.create_sheet("Unmatched Files")
        ws2.append(["Unmatched File"])
        for item in unmatched:
            ws2.append([item])
        autosize_columns(ws2)

    os.makedirs("output", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join("output", f"audit_summary_{timestamp}.xlsx")
    wb.save(path)

    return path