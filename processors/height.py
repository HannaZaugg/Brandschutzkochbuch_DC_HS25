"""
processors/height.py

Lädt ein IFC, berechnet die Gebäudehöhe und ordnet sie in die VKF-Kategorien ein.

"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

# Kompatibilitäts-Import: funktioniert als Modul (-m) und bei Direktaufruf
if __package__ in (None, ""):
    import os as _os, sys as _sys

    _sys.path.append(_os.path.dirname(_os.path.dirname(__file__)))
    from processors.ifc_loader import IfcLoader
    from processors.vkf_rules import height_category
else:
    from .ifc_loader import IfcLoader
    from .vkf_rules import height_category

@dataclass
class HeightResult:
    ifc_path: str
    height_m: Optional[float]
    vkf_category: str
    extra_answers: Optional[dict[str, str]] = None

    @property
    def rounded_height_m(self) -> Optional[float]:
        return None if self.height_m is None else round(self.height_m, 3)

    def text_lines(self) -> tuple[str, str]:
        if self.height_m is None:
            return ("Höhe [m]=n/a", "Gebäudekategorie (VKF, Höhe): n/a")
        return (
            f"Höhe [m]={self.rounded_height_m}",
            f"Gebäudekategorie (VKF, Höhe): {self.vkf_category}",
        )


class HeightCalculator:
    def __init__(self, ifc):
        self.ifc = ifc

    @staticmethod
    def _placement_chain_z(local_placement) -> float:
        """Summiert die Z-Verschiebung entlang der Placement-Kette."""

        def z_of(lp):
            try:
                return float(lp.RelativePlacement.Location.Coordinates[2])
            except Exception:
                try:
                    return float(lp.RelativePlacement.Location[2])
                except Exception:
                    return 0.0

        z = 0.0
        seen = set()
        lp = local_placement
        for _ in range(64):
            if lp is None:
                break
            key = getattr(lp, "id", None) or id(lp)
            if key in seen:
                break
            seen.add(key)
            z += z_of(lp)
            try:
                lp = lp.PlacementRelTo
            except Exception:
                lp = None
        return z

    @classmethod
    def _storey_abs_z(cls, storey) -> float:
        try:
            elev = storey.Elevation
            if elev is not None:
                return float(elev)
        except Exception:
            pass
        try:
            return cls._placement_chain_z(storey.ObjectPlacement)
        except Exception:
            return 0.0

    def compute_height_m(self) -> Optional[float]:
        try:
            storeys = self.ifc.by_type("IfcBuildingStorey") or []
            if not storeys:
                return None
            zs = [self._storey_abs_z(s) for s in storeys]
            if not zs:
                return None
            return float(max(zs) - min(zs))
        except Exception:
            return None


class HeightService:
    def __init__(self, loader: Optional[IfcLoader] = None):
        self.loader = loader or IfcLoader()

    def compute_from_path(self, path: str, extra_answers: Optional[dict[str, str]] = None) -> HeightResult:
        ifc = self.loader.load(path)
        height = HeightCalculator(ifc).compute_height_m()
        category = height_category(height)
        return HeightResult(
            ifc_path=path,
            height_m=height,
            vkf_category=category,
            extra_answers=extra_answers or None,
        )
