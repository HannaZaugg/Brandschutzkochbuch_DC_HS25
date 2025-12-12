
"""
processors/ifc_loader.py
OOP-Variante: IfcLoader mit .load() und .summarize()
Modulstart:
    python3 processors/ifc_loader.py "/Users/hannazaugg/Library/Mobile Documents/com~apple~CloudDocs/HSLU/HS25/DT_Programming/Brandschutzkochbuch/Modelle/ARC_Modell_NEST_230328.ifc"
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

@dataclass
class IfcSummary:
    path: str
    schema: Optional[str]
    n_products: int
    n_storeys: int

class IfcLoader:
    def __init__(self):
        try:
            import ifcopenshell  # type: ignore
        except Exception as e:
            raise ImportError(
                "ifcopenshell nicht installiert. (pip install ifcopenshell)"
            ) from e
        self.ifcopenshell = ifcopenshell

    def load(self, path: str):
        import os
        if not os.path.exists(path):
            raise FileNotFoundError(f"IFC-Datei nicht gefunden: {path}")
        return self.ifcopenshell.open(path)

    @staticmethod
    def _schema(ifc_file) -> Optional[str]:
        # Mal ist schema eine Methode, mal ein String:
        attr = getattr(ifc_file, "schema", None)
        return attr() if callable(attr) else attr

    def summarize(self, ifc_file) -> IfcSummary:
        schema = self._schema(ifc_file)
        products = ifc_file.by_type("IfcProduct")
        storeys = ifc_file.by_type("IfcBuildingStorey")
        return IfcSummary(
            path=getattr(ifc_file, "filepath", ""),
            schema=schema,
            n_products=len(products),
            n_storeys=len(storeys),
        )


def load_ifc(path: str):
    """Convenience-Funktion für Module, die nur ein IFC laden wollen."""
    return IfcLoader().load(path)

# ----- CLI bei Modulstart -----
def _main():
    import sys
    if len(sys.argv) < 2:
        print("Nutzung:\n  python -m processors.ifc_loader \"/Pfad/zum/Modell.ifc\"")
        raise SystemExit(2)
    path = sys.argv[1]
    loader = IfcLoader()
    ifc = loader.load(path)
    s = loader.summarize(ifc)
    print(f"[OK] Schema={s.schema}  Produkte={s.n_products}  Geschosse={s.n_storeys}")

if __name__ == "__main__":
    _main()
