from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, List

# Kompatibilitäts-Import wie bei HeightService / ifc_loader
if __package__ in (None, ""):
    import os as _os, sys as _sys

    _sys.path.append(_os.path.dirname(_os.path.dirname(__file__)))
    from processors.ifc_loader import IfcLoader
else:
    from .ifc_loader import IfcLoader


@dataclass
class StoreyArea:
    """Eine Geschossfläche, berechnet aus den Raumflächen (IfcSpace)."""
    name: str
    elevation: Optional[float]
    area_m2: float


@dataclass
class AreaResult:
    """
    Ergebniscontainer für die Gebäudefläche nach VKF.

    building_area_m2 = Summe aller Geschossflächen (aus Räumen)
    storeys          = Liste der einzelnen Geschossflächen
    """
    ifc_path: str
    building_area_m2: Optional[float]
    storeys: List[StoreyArea]

    @property
    def rounded_area_m2(self) -> Optional[float]:
        if self.building_area_m2 is None:
            return None
        return round(self.building_area_m2, 3)

    def text_lines(self) -> list[str]:
        lines: list[str] = [f"IFC-Datei: {self.ifc_path}"]

        if self.building_area_m2 is None or not self.storeys:
            lines.append(
                "Gebäudefläche nach VKF konnte nicht automatisch ermittelt werden "
                "(keine passenden Raumflächen gefunden)."
            )
            return lines

        lines.append(
            f"Gebäudefläche nach VKF (Summe Geschossflächen aus Räumen): "
            f"{self.building_area_m2:.1f} m²"
        )
        lines.append("")
        lines.append("Geschossflächen (aus IfcSpace-Quantities):")

        # nach Höhe sortieren (falls Höhe vorhanden)
        for s in sorted(
            self.storeys,
            key=lambda st: (st.elevation is None, st.elevation if st.elevation is not None else 0.0),
        ):
            label = s.name or "<ohne Name>"
            if s.elevation is not None:
                label += f" (z = {s.elevation:.2f} m)"
            lines.append(f"  - {label}: {s.area_m2:.1f} m²")

        return lines


class BuildingAreaCalculator:
    """
    Ermittelt Geschossflächen und Gebäudefläche aus allen Räumen (IfcSpace).

    Strategie:
    - Räume je Geschoss über IfcRelContainedInSpatialStructure finden.
    - Für jeden Raum eine IfcQuantityArea (Net/Gross) aus den Mengen lesen.
    - Pro Geschoss aufsummieren; Summe aller Geschosse = Gebäudefläche nach VKF.
    """

    def __init__(self, ifc_file):
        self.ifc = ifc_file

    # ------------------------------------------------------------
    # Hilfsfunktionen
    # ------------------------------------------------------------

    def _space_area_m2(self, space) -> Optional[float]:
        """
        Liest die Raumfläche aus IfcElementQuantity (IfcQuantityArea).

        Es werden typische Namen aus BIM-Tools erkannt:
        NETFLOORAREA, GROSSFLOORAREA, NETAREA, GROSSAREA, AREA (mit/ohne _ / Leerzeichen).
        """
        for rel in getattr(space, "IsDefinedBy", []) or []:
            if not rel.is_a("IfcRelDefinesByProperties"):
                continue

            prop_def = getattr(rel, "RelatingPropertyDefinition", None)
            if prop_def is None:
                continue
            if not prop_def.is_a("IfcElementQuantity"):
                continue

            for q in prop_def.Quantities or []:
                if not q.is_a("IfcQuantityArea"):
                    continue

                q_name = (q.Name or "").upper().replace(" ", "").replace("_", "")
                if q_name in {
                    "NETFLOORAREA",
                    "GROSSFLOORAREA",
                    "NETAREA",
                    "GROSSAREA",
                    "AREA",
                }:
                    if q.AreaValue is not None:
                        return float(q.AreaValue)

        # Kein passender Quantity-Eintrag gefunden
        return None

    def _spaces_by_storey(self) -> dict:
        """
        Ordnet jedem IfcBuildingStorey die enthaltenen IfcSpace-Objekte zu.

        Viele Modelle hängen Räume nicht über ContainsElements an, sondern
        über IfcRelAggregates / Decomposes. Wir berücksichtigen beide Varianten.
        """
        mapping = {s: [] for s in self.ifc.by_type("IfcBuildingStorey") or []}

        for space in self.ifc.by_type("IfcSpace") or []:
            storey = None

            # 1) Üblicher Weg: Space.Decomposes -> IfcRelAggregates
            for rel in getattr(space, "Decomposes", []) or []:
                parent = getattr(rel, "RelatingObject", None)
                if parent and parent.is_a("IfcBuildingStorey"):
                    storey = parent
                    break

            # 2) Fallback: ContainedInStructure (manchmal für Räume verwendet)
            if storey is None:
                for rel in getattr(space, "ContainedInStructure", []) or []:
                    if not rel.is_a("IfcRelContainedInSpatialStructure"):
                        continue
                    parent = getattr(rel, "RelatingStructure", None)
                    if parent and parent.is_a("IfcBuildingStorey"):
                        storey = parent
                        break

            if storey is None:
                continue

            mapping.setdefault(storey, []).append(space)

        return mapping

    # ------------------------------------------------------------
    # Hauptlogik
    # ------------------------------------------------------------

    def compute_storey_areas(self) -> List[StoreyArea]:
        """Berechnet die Geschossflächen aus den Raumflächen."""
        storeys_spaces = self._spaces_by_storey()
        storey_results: List[StoreyArea] = []

        for storey, spaces in storeys_spaces.items():
            storey_area = 0.0

            for space in spaces:
                area = self._space_area_m2(space)
                if area is None:
                    continue
                storey_area += area

            if storey_area > 0.0:
                name = (
                    getattr(storey, "LongName", None)
                    or getattr(storey, "Name", None)
                    or ""
                )
                elevation = getattr(storey, "Elevation", None)

                storey_results.append(
                    StoreyArea(
                        name=name,
                        elevation=elevation,
                        area_m2=storey_area,
                    )
                )

        return storey_results

    def compute_building_area_m2(self) -> Optional[float]:
        """
        Alte API, falls du sie irgendwo verwendest:
        gibt nur die Gesamtfläche zurück.
        """
        storeys = self.compute_storey_areas()
        if not storeys:
            return None
        return sum(s.area_m2 for s in storeys)


class AreaService:
    """Service-Klasse analog zu HeightService, aber für die Gebäudefläche."""

    def compute_from_path(self, ifc_path: str) -> AreaResult:
        loader = IfcLoader()
        ifc = loader.load(ifc_path)

        calc = BuildingAreaCalculator(ifc)
        storeys = calc.compute_storey_areas()
        building_area_m2 = (
            sum(s.area_m2 for s in storeys) if storeys else None
        )

        return AreaResult(
            ifc_path=ifc_path,
            building_area_m2=building_area_m2,
            storeys=storeys,
        )
