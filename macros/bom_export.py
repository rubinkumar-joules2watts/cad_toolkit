"""
BOM Export Macro
----------------
Simulates extracting a Bill of Materials from an assembly tree
and exporting it to Excel.

In real NX/CATIA: replace MOCK_ASSEMBLY with NX Open API calls
to traverse the actual part tree and read attributes.
"""

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from pathlib import Path
from datetime import datetime
from core.logger import logger


# Mock assembly tree — simulates data from NX/CATIA assembly
MOCK_ASSEMBLIES = {
    "ENGINE_BLOCK_v3": [
        {"part_no": "PN-001", "description": "Cylinder Block",     "material": "Cast Iron",      "qty": 1,  "revision": "C", "weight_kg": 45.2},
        {"part_no": "PN-002", "description": "Piston",             "material": "Aluminium Alloy","qty": 6,  "revision": "B", "weight_kg": 0.8},
        {"part_no": "PN-003", "description": "Crankshaft",         "material": "Forged Steel",   "qty": 1,  "revision": "D", "weight_kg": 12.5},
        {"part_no": "PN-004", "description": "Connecting Rod",     "material": "Alloy Steel",    "qty": 6,  "revision": "A", "weight_kg": 0.6},
        {"part_no": "PN-005", "description": "Camshaft",           "material": "Chilled Iron",   "qty": 2,  "revision": "B", "weight_kg": 3.2},
        {"part_no": "PN-006", "description": "Valve (Intake)",     "material": "Stainless Steel","qty": 12, "revision": "A", "weight_kg": 0.1},
        {"part_no": "PN-007", "description": "Valve (Exhaust)",    "material": "Nimonic Alloy",  "qty": 12, "revision": "A", "weight_kg": 0.1},
        {"part_no": "PN-008", "description": "Oil Pump",           "material": "Aluminium",      "qty": 1,  "revision": "C", "weight_kg": 1.4},
        {"part_no": "PN-009", "description": "Timing Chain",       "material": "Carbon Steel",   "qty": 1,  "revision": "B", "weight_kg": 0.5},
        {"part_no": "PN-010", "description": "Head Gasket",        "material": "Multi-layer Steel","qty": 1, "revision": "E", "weight_kg": 0.3},
    ],
    "GEARBOX_ASSY": [
        {"part_no": "GB-001", "description": "Gearbox Housing",    "material": "Aluminium Die Cast","qty": 1, "revision": "B", "weight_kg": 8.5},
        {"part_no": "GB-002", "description": "Input Shaft",        "material": "Case Hardened Steel","qty": 1,"revision": "A", "weight_kg": 2.1},
        {"part_no": "GB-003", "description": "Output Shaft",       "material": "Case Hardened Steel","qty": 1,"revision": "A", "weight_kg": 3.4},
        {"part_no": "GB-004", "description": "Synchromesh Ring",   "material": "Brass",           "qty": 6, "revision": "C", "weight_kg": 0.2},
        {"part_no": "GB-005", "description": "Gear Selector Fork", "material": "Steel",           "qty": 3, "revision": "A", "weight_kg": 0.4},
    ]
}


def run(params: dict) -> dict:
    assembly_name = params.get("assembly_name", "ENGINE_BLOCK_v3")
    output_format = params.get("output_format", "xlsx")

    logger.info(f"BOM Export started for assembly: {assembly_name}")

    parts = MOCK_ASSEMBLIES.get(assembly_name)
    if not parts:
        available = list(MOCK_ASSEMBLIES.keys())
        raise ValueError(f"Assembly '{assembly_name}' not found. Available: {available}")

    output_path = Path(f"outputs/BOM_{assembly_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Bill of Materials"

    # Header styling
    header_fill = PatternFill("solid", fgColor="1F3864")
    header_font = Font(bold=True, color="FFFFFF", size=11)
    headers = ["Part No", "Description", "Material", "Qty", "Revision", "Weight (kg)", "Total Weight (kg)"]

    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=h)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center")

    # Data rows
    alt_fill = PatternFill("solid", fgColor="EBF0FA")
    for row_idx, part in enumerate(parts, 2):
        total_weight = round(part["qty"] * part["weight_kg"], 3)
        row_data = [
            part["part_no"], part["description"], part["material"],
            part["qty"], part["revision"], part["weight_kg"], total_weight
        ]
        for col, val in enumerate(row_data, 1):
            cell = ws.cell(row=row_idx, column=col, value=val)
            if row_idx % 2 == 0:
                cell.fill = alt_fill
            cell.alignment = Alignment(horizontal="center" if col != 2 else "left")

    # Column widths
    ws.column_dimensions["A"].width = 12
    ws.column_dimensions["B"].width = 28
    ws.column_dimensions["C"].width = 22
    for col in ["D", "E", "F", "G"]:
        ws.column_dimensions[col].width = 16

    wb.save(output_path)

    total_parts = len(parts)
    total_weight = round(sum(p["qty"] * p["weight_kg"] for p in parts), 2)
    logger.success(f"BOM exported: {total_parts} parts, {total_weight}kg total → {output_path}")

    return {
        "file": str(output_path),
        "assembly": assembly_name,
        "total_parts": total_parts,
        "total_weight_kg": total_weight
    }
