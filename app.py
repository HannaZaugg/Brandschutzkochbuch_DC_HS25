import os
import tempfile
from datetime import datetime

import streamlit as st

from questions import DEFAULT_QUESTIONS
from processors.area import AreaService
from processors.height import HeightService

# run with: streamlit run app.py

# Grundlayout und Metadaten der Seite setzen (Titel/Icon/Layout)
st.set_page_config(page_title="Brandschutz • IFC Checker", page_icon="🧯", layout="wide")

# Sitzungsvorgaben setzen, damit nichts fehlt wenn Nutzer neu lädt
st.session_state.setdefault("project_info", {"number": "", "name": "", "has_ifc": True})
st.session_state.setdefault("project_started", False)
st.session_state.setdefault("dashboard_ready", False)
st.session_state.setdefault("question_answers", {q.key: q.default for q in DEFAULT_QUESTIONS})
st.session_state.setdefault("manual_inputs", {"height_m": None, "building_area_m2": None})
st.session_state.setdefault("ifc_result", {"height": None, "area": None, "error": None})
st.session_state.setdefault("active_tab", "Projektstart")  # erinnert an zuletzt genutzten Tab
st.session_state.setdefault("has_ifc_choice", "Ja")

# Titel-Header der App für sofortige Orientierung
st.title("🧯 Brandschutzkochbuch")
st.markdown("Starte ein Projekt, lade (optional) ein IFC hoch und beantworte die Fragen. Wechsel jederzeit zwischen Tabs.")
summary_container = st.container()  # Platzhalter für die Übersicht oberhalb der Tabs

