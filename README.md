
# IFC Height • Schritt 1 (nur CLI)

Ziel: **So simpel wie möglich** ein IFC laden und die Gebäudehöhe berechnen.

## Installation
```bash
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows PowerShell
# .venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

## Nutzung
```bash
# 1) Loader-Selbsttest (ohne Datei nur Importcheck)
python processors/ifc_loader.py

# 2) Loader mit Datei (Schema & Grundzahlen)
python processors/ifc_loader.py "/Pfad/zu/deinem/Modell.ifc"

# 3) Höhenberechnung (minimal)
python processors/height.py "/Pfad/zu/deinem/Modell.ifc"

# 4) Einfache Gesamtausführung
python run_height.py "/Pfad/zu/deinem/Modell.ifc"
```

> Achtung Pfade mit Leerzeichen **immer in Anführungszeichen** setzen.

## Nächste Schritte (geplant)
- Robustere Höhenlogik (Bounding Box / ifcopenshell.geom-Fallback)
- VKF-Höhenkategorien ableiten
- Einfache CSV-/Excel-Ausgabe
- Später: Streamlit-UI
