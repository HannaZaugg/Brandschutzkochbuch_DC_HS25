from __future__ import annotations

from pathlib import Path
from typing import List, Optional

import pandas as pd

from processors.height import HeightResult
from processors.area import AreaResult
from processors.vkf_rules import small_building_comment, storey_area_comment


def _build_rows(
    height_result: HeightResult,
    area_result: AreaResult,
    extra_columns: Optional[dict[str, str]] = None,
) -> List[dict[str, str]]:
    """Erzeugt die feste Tabellenstruktur mit Überschriften und Antworten."""
    extra_columns = extra_columns or {}

    def answer(label: str) -> str:
        return extra_columns.get(label, "-")

    rows: List[dict[str, str]] = []

    rows.append({"Beschrieb": "Objektinformationen", "Antwort/Wert": "", "VKF": ""})
    rows.append({"Beschrieb": "Nutzung", "Antwort/Wert": answer("Nutzung"), "VKF": ""})
    rows.append(
        {
            "Beschrieb": "Gebäudehöhe",
            "Antwort/Wert": height_result.rounded_height_m if height_result.height_m is not None else "n/a",
            "VKF": height_result.vkf_category,
        }
    )
    if area_result.building_area_m2 is not None:
        total_area_value = area_result.rounded_area_m2
    else:
        total_area_value = "n/a"
    vkf_comment = small_building_comment(area_result.building_area_m2)

    rows.append(
        {
            "Beschrieb": "Geschossfläche",
            "Antwort/Wert": total_area_value,
            "VKF": vkf_comment,
        }
    )

    if area_result.storeys:
        storeys = sorted(
            area_result.storeys,
            key=lambda s: (s.elevation is None, s.elevation if s.elevation is not None else 0.0),
        )
        for storey in storeys:
            label = storey.name or "Geschoss"
            if storey.elevation is not None:
                label += f" (z = {storey.elevation:.2f} m)"
            storey_vkf = storey_area_comment(storey.area_m2)
            rows.append(
                {
                    "Beschrieb": f"  - {label}",
                    "Antwort/Wert": round(storey.area_m2, 3),
                    "VKF": storey_vkf,
                }
            )
    rows.append({"Beschrieb": "Bauweise", "Antwort/Wert": answer("Bauweise"), "VKF": ""})
    rows.append({"Beschrieb": "Sicherheitsabstand", "Antwort/Wert": answer("Sicherheitsabstand"), "VKF": ""})

    rows.append({"Beschrieb": "Qualitätssicherung", "Antwort/Wert": "", "VKF": ""})
    rows.append({"Beschrieb": "QS-Stufe", "Antwort/Wert": answer("QS-Stufe"), "VKF": ""})
    rows.append({"Beschrieb": "Besonderes", "Antwort/Wert": answer("Besonderes"), "VKF": ""})

    rows.append({"Beschrieb": "Gebäudehülle", "Antwort/Wert": "", "VKF": ""})
    rows.append({"Beschrieb": "Tragwerk", "Antwort/Wert": answer("Tragwerk"), "VKF": ""})
    rows.append({"Beschrieb": "Tragwerk Treppenhaus", "Antwort/Wert": answer("Tragwerk Treppenhaus"), "VKF": ""})
    rows.append({"Beschrieb": "Geschossdecke", "Antwort/Wert": answer("Geschossdecke"), "VKF": ""})
    rows.append({"Beschrieb": "horz. Fluchtweg / Wände", "Antwort/Wert": answer("horz. Fluchtweg / Wände"), "VKF": ""})

    return rows


def write_result_to_excel(
    height_result: HeightResult,
    area_result: AreaResult,
    excel_path: str,
    extra_columns: Optional[dict[str, str]] = None,
) -> None:
    excel_path = Path(excel_path)
    rows = _build_rows(height_result, area_result, extra_columns)
    df = pd.DataFrame(rows, columns=["Beschrieb", "Antwort/Wert", "VKF"])
    excel_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(excel_path, index=False)
    _apply_header_formatting(excel_path, rows)


def _apply_header_formatting(excel_path: Path, rows: List[dict[str, str]]) -> None:
    """Setzt Überschriften fett (benötigt openpyxl)."""
    try:
        from openpyxl import load_workbook
        from openpyxl.styles import Font
    except ModuleNotFoundError:
        return

    header_rows = [
        idx
        for idx, row in enumerate(rows, start=2)
        if row["Beschrieb"] and not row["Antwort/Wert"] and not row["VKF"]
    ]
    if not header_rows:
        return

    wb = load_workbook(excel_path)
    ws = wb.active
    bold_font = Font(bold=True)
    for row_idx in header_rows:
        for col in ("A", "B", "C"):
            ws[f"{col}{row_idx}"].font = bold_font
    wb.save(excel_path)
