"""
RGCO Overlay Comparison Macro
------------------------------
Simulates a Red/Green Comparison Overlay between two revisions of a part.
Diffs geometry attributes, dimensions, and material specs.

In real NX/CATIA: load two part files via API, extract geometry data,
compare face counts, body volumes, key dimensions, and attribute values.
"""

from pathlib import Path
from datetime import datetime
from core.logger import logger


# Mock part revision database
MOCK_PARTS = {
    "PN-001": {
        "A": {
            "volume_mm3": 48200.0,
            "surface_area_mm2": 18400.0,
            "faces": 24,
            "material": "Cast Iron",
            "mass_kg": 44.8,
            "dimensions": {"length": 480, "width": 220, "height": 310},
            "tolerances": {"bore_dia": "±0.02", "flatness": "0.05"},
            "holes": 12,
            "threads": 8
        },
        "B": {
            "volume_mm3": 48200.0,
            "surface_area_mm2": 18400.0,
            "faces": 24,
            "material": "Cast Iron",
            "mass_kg": 44.8,
            "dimensions": {"length": 480, "width": 220, "height": 310},
            "tolerances": {"bore_dia": "±0.02", "flatness": "0.05"},
            "holes": 12,
            "threads": 8
        },
        "C": {
            "volume_mm3": 47850.0,          # Changed — lightweighting
            "surface_area_mm2": 18650.0,    # Changed — new ribbing
            "faces": 28,                    # Changed — 4 new faces from ribs
            "material": "Compacted Graphite Iron",  # Material change
            "mass_kg": 45.2,
            "dimensions": {"length": 480, "width": 220, "height": 310},
            "tolerances": {"bore_dia": "±0.015", "flatness": "0.04"},  # Tighter
            "holes": 12,
            "threads": 10                   # 2 new threads
        }
    },
    "GB-001": {
        "A": {
            "volume_mm3": 22400.0,
            "surface_area_mm2": 14200.0,
            "faces": 18,
            "material": "Aluminium Die Cast",
            "mass_kg": 8.2,
            "dimensions": {"length": 320, "width": 180, "height": 210},
            "tolerances": {"shaft_bore": "±0.01"},
            "holes": 8,
            "threads": 6
        },
        "B": {
            "volume_mm3": 22400.0,
            "surface_area_mm2": 14200.0,
            "faces": 18,
            "material": "Aluminium Die Cast",
            "mass_kg": 8.5,                 # Weight changed
            "dimensions": {"length": 320, "width": 185, "height": 210},  # Width changed
            "tolerances": {"shaft_bore": "±0.01"},
            "holes": 10,                    # 2 new holes
            "threads": 6
        }
    }
}


def _diff_dicts(a: dict, b: dict, path: str = "") -> list:
    """Recursively diff two dicts, return list of change descriptions."""
    changes = []
    all_keys = set(a.keys()) | set(b.keys())
    for key in all_keys:
        full_key = f"{path}.{key}" if path else key
        if key not in a:
            changes.append({"field": full_key, "type": "ADDED", "old": None, "new": b[key]})
        elif key not in b:
            changes.append({"field": full_key, "type": "REMOVED", "old": a[key], "new": None})
        elif isinstance(a[key], dict) and isinstance(b[key], dict):
            changes += _diff_dicts(a[key], b[key], full_key)
        elif a[key] != b[key]:
            changes.append({"field": full_key, "type": "MODIFIED", "old": a[key], "new": b[key]})
    return changes