# Seitenleiste: Projektinfos und Sitzungsstart
with st.sidebar:
    # Aktiven Zeitstempel anzeigen, damit klar ist wann gestartet wurde
    st.caption(f"Aktive Sitzung gestartet: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    # Kurzer Überblick zum Status anzeigen
    st.write("**Status**")
    st.write(
        f"Projekt: {st.session_state['project_info'].get('number') or '-'} "
        f"{st.session_state['project_info'].get('name') or ''}"
    )
    st.write(
        "IFC geladen: "
        f"{'ja' if st.session_state['ifc_result'].get('height') or st.session_state['ifc_result'].get('area') else 'nein'}"
    )

# Hilfsfunktion: IFC-Upload speichern, analysieren und Ergebnis zurückgeben
def analyze_ifc(uploaded_file):
    """Nimmt den Upload entgegen, schreibt ihn temporär und wertet Höhe/Fläche aus."""
    temp_path = None
    try:
        # Upload-Inhalt in eine temporäre Datei schreiben, damit ifcopenshell sie lesen kann
        with tempfile.NamedTemporaryFile(delete=False, suffix=".ifc") as tmp:
            tmp.write(uploaded_file.getbuffer())
            temp_path = tmp.name

        # Auswertungen durchführen: Höhe und Flächen
        height_result = HeightService().compute_from_path(temp_path, extra_answers=st.session_state.get("question_answers"))
        area_result = AreaService().compute_from_path(temp_path)
        return {"height": height_result, "area": area_result, "error": None}
    except ImportError as exc:
        missing = getattr(exc, "name", None) or "ifcopenshell"
        return {"height": None, "area": None, "error": f"Fehlendes Paket: {missing} (pip install ifcopenshell)"}
    except FileNotFoundError as exc:
        return {"height": None, "area": None, "error": str(exc)}
    except Exception as exc:
        return {"height": None, "area": None, "error": f"Unerwarteter Fehler: {exc}"}
    finally:
        # Temporäre Datei aufräumen, damit keine Reste liegen bleiben
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except OSError:
                pass

# Hilfsfunktion: fasst die wichtigsten Kennzahlen für die Übersicht zusammen
def summary_values():
    """Lieferte Höhe, VKF-Kategorie, Fläche und Geschossliste aus IFC oder manuellen Werten."""
    pi = st.session_state["project_info"]
    ifc_res = st.session_state["ifc_result"]

    height_val = None
    vkf_cat = None
    area_val = None
    storeys = []
    if ifc_res and ifc_res.get("height"):
        height_val = ifc_res["height"].rounded_height_m
        vkf_cat = ifc_res["height"].vkf_category
    if ifc_res and ifc_res.get("area"):
        area_val = ifc_res["area"].rounded_area_m2
        storeys = ifc_res["area"].storeys

    # Falls keine IFC-Werte, auf manuelle zurückgreifen
    if height_val is None:
        height_val = st.session_state["manual_inputs"].get("height_m")
    if area_val is None:
        area_val = st.session_state["manual_inputs"].get("building_area_m2")

    # VKF-Kategorie aus manueller Höhe ableiten, falls keine IFC-Kategorie vorliegt
    if vkf_cat is None and height_val is not None:
        try:
            from processors.vkf_rules import height_category
            vkf_cat = height_category(height_val)
        except Exception:
            vkf_cat = None

    return {
        "project_info": pi,
        "height_val": height_val,
        "vkf_cat": vkf_cat,
        "area_val": area_val,
        "storeys": storeys,
    }

# Tabs anlegen: Projektstart, Fragen, Dashboard (klassische Streamlit-Tabs)
tab_start, tab_questions, tab_dashboard = st.tabs(["Objektinformationen", "Fragen", "Dashboard"])

# --- Tab: Projektstart ---
with tab_start:
    st.header("Neues Projekt starten")
    st.markdown(
        "Bitte Projektnummer und Projektname angeben. "
        "Falls ein IFC verfügbar ist, kannst du es direkt hier hochladen."
    )

    project_number = st.text_input("Projektnummer (Pflicht)", value=st.session_state["project_info"].get("number", ""))
    project_name = st.text_input("Projektname", value=st.session_state["project_info"].get("name", ""))
    usage_value = st.text_input(
        "Nutzung",
        value=st.session_state["question_answers"].get("usage", "-"),
    )
    construction_value = st.selectbox(
        "Bauweise",
        options=["Beton", "Holz", "Stahl", "Weitere", "Unbekannt"],
        index=0,
        key="construction_select",
    )
    has_ifc_choice = st.radio(
        "Ist ein IFC vorhanden?",
        options=["Ja", "Nein"],
        index=0 if st.session_state["has_ifc_choice"] == "Ja" else 1,
        key="has_ifc_choice",
    )
    uploaded_ifc = st.file_uploader("IFC-Datei hochladen (falls vorhanden)", type=["ifc"], key="ifc_upload_start")

    # Wenn kein IFC vorhanden ist, direkt hier Höhe und Fläche abfragen
    manual_height_start = None
    manual_area_start = None
    if has_ifc_choice == "Nein":
        manual_height_start = st.number_input(
            "Gebäudehöhe [m] (kein IFC vorhanden)",
            value=st.session_state["manual_inputs"].get("height_m") or 0.0,
            min_value=0.0,
            step=0.1,
            key="manual_height_start",
        )
        manual_area_start = st.number_input(
            "Gebäudefläche (Summe Geschosse) [m²] (kein IFC vorhanden)",
            value=st.session_state["manual_inputs"].get("building_area_m2") or 0.0,
            min_value=0.0,
            step=1.0,
            key="manual_area_start",
        )
    start_submitted = st.button("Projekt starten")

    if start_submitted:
        # Eingaben prüfen und in Session legen
        if not project_number.strip():
            st.error("Projektnummer darf nicht leer sein.")
        elif not project_name.strip():
            st.error("Projektname darf nicht leer sein.")
        elif has_ifc_choice == "Ja" and uploaded_ifc is None:
            st.error("Bitte IFC-Datei hochladen oder 'Nein' wählen.")
        else:
            st.session_state["project_info"] = {
                "number": project_number,
                "name": project_name.strip(),
                "has_ifc": has_ifc_choice == "Ja",
            }
            # Nutzung und Bauweise direkt speichern
            st.session_state["question_answers"]["usage"] = usage_value.strip() or "-"
            st.session_state["question_answers"]["construction_type"] = construction_value or "-"
            st.session_state["project_started"] = True
            st.session_state["dashboard_ready"] = True  # Dashboard sofort freischalten

            if has_ifc_choice == "Ja" and uploaded_ifc:
                with st.spinner("IFC wird ausgewertet..."):
                    st.session_state["ifc_result"] = analyze_ifc(uploaded_ifc)
                if st.session_state["ifc_result"]["error"]:
                    st.error(st.session_state["ifc_result"]["error"])
                else:
                    st.success("IFC erfolgreich ausgewertet.")
                    # IFC-Werte als Defaults für manuelle Eingaben setzen
                    height_val = st.session_state["ifc_result"]["height"].height_m if st.session_state["ifc_result"]["height"] else None
                    area_val = st.session_state["ifc_result"]["area"].building_area_m2 if st.session_state["ifc_result"]["area"] else None
                st.session_state["manual_inputs"] = {"height_m": height_val, "building_area_m2": area_val}
            else:
                # Kein IFC: manuelle Felder befüllen
                st.session_state["ifc_result"] = {"height": None, "area": None, "error": None}
                st.session_state["manual_inputs"] = {
                    "height_m": manual_height_start,
                    "building_area_m2": manual_area_start,
                }
            st.success("Projekt gestartet.")

# --- Tab: Fragen und ggf. manuelle Werte ---
with tab_questions:
    if not st.session_state.get("project_started"):
        st.warning("Bitte zuerst im Tab 'Projektstart' starten.")
    else:
        st.header("Projektfragen beantworten")
        st.markdown("Beantworte alle Fragen. Ohne IFC bitte Höhe und Geschossfläche manuell angeben.")

        with st.form("questions_form"):
            # Fragen nach Kategorie gruppieren und gruppiert anzeigen
            grouped: dict[str, list] = {}
            for q in DEFAULT_QUESTIONS:
                grouped.setdefault(q.category, []).append(q)
            for category, questions in grouped.items():
                st.subheader(category)
                for question in questions:
                    current_val = st.session_state["question_answers"].get(question.key, question.default)
                    if question.options:
                        # Auswahl aus vorgegebenen Optionen (Radio)
                        default_index = (
                            question.options.index(current_val)
                            if current_val in (question.options or [])
                            else 0
                        )
                        st.radio(
                            question.prompt,
                            options=question.options,
                            index=default_index,
                            key=f"question_{question.key}",
                        )
                    else:
                        st.text_input(
                            question.prompt,
                            value=current_val,
                            key=f"question_{question.key}",
                        )
            submitted = st.form_submit_button("Antworten speichern")

        # Speicherung der neuen Antworten nach Klick auf den Button
        if submitted:
            st.session_state["question_answers"] = {
                q.key: st.session_state.get(f"question_{q.key}") or q.default
                for q in DEFAULT_QUESTIONS
            }
            # Nach dem Speichern gilt der Stand als bestätigt
            st.session_state["dashboard_ready"] = True
            st.success("Antworten gespeichert. Dashboard ist freigegeben.")

        # Zwischenstand anzeigen
        st.subheader("Aktuelle Antworten")
        st.table(
            {
                "Frage": [q.prompt for q in DEFAULT_QUESTIONS],
                "Antwort": [st.session_state["question_answers"].get(q.key, q.default) for q in DEFAULT_QUESTIONS],
            }
        )

# --- Tab: Übersicht/Dashboard ---
with tab_dashboard:
    if not st.session_state.get("project_started"):
        st.info("Bitte zuerst im Tab 'Projektstart' starten.")
    else:
        # Hinweis falls Fragen noch nicht bestätigt sind
        if not st.session_state.get("dashboard_ready"):
            st.warning("Fragen noch nicht bestätigt. Werte können unvollständig sein.")

        summary = summary_values()
        storeys = summary["storeys"]

        # Antworten nach Kategorien als Karten anzeigen (Objektinfos werden oben angezeigt)
        grouped_answers: dict[str, list[tuple[str, str, str]]] = {}
        for q in DEFAULT_QUESTIONS:
            grouped_answers.setdefault(q.category, []).append(
                (q.excel_header, q.prompt, st.session_state["question_answers"].get(q.key, q.default))
            )

        categories = [c for c in grouped_answers.keys() if c.lower() != "projekt"]
        cols = st.columns(2)
        # Farbige Kacheln
        palette = ["#eef2ff", "#e8fff3", "#fff4e6", "#f0f9ff", "#fdf2f8", "#f3f4f6"]
        for idx, cat in enumerate(categories):
            bg = palette[idx % len(palette)]
            with cols[idx % 2]:
                st.markdown(
                    f"""
                    <div style="background:{bg}; padding:12px 14px; border-radius:8px; border:1px solid #d9d9d9; margin-bottom:12px;">
                        <div style="font-weight:700; font-size:16px; margin-bottom:8px;">{cat}</div>
                        <div style="display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:6px 12px;">
                            {"".join(f"<div><strong>{excel}</strong>: {answer or '-'}</div>" for excel, _prompt, answer in grouped_answers[cat])}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

# Oberer Bereich: Kernübersicht direkt unter dem Untertitel, immer sichtbar (wenn Projekt gestartet)
with summary_container:
    st.markdown("---")
    st.header("Objektinformationen")
    if not st.session_state.get("project_started"):
        st.info("Starte zuerst ein Projekt, um die Übersicht zu füllen.")
    else:
        summary = summary_values()
        pi = summary["project_info"]
        height_val = summary["height_val"]
        vkf_cat = summary["vkf_cat"]
        area_val = summary["area_val"]
        usage_val = st.session_state["question_answers"].get("usage", "-")
        construction_val = st.session_state["question_answers"].get("construction_type", "-")

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Projektnummer", pi.get("number") or "n/a")
            st.metric("Projektname", pi.get("name") or "n/a")
            st.metric("Gebäudehöhe [m]", f"{height_val}" if height_val is not None else "n/a")
        with col2:
            st.metric("Nutzung", usage_val or "-")
            st.metric("Bauweise", construction_val or "-")
            st.metric("VKF-Kategorie (aus Höhe)", vkf_cat or "n/a")
            # Gesamtfläche wird hier nicht mehr gezeigt; stattdessen die Geschossflächen unten

        # Geschossflächen je Geschoss anzeigen, falls vorhanden
        storeys = summary.get("storeys") or []
        if storeys:
            st.markdown("**Geschossflächen (je Geschoss)**")
            st.table(
                {
                    "Geschoss": [s.name or "<ohne Name>" for s in storeys],
                    "Fläche [m²]": [round(s.area_m2, 3) for s in storeys],
                }
            )
