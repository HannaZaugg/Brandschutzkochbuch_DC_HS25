"""
Run Height – zentrales Einstiegsskript

Nutzung (im Projekt-Root):
    # Interaktiv (Pfad wird abgefragt)
    python3 run_height.py

    # Direkt mit Pfad
    python3 run_height.py "/Pfad/zum/Modell.ifc"
    
    /Users/hannazaugg/Library/Mobile Documents/com~apple~CloudDocs/HSLU/HS25/DT_Programming/Brandschutzkochbuch/Modelle/ARC_Modell_NEST_230328.ifc
"""
from __future__ import annotations
import argparse

from processors.height import HeightService
from processors.area import AreaService
from questions import DEFAULT_QUESTIONS, answers_for_excel, ask_questions

def main() -> None:
    parser = argparse.ArgumentParser(description="Liest IFC, berechnet Gesamthöhe und VKF-Kategorie.")
    parser.add_argument("path", nargs="?", help="Pfad zur IFC-Datei")
    parser.add_argument(
        "--excel",
        nargs="?",
        const="Brandschutzkochbuch.xlsx",
        default="Brandschutzkochbuch.xlsx",
        help="Pfad zu einer Excel-Datei (Standard: Brandschutzkochbuch.xlsx im aktuellen Ordner)",
    )
    args = parser.parse_args()

    # Interaktiver Prompt, falls kein Pfad übergeben wurde
    if not args.path:
        try:
            args.path = input("Pfad zur IFC-Datei: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("Abgebrochen.")
            raise SystemExit(2)
    if not args.path:
        print("Kein Pfad angegeben.")
        raise SystemExit(2)

    survey_answers = ask_questions(DEFAULT_QUESTIONS)

    service = HeightService()
    height_result = service.compute_from_path(args.path, extra_answers=survey_answers)
    
    area_service = AreaService()
    area_result = area_service.compute_from_path(args.path)

    def print_text():
        for line in height_result.text_lines():
            print(line)
        for line in area_result.text_lines():
            print(line)

    print_text()

    excel_path = args.excel or "Brandschutzkochbuch.xlsx"
    try:
        from excel import write_result_to_excel
    except ModuleNotFoundError as exc:
        missing = exc.name or "pandas"
        print(
            f"Excel-Export benötigt das Paket '{missing}'. "
            "Bitte installiere es (z.B. `pip install pandas openpyxl`)."
        )
        raise SystemExit(1)

    write_result_to_excel(
        height_result,
        area_result,
        excel_path,
        extra_columns=answers_for_excel(survey_answers, DEFAULT_QUESTIONS),
    )
    print(f"Ergebnis in Excel geschrieben: {excel_path}")


if __name__ == "__main__":
    main()
