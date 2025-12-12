
# Brandschutzkochbuch (IFC + Streamlit)

Streamlit-App zum Erfassen von Projektinfos, Beantworten eines Fragenkatalogs und Auswerten von IFC-Dateien (Gebäudehöhe, Geschossflächen). Ohne IFC können Höhe/Fläche manuell erfasst werden. Ergebnisse erscheinen in einer Übersicht und in farbigen Kacheln nach Kategorien.

## Installation
```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Start (Streamlit)
```bash
streamlit run app.py
```
- Tab „Objektinformationen“: Projektnummer, Projektname, Nutzung, Bauweise eingeben; IFC hochladen oder Höhe/Fläche manuell erfassen.
- Tab „Fragen“: restlichen Fragenkatalog ausfüllen (Auswahlfelder bzw. Freitext).
- Dashboard: Übersicht (inkl. VKF-Kategorie aus Höhe) und Kacheln je Kategorie.

## CLI (optional)
```bash
# IFC laden, Höhe/Flächen berechnen, Fragen interaktiv abfragen und nach Excel schreiben
python run.py "/Pfad/zum/Modell.ifc"
```

## Hinweise
- IFC-Auswertung benötigt `ifcopenshell`. Für Excel-Export zusätzlich `pandas` und `openpyxl`.
- Pfade mit Leerzeichen immer in Anführungszeichen setzen.
