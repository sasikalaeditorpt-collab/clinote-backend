import os
from datetime import datetime
from openpyxl import Workbook
from openpyxl.styles import Alignment


def write_excel_summary(all_rows, unmatched):
    """
    Produce a legacy-style narrative audit report in Excel.

    Format:
        TrackingNumber   Patient

            Typist: <typist>
            Typed: <typed>
            Dictated: <dictated>

            Typist: <typist>
            Typed: <typed>
            Dictated: <dictated>

        (blank line)
        (next patient)
    """

    wb = Workbook()
    ws = wb.active
    ws.title = "Audit Summary"

    # Header row
    ws.append(["Audit Summary"])
    ws["A1"].alignment = Alignment(horizontal="left", vertical="top")

    # Group rows by tracking number + patient
    grouped = {}
    for row in all_rows:
        key = (row.get("tracking_number"), row.get("patient"))
        grouped.setdefault(key, []).append(row)

    # Write each patient block
    for (tracking, patient), diffs in grouped.items():

        # Patient header
        ws.append([f"{tracking}    {patient}"])
        ws.append([""])  # blank line after header

        for d in diffs:
            typist = d.get("typist") or ""
            typed = d.get("typed") or ""
            dictated = d.get("dictated") or ""

            # Four-space indentation
            ws.append([f"    Typist: {typist}"])
            ws.append([f"    Typed: {typed}"])
            ws.append([f"    Dictated: {dictated}"])
            ws.append([""])  # blank line between diff pairs

        ws.append([""])  # blank line between patients

    # Optional unmatched sheet
    if unmatched:
        ws2 = wb.create_sheet("Unmatched Files")
        ws2.append(["Unmatched File"])
        for item in unmatched:
            ws2.append([item])

    # Save output
    os.makedirs("output", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    excel_path = os.path.join("output", f"audit_summary_{timestamp}.xlsx")
    wb.save(excel_path)

    return excel_path