def _build_rgco_viewer(part_name: str, revision_a: str, revision_b: str, rev_a: dict, rev_b: dict, changes: list) -> dict:
    old_dims = rev_a.get("dimensions", {})
    new_dims = rev_b.get("dimensions", {})
    length = max(old_dims.get("length", 300), new_dims.get("length", 300))
    width = max(old_dims.get("width", 150), new_dims.get("width", 150))
    height = max(old_dims.get("height", 150), new_dims.get("height", 150))

    objects = [
        {
            "id": f"{part_name}_rev_{revision_a}_body",
            "label": f"Rev {revision_a} reference body",
            "kind": "box",
            "position": [0, 0, 0],
            "size": [
                old_dims.get("length", length),
                old_dims.get("width", width),
                old_dims.get("height", height),
            ],
            "color": "#ef4444",
            "opacity": 0.28,
            "wireframe": True,
            "semantic": "old_geometry",
        },
        {
            "id": f"{part_name}_rev_{revision_b}_body",
            "label": f"Rev {revision_b} target body",
            "kind": "box",
            "position": [0, 0, 0],
            "size": [
                new_dims.get("length", length),
                new_dims.get("width", width),
                new_dims.get("height", height),
            ],
            "color": "#22c55e",
            "opacity": 0.35,
            "wireframe": False,
            "semantic": "new_geometry",
        },
    ]

    dimension_changes = [c for c in changes if c["field"].startswith("dimensions.")]
    for index, change in enumerate(dimension_changes):
        axis = change["field"].split(".", 1)[1]
        objects.append({
            "id": f"dimension_change_{axis}",
            "label": f"{axis}: {change['old']} -> {change['new']}",
            "kind": "change_marker",
            "position": [
                0,
                (index + 1) * width * 0.18,
                height * 0.58,
            ],
            "size": [length * 0.18, width * 0.04, height * 0.04],
            "color": "#f59e0b",
            "opacity": 0.9,
            "semantic": "modified_geometry",
            "source_change": change,
        })

    count_markers = [
        c for c in changes
        if c["field"] in {"faces", "holes", "threads", "volume_mm3", "surface_area_mm2"}
    ]
    for index, change in enumerate(count_markers):
        marker_type = "added_geometry" if change["new"] and change["old"] and change["new"] > change["old"] else "modified_geometry"
        objects.append({
            "id": f"change_marker_{change['field']}",
            "label": f"{change['field']}: {change['old']} -> {change['new']}",
            "kind": "cylinder",
            "position": [
                -length * 0.36 + (index * length * 0.16),
                -width * 0.58,
                height * 0.62,
            ],
            "radius": max(min(width, height) * 0.045, 6),
            "depth": max(height * 0.16, 20),
            "color": "#22c55e" if marker_type == "added_geometry" else "#f59e0b",
            "opacity": 0.85,
            "semantic": marker_type,
            "source_change": change,
        })

    material_changes = [c for c in changes if c["field"] == "material"]
    for change in material_changes:
        objects.append({
            "id": "material_change_badge",
            "label": f"Material: {change['old']} -> {change['new']}",
            "kind": "annotation",
            "position": [0, width * 0.7, height * 0.8],
            "color": "#f59e0b",
            "semantic": "metadata_change",
            "source_change": change,
        })

    return {
        "type": "3d",
        "format": "scene-json",
        "engine": "threejs-compatible",
        "title": f"RGCO Overlay: {part_name} Rev {revision_a} vs Rev {revision_b}",
        "units": "mm",
        "camera": {
            "position": [length * 1.15, width * 1.2, height * 1.1],
            "target": [0, 0, 0],
            "fov": 45,
        },
        "legend": [
            {"label": f"Removed / Rev {revision_a}", "color": "#ef4444"},
            {"label": f"Added / Rev {revision_b}", "color": "#22c55e"},
            {"label": "Modified", "color": "#f59e0b"},
        ],
        "objects": objects,
    }


def _to_report_rows(changes: list[dict]) -> list[dict]:
    rows: list[dict] = []
    for index, change in enumerate(changes, start=1):
        status = change["type"].title()
        field_name = change["field"]
        feature = field_name.replace(".", " ").replace("_", " ").title()
        old_value = "—" if change["old"] is None else str(change["old"])
        new_value = "—" if change["new"] is None else str(change["new"])

        if change["old"] is None or change["new"] is None:
            delta = "—"
        else:
            try:
                delta_numeric = float(change["new"]) - float(change["old"])
                delta = f"{delta_numeric:+g}"
            except (TypeError, ValueError):
                delta = f"{old_value} -> {new_value}" if old_value != new_value else "0"

        rows.append({
            "id": f"chg_{index:03}",
            "feature": feature,
            "field": field_name,
            "v1_value": old_value,
            "v2_value": new_value,
            "delta": delta,
            "status": status,
            "location": "Global model",
        })
    return rows


def _build_comparison_views(
    part_name: str,
    revision_a: str,
    revision_b: str,
    rev_a: dict,
    rev_b: dict,
    changes: list[dict],
) -> dict:
    report_rows = _to_report_rows(changes)
    timestamp = datetime.now().isoformat()
    before_snapshot = {
        "snapshot_id": f"{part_name}_rev_{revision_a}_before",
        "label": f"Part Rev {revision_a} (Before)",
        "revision": revision_a,
        "kind": "synthetic-render",
        "meta": {
            "dimensions": rev_a.get("dimensions", {}),
            "material": rev_a.get("material"),
            "faces": rev_a.get("faces"),
            "volume_mm3": rev_a.get("volume_mm3"),
        },
    }
    after_snapshot = {
        "snapshot_id": f"{part_name}_rev_{revision_b}_after",
        "label": f"Part Rev {revision_b} (After)",
        "revision": revision_b,
        "kind": "synthetic-render",
        "meta": {
            "dimensions": rev_b.get("dimensions", {}),
            "material": rev_b.get("material"),
            "faces": rev_b.get("faces"),
            "volume_mm3": rev_b.get("volume_mm3"),
        },
    }

    return {
        "generated_at": timestamp,
        "part": part_name,
        "revision_a": revision_a,
        "revision_b": revision_b,
        "tabs": [
            {
                "id": "side_by_side",
                "label": "Side-by-Side 3D View",
                "type": "image_pair",
                "content": {
                    "before": before_snapshot,
                    "after": after_snapshot,
                },
            },
            {
                "id": "overlay_diff",
                "label": "Overlay Diff View",
                "type": "overlay_scene",
                "content": {
                    "viewer_ref": "viewer",
                    "legend": [
                        {"color": "#94a3b8", "meaning": "Unchanged geometry"},
                        {"color": "#ef4444", "meaning": f"Removed (Rev {revision_a})"},
                        {"color": "#22c55e", "meaning": f"Added (Rev {revision_b})"},
                        {"color": "#f59e0b", "meaning": "Modified dimensions/features"},
                    ],
                },
            },
            {
                "id": "change_report",
                "label": "Change Report",
                "type": "table",
                "content": {
                    "columns": [
                        {"key": "feature", "label": "Feature"},
                        {"key": "v1_value", "label": f"Rev {revision_a} Value"},
                        {"key": "v2_value", "label": f"Rev {revision_b} Value"},
                        {"key": "delta", "label": "Delta"},
                        {"key": "status", "label": "Status"},
                        {"key": "location", "label": "Location"},
                    ],
                    "rows": report_rows,
                },
            },
        ],
    }


