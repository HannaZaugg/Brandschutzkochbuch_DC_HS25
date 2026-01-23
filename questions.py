"""Fragenkatalog für zusätzliche Nutzereingaben."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, Optional


@dataclass(frozen=True)
class Question:
    key: str
    prompt: str
    excel_header: str
    category: str
    default: str = "nicht bestimmt"
    options: Optional[tuple[str, ...]] = None
    widget: str = "text"  # "text", "radio", "select"


DEFAULT_QUESTIONS: tuple[Question, ...] = (
    
    #Qualitätssicherung
    Question(
        key="qs_level",
        prompt="Welche QS-Stufe liegt vor?",
        excel_header="QS-Stufe",
        category="Qualitätssicherung",
        default="nicht bestimmt",
        widget="select",
        options=("nicht bestimmt", "QSS1", "QSS2", "QSS3"),
    ),
    Question(
        key="special_notes",
        prompt="Gibt es Besonderes zu beachten?",
        excel_header="Besonderes",
        category="Qualitätssicherung",
        default="nicht bestimmt",
    ),
    
    #Gebäudehülle
    Question(
        key="fassade_classificated",
        prompt="Was gilt bei der Aussenwand für ein Klassifiziertes System?",
        excel_header="Klassifiziertes System",
        category="Gebäudehülle",
        options=("nicht bestimmt", "RF1", "RF2-cr", "RF3-cr" ),
        default="nicht bestimmt",
        widget="select",
    ),
    Question(
        key="fassade_cover",
        prompt="Was gilt für die Aussenwandbekleidung?",
        excel_header="Aussenwandbekleidung",
        category="Gebäudehülle",
        options=("nicht bestimmt", "RF1", "RF2-cr", "RF3-cr" ),
        default="nicht bestimmt",
        widget="select",
    ),
    Question(
        key="fassade_isolation",
        prompt="Was gilt für die Wärmedämmschicht und die Zwischenschicht?",
        excel_header="Wärmedämmschicht / Zwischenschicht",
        category="Gebäudehülle",
        options=("nicht bestimmt", "RF1", "RF2-cr"),
        default="nicht bestimmt",
        widget="select",
    ),
    Question(
        key="fassade_light_bands",
        prompt="Was gild für Lichtbänder?",
        excel_header="Lichtbänder",
        category="Gebäudehülle",
        options=("nicht bestimmt", "RF1", "RF2", "RF3"),
        default="nicht bestimmt",
        widget="select",
    ),
    Question(
        key="roof_main",
        prompt="Wie ist der Aufbau vom Dach vorgesehen?",
        excel_header="Dach",
        category="Gebäudehülle",
        options=("nicht bestimmt", "Schichtaufbau Variante 1", "Schichtaufbau Variante 2", "Schichtaufbau Variante 3", "Schichtaufbau Variante 4", "Schichtaufbau Variante 5", "Schichtaufbau Variante 6", "Schichtaufbau Variante 7", "Schichtaufbau Variante 8", "Schichtaufbau Variante 9", "Eingeschossige Zeltbauten / Traglufthallen / Treibhäuser", "Nebenbauten"),
        default="nicht bestimmt",
        widget="select",
    ),
        
    #Tragwerke und Brandabschnitte
    Question(
        key="concept_type",
        prompt="Welche Art Konzept liegt vor?",
        excel_header="Tragwerk",
        category="Tragwerke und Brandabschnitte",
        options=("nicht bestimmt", "Bauliches Konzept", "Löschanlage Konzept"),
        default="nicht bestimmt",
        widget="select",
    ),
    Question(
        key="requirement_structure_basement",
        prompt="Welche Anforderungen an das Tragwerk gelten im Untergeschoss?",
        excel_header="Tragwerk UG",
        category="Tragwerke und Brandabschnitte",
        options=("R60", "R30", "R90", "RO"),
        default="nicht bestimmt",
        widget="select",
    ),
    Question(
        key="requirement_structure_eg_og",
        prompt="Welche Anforderungen an das Tragwerk gelten in Erdgeschoss und den Obergeschossen?",
        excel_header="Tragwerk EG & OG",
        category="Tragwerke und Brandabschnitte",
        default="nicht bestimmt",
        widget="select",
        options=("nicht bestimmt", "R30", "R60", "R90", "R0"),
    ),
    Question(
        key="requirement_structure_attic",
        prompt="Welche Anforderungen an das Tragwerk gelten im obersten Geschoss?",
        excel_header="Tragwerk DG",
        category="Tragwerke und Brandabschnitte",
        default="nicht bestimmt",
        widget="select",
        options=("R0", "R30", "R60", "R90"),
    ),
    Question(
        key="requirement_floors",
        prompt="Welche Anforderungen gelten für Brandabschnittsbildende Geschossdecken?",
        excel_header="Geschossdecken",
        category="Tragwerke und Brandabschnitte",
        default="nicht bestimmt",
        widget="select",
        options=("nicht bestimmt", "REI30", "REI60", "REI90", "REI120"),
    ), 
    Question(
        key="requirement_escape_routes",
        prompt="Welche Anforderungen gelten für Brandabschnitte bei Brandabschnittsbildenden Wänden und horizontalen Fluchtwegen?",
        excel_header="Horizontale Fluchtwege",
        category="Tragwerke und Brandabschnitte",
        default="nicht bestimmt",
        widget="select",
        options=("nicht bestimmt", "EI30", "EI60", "EI90"),
    ), 
    Question(
        key="requirement_stairs",
        prompt="Welche Anforderungen gelten für Brandabschnitte bei vertikalen Fluchtwegen?",
        excel_header="Treppenhaus",
        category="Tragwerke und Brandabschnitte",
        default="nicht bestimmt",
        widget="select",
        options=("nicht bestimmt", "REI30", "REI60", "REI90", "REI120"),
    ),      

             
    #Flucht-& Rettungswege
    Question(
        key="compliance_vertical_routes",
        prompt="Ist die Vorgegebene Anzahl an vertikalen Fluchtwegen vorhanden?",
        excel_header="Vertikale Fluchtwege",
        category="Flucht- & Rettungswege",
        default="Erfüllt",
        widget="select",
        options=("Erfüllt", "Nicht erfüllt"),
    ),
    Question(
        key="compliance_exit_free",
        prompt="Führen die vertikalen Fluchtwege ins Freie?",
        excel_header="Ausgang ins Freie",
        category="Flucht- & Rettungswege",
        default="Erfüllt",
        widget="select",
        options=("Erfüllt", "Nicht erfüllt"),
    ),
    Question(
        key="compliance_width",
        prompt="Sind die Mindestbreiten von 1.20 im FLuchtweg eingehalten?",
        excel_header="Abmessungen min. 1.20m",
        category="Flucht- & Rettungswege",
        default="Erfüllt",
        widget="select",
        options=("Erfüllt", "Nicht erfüllt"),
    ),
    Question(
        key="occupancy_over_300",
        prompt="Gibt es einen Raum welcher eine Personenbelegung von über 300 Personen hat?",
        excel_header="Personenbelegung",
        category="Flucht- & Rettungswege",
        default="nein",
        widget="select",
        options=("Nein", "Ja"),
    ),
    Question(
        key="compliance_doors",
        prompt="Ist die Anzahl Türen und deren Breiten eingehalten?",
        excel_header="Anzahl Ausgänge / Türbreiten",
        category="Flucht- & Rettungswege",
        default="Erfüllt",
        widget="select",
        options=("Erfüllt", "Nicht erfüllt"),
    ),
    Question(
        key="compliance_room_sequence",
        prompt="Führen die FLuchtwege maximal durch einen angrenzenden Raum?",
        excel_header="Raumabfolge",
        category="Flucht- & Rettungswege",
        default="Erfüllt",
        widget="select",
        options=("Erfüllt", "Nicht erfüllt"),
    ),

    
    #Notbeleuchtung
    
    #Löscheinrichtung
    
    #Sprinkleranlage
    
    #Brandmeldeanlage
    
)


def ask_questions(
    questions: Iterable[Question] = DEFAULT_QUESTIONS,
    input_func: Callable[[str], str] = input,
) -> dict[str, str]:
    """Fragt alle Fragen nacheinander ab und liefert Antworten nach key."""
    answers: dict[str, str] = {}
    for question in questions:
        raw = input_func(f"{question.prompt.strip()} ").strip()
        answers[question.key] = raw or question.default
    return answers


def answers_for_excel(
    answers: dict[str, str],
    questions: Iterable[Question] = DEFAULT_QUESTIONS,
) -> dict[str, str]:
    """Mappt gespeicherte Antworten auf Excel-Spaltennamen."""
    excel_values: dict[str, str] = {}
    for question in questions:
        excel_values[question.excel_header] = answers.get(question.key, question.default)
    return excel_values
