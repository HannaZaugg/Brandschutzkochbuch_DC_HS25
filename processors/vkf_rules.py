from __future__ import annotations

from typing import Optional

SMALL_BUILDING_LIMIT_M2 = 600.0
STOREY_AREA_LIMIT_M2 = 1000.0


def height_category(height_m: Optional[float]) -> str:
    """Gibt die VKF-Kategorie anhand der Gebäudehöhe zurück."""
    if height_m is None:
        return "n/a"
    if height_m <= 11:
        return "Gebäude geringer Höhe"
    if height_m <= 30:
        return "Gebäude mittlerer Höhe"
    return "Hochhaus"


def small_building_comment(
    total_area_m2: Optional[float],
    *,
    limit_m2: float = SMALL_BUILDING_LIMIT_M2,
) -> str:
    """Bewertet, ob die Gesamtfläche einem Gebäude geringer Abmessung entspricht."""
    if total_area_m2 is None:
        return ""
    if total_area_m2 <= limit_m2:
        return "Gebäude geringer Abmessung"
    return "Kein Gebäude geringer Abmessung"


def storey_area_comment(
    storey_area_m2: float,
    *,
    limit_m2: float = STOREY_AREA_LIMIT_M2,
) -> str:
    """Kommentar für Geschosse, die eine maximale Brandabschnittsfläche überschreiten."""
    if storey_area_m2 > limit_m2:
        return "Brandabschnittsunterteilung erforderlich"
    return ""