def run(params: dict) -> dict:
    part_name   = params.get("part_name", "PN-001")
    revision_a  = params.get("revision_a", "B")
    revision_b  = params.get("revision_b", "C")
    persist_report = params.get("_persist_report", True)
    include_report = params.get("_include_report", False)

    logger.info(f"RGCO Comparison: {part_name} Rev {revision_a} → Rev {revision_b}")

    part_data = MOCK_PARTS.get(part_name)
    if not part_data:
        raise ValueError(f"Part '{part_name}' not found. Available: {list(MOCK_PARTS.keys())}")

    rev_a = part_data.get(revision_a)
    rev_b = part_data.get(revision_b)

    if not rev_a:
        raise ValueError(f"Revision '{revision_a}' not found for part '{part_name}'")
    if not rev_b:
        raise ValueError(f"Revision '{revision_b}' not found for part '{part_name}'")

    changes = _diff_dicts(rev_a, rev_b)

    added    = [c for c in changes if c["type"] == "ADDED"]
    removed  = [c for c in changes if c["type"] == "REMOVED"]
    modified = [c for c in changes if c["type"] == "MODIFIED"]

    overall = "NO CHANGE" if not changes else "CHANGES DETECTED"

    report_lines = [
        "RGCO OVERLAY COMPARISON REPORT",
        "=" * 50,
        f"Part      : {part_name}",
        f"Comparing : Rev {revision_a}  →  Rev {revision_b}",
        f"Date      : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Result    : {overall}",
        f"Changes   : {len(changes)} ({len(modified)} modified, {len(added)} added, {len(removed)} removed)",
        "=" * 50,
        "",
    ]

    if modified:
        report_lines.append("MODIFIED:")
        for c in modified:
            report_lines.append(f"  {c['field']:<30} {str(c['old']):<20} →  {str(c['new'])}")

    if added:
        report_lines.append("")
        report_lines.append("ADDED:")
        for c in added:
            report_lines.append(f"  {c['field']:<30} (new) {c['new']}")

    if removed:
        report_lines.append("")
        report_lines.append("REMOVED:")
        for c in removed:
            report_lines.append(f"  {c['field']:<30} was: {c['old']}")

    if not changes:
        report_lines.append("No differences found between revisions.")

    report_content = "\n".join(report_lines) + "\n"
    filename = f"RGCO_{part_name}_Rev{revision_a}_vs_Rev{revision_b}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    output_path = Path("outputs") / filename
    if persist_report:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report_content)

    logger.success(f"RGCO comparison complete: {len(changes)} changes found")

    output = {
        "overall": overall,
        "part": part_name,
        "revision_a": revision_a,
        "revision_b": revision_b,
        "total_changes": len(changes),
        "modified": len(modified),
        "added": len(added),
        "removed": len(removed),
        "report_file": str(output_path) if persist_report else None,
        "changes": changes,
        "execution": {
            "status": "completed",
            "steps": [
                {"id": "load_v1", "label": f"Load revision {revision_a}", "state": "done"},
                {"id": "load_v2", "label": f"Load revision {revision_b}", "state": "done"},
                {"id": "compare_geometry", "label": "Compare geometry and metadata", "state": "done"},
                {"id": "build_visuals", "label": "Generate side-by-side and overlay views", "state": "done"},
                {"id": "build_report", "label": "Assemble structured change report", "state": "done"},
            ],
        },
        "viewer": _build_rgco_viewer(part_name, revision_a, revision_b, rev_a, rev_b, changes),
        "comparison_views": _build_comparison_views(part_name, revision_a, revision_b, rev_a, rev_b, changes),
    }

    if include_report:
        output["report"] = {
            "filename": filename,
            "media_type": "text/plain",
            "encoding": "utf-8",
            "content": report_content,
        }

    return output
