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
    default: str = "-"
    options: Optional[tuple[str, ...]] = None


DEFAULT_QUESTIONS: tuple[Question, ...] = (
    
    #Qualitätssicherung
    Question(
        key="qs_level",
        prompt="Welche QS-Stufe liegt vor?",
        excel_header="QS-Stufe",
        category="Qualitätssicherung",
    ),
    Question(
        key="special_notes",
        prompt="Gibt es Besonderes zu beachten?",
        excel_header="Besonderes",
        category="Qualitätssicherung",
    ),
    
    #Gebäudehülle
    Question(
        key="fassade_main",
        prompt="Wie ist die Fassade aufgebaut?",
        excel_header="Fassade",
        category="Gebäudehülle",
    ),
        Question(
        key="roof_main",
        prompt="Wie ist das Dach aufgebaut?",
        excel_header="Dach",
        category="Gebäudehülle",
    ),
        
    #Tragwerke und Brandabschnitte
        Question(
        key="concept_type",
        prompt="Welche Art Konzept liegt vor?",
        excel_header="Tragwerk",
        category="Tragwerke und Brandabschnitte",
        options=("Bauliches Konzept", "Löschanlage Konzept"),
    ),
        Question(
        key="requirement_structure_basement",
        prompt="Welche Anforderungen an das Tragwerk gelten im Untergeschoss?",
        excel_header="Tragwerk UG",
        category="Tragwerke und Brandabschnitte",
    ),
        Question(
        key="requirement_structure_eg_og",
        prompt="Welche Anforderungen an das Tragwerk gelten in Erdgeschoss und den Obergeschossen?",
        excel_header="Tragwerk EG & OG",
        category="Tragwerke und Brandabschnitte",
    ),
            Question(
        key="requirement_structure_attic",
        prompt="Welche Anforderungen an das Tragwerk gelten im obersten Geschoss?",
        excel_header="Tragwerk DG",
        category="Tragwerke und Brandabschnitte",
    ),
        Question(
        key="requirement_structure",
        prompt="Welche Anforderungen gelten für Brandabschnitte beim Tragwerk?",
        excel_header="Tragwerk",
        category="Tragwerke und Brandabschnitte",
    ),
        Question(
        key="requirement_stairs",
        prompt="Welche Anforderungen gelten für Brandabschnitte beim Treppenhaus?",
        excel_header="Treppenhaus",
        category="Tragwerke und Brandabschnitte",
    ),     
        Question(
        key="requirement_floors",
        prompt="Welche Anforderungen gelten für Brandabschnitte bei Geschossdecken?",
        excel_header="Geschossdecken",
        category="Tragwerke und Brandabschnitte",
    ),  
        Question(
        key="requirement_escape_routes",
        prompt="Welche Anforderungen gelten für Brandabschnitte bei horizontalen Fluchtwegen?",
        excel_header="Horizontale Fluchtwege",
        category="Tragwerke und Brandabschnitte",
    ), 
             
    #Flucht-& Rettungswege
    
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
