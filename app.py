import os
import tempfile
import io
import base64
from datetime import datetime

import streamlit as st

from questions import DEFAULT_QUESTIONS, answers_for_excel
from processors.area import AreaService
from processors.height import HeightService
from processors.vkf_rules import vertical_escape_routes

# run with: streamlit run app.py

# Grundlayout und Metadaten der Seite setzen (Titel/Icon/Layout)
st.set_page_config(page_title="Brandschutz • IFC Checker", page_icon="🧯", layout="wide")

# Sitzungsvorgaben setzen, damit nichts fehlt wenn Nutzer neu lädt
st.session_state.setdefault("project_info", {"number": "", "name": "", "has_ifc": True})
st.session_state.setdefault("project_started", False)
st.session_state.setdefault("dashboard_ready", False)
st.session_state.setdefault("question_answers", {q.key: q.default for q in DEFAULT_QUESTIONS})
st.session_state.setdefault("manual_inputs", {"height_m": None, "building_area_m2": None})
st.session_state.setdefault("manual_storeys", [])
st.session_state.setdefault("ifc_result", {"height": None, "area": None, "error": None})
st.session_state.setdefault("active_tab", "Projektstart")  # erinnert an zuletzt genutzten Tab
st.session_state.setdefault("has_ifc_choice", "Ja")

# Logo laden und als data URI einbetten (fallback: ohne Bild)
logo_path = "/Users/hannazaugg/Library/Mobile Documents/com~apple~CloudDocs/HSLU/HS25/DT_Programming/Brandschutzkochbuch/Code/Tabellen/Flammen.png"
logo_data_uri = None
try:
    with open(logo_path, "rb") as f:
        logo_b64 = base64.b64encode(f.read()).decode("utf-8")
        logo_data_uri = f"data:image/png;base64,{logo_b64}"
except FileNotFoundError:
    logo_data_uri = None

# Titel-Header der App für sofortige Orientierung + Hero-Background
bg_style = ""
if logo_data_uri:
    bg_style = f"background-image: url('{logo_data_uri}');"
st.markdown(
    f"""
    <div style="width:100%; height:180px; border-radius:10px; overflow:hidden; position:relative; margin-bottom:0; {bg_style} background-size:cover; background-position:center;">
        <div style="position:absolute; inset:0; background:linear-gradient(90deg, rgba(255,255,255,0.82) 45%, rgba(255,255,255,0.6) 100%); display:flex; align-items:center; padding:16px 20px;">
            <div>
                <h1 style="margin:0; padding:0; font-size:32px;">Brandschutzkochbuch</h1>
                <p style="margin:6px 0 0 0; color:#3a3a3a; font-size:16px;">Starte ein Projekt, lade (optional) ein IFC hoch und beantworte die Fragen. Wechsel jederzeit zwischen Tabs.</p>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)
summary_container = st.container()  # Platzhalter für die Übersicht oberhalb der Tabs

# Globales Styling (Fonts, Farben, Inputs, Buttons)
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto+Condensed:wght@400;600;700&display=swap');
    :root {
        --bg: #ffffff;
        --panel: #f7f7f7;
        --card: #ffffff;
        --muted: #4a4a4a;
        --accent1: #b83a2f;
        --accent2: #7a2e2e;
        --accent3: #c56a46;
        --text: #161616;
        --text-muted: #3a3a3a;
    }
    html, body, [class*="css"] {
        font-family: 'Roboto Condensed', 'Helvetica Neue', Arial, sans-serif;
        color: var(--text);
        background: var(--bg);
        background-image: url("file:///Users/hannazaugg/Library/Mobile%20Documents/com~apple~CloudDocs/HSLU/HS25/DT_Programming/Brandschutzkochbuch/Code/Tabellen/Flammen.png");
        background-size: cover;
        background-repeat: no-repeat;
        background-attachment: fixed;
        background-position: center;
    }
    .stApp {
        background: linear-gradient(rgba(255,255,255,0.92), rgba(255,255,255,0.92));
    }
    section.main > div {
        background: transparent;
    }
    h1, h2, h3, h4, h5 {
        color: var(--text);
        letter-spacing: 0.1px;
    }
    p, label, span {
        color: var(--text-muted);
    }
    .stTextInput > div > div > input,
    .stNumberInput input,
    .stSelectbox > div > div > select,
    .stRadio > div {
        background: var(--panel);
        color: var(--text);
        border-radius: 6px;
        border: 1px solid #3a2b2b;
    }
    .stTextInput > div > div > input:focus,
    .stNumberInput input:focus,
    .stSelectbox > div > div > select:focus {
        border-color: var(--accent1);
        box-shadow: 0 0 0 1px var(--accent1);
    }
    /* Buttons und Downloads breit selektieren */
    button,
    button[kind],
    button[data-baseweb="button"],
    div.stButton > button,
    div.stDownloadButton > button,
    div[data-testid="baseButton-secondary"] > button,
    div[data-testid="baseButton-primary"] > button,
    div[data-testid="baseButton-primaryFormSubmit"] > button,
    div[data-testid="baseButton-secondaryFormSubmit"] > button {
        background: #5a2a2a !important;
        color: #ffffff !important;
        /* falls Text-Knoten eigene Farbe erzwingen: */
        }
    button *,
    div.stButton > button *,
    div.stDownloadButton > button *,
    div[data-testid="baseButton-secondary"] > button *,
    div[data-testid="baseButton-primary"] > button *,
    div[data-testid="baseButton-primaryFormSubmit"] > button *,
    div[data-testid="baseButton-secondaryFormSubmit"] > button * {
        color: #ffffff !important;
        border: none !important;
        border-radius: 6px !important;
        font-weight: 800 !important;
        letter-spacing: 0.3px !important;
        box-shadow: none !important;
    }
    button:hover,
    button[kind]:hover,
    button[data-baseweb="button"]:hover,
    div.stButton > button:hover,
    div.stDownloadButton > button:hover,
    div[data-testid="baseButton-secondary"] > button:hover,
    div[data-testid="baseButton-primary"] > button:hover,
    div[data-testid="baseButton-primaryFormSubmit"] > button:hover,
    div[data-testid="baseButton-secondaryFormSubmit"] > button:hover {
        background: #7c3c3c !important;
        color: #ffffff !important;
        box-shadow: none !important;
    }
    button:disabled,
    button[kind]:disabled,
    button[data-baseweb="button"]:disabled,
    div.stButton > button:disabled,
    div.stDownloadButton > button:disabled,
    div[data-testid="baseButton-secondary"] > button:disabled,
    div[data-testid="baseButton-primary"] > button:disabled,
    div[data-testid="baseButton-primaryFormSubmit"] > button:disabled,
    div[data-testid="baseButton-secondaryFormSubmit"] > button:disabled {
        background: #8c6e6e !important;
        color: #ffffff !important;
        opacity: 1 !important;
        filter: none !important;
    }
    /* Tabs auf rotbraun mit weißer Schrift angleichen */
    .stTabs [role="tab"] {
        color: #5a2a2a;
        border: 1px solid #5a2a2a33;
        background: #ffffff;
        border-radius: 6px 6px 0 0;
        margin-right: 4px;
    }
    .stTabs [aria-selected="true"] {
        color: #ffffff;
        background: #5a2a2a;
        border-color: #5a2a2a;
    }
    /* Tabs sticky oben halten */
    .stTabs {
        margin-bottom: 8px;
    }
    /* Tab-Leiste normal (kein Sticky, kein Balken) */
    .stTabs [data-baseweb="tab-list"] {
        position: relative;
        top: auto;
        z-index: auto;
        background: transparent;
        padding: 6px 0;
        display: flex;
        justify-content: space-between;
        box-shadow: none;
    }
    .stTabs [role="tab"] {
        flex: 1 1 0;
        text-align: center;
        background: #f3dedd;
        color: #5a2a2a;
        border: 1px solid #5a2a2a33;
        border-bottom: none;
    }
    .stTabs [aria-selected="true"] {
        color: #ffffff;
        background: #5a2a2a;
        border-color: #5a2a2a;
    }
    /* Logo oben links einblenden (Dunkelrot) */
    .logo-container {
        position: fixed;
        top: 10px;
        left: 10px;
        z-index: 100;
    }
    .logo-container img {
        width: 48px;
        height: 48px;
        object-fit: contain;
        filter: invert(14%) sepia(57%) saturate(526%) hue-rotate(335deg) brightness(90%) contrast(90%);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Seitenleiste: Projektinfos und Sitzungsstart
with st.sidebar:
    st.image(
        "/Users/hannazaugg/Library/Mobile Documents/com~apple~CloudDocs/HSLU/HS25/DT_Programming/Brandschutzkochbuch/Code/Tabellen/Logo.svg",
        width=110,
        caption="",
    )
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
    if not storeys:
        manual_storeys = (
            st.session_state.get("manual_inputs", {}).get("storeys")
            or st.session_state.get("manual_storeys")
            or []
        )
        class _ManualStorey:
            def __init__(self, name, area):
                self.name = name
                self.area_m2 = area
        storeys = [_ManualStorey(s.get("name", f"Geschoss {i+1}"), s.get("area", 0.0)) for i, s in enumerate(manual_storeys)]

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
    usage_options = ["-", "Wohnen", "Büro", "Industrie", "Gewerbe", "Lager", "Parking", "Verschiedene", "Andere"]
    usage_current = st.session_state["question_answers"].get("usage", "-")
    usage_index = usage_options.index(usage_current) if usage_current in usage_options else 0
    usage_value = st.selectbox("Nutzung", options=usage_options, index=usage_index)
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
    manual_storeys = st.session_state.get("manual_storeys") or []
    if has_ifc_choice == "Nein" and not manual_storeys:
        manual_storeys = [{"name": "EG", "area": 0.0}]
    if has_ifc_choice == "Nein":
        manual_height_start = st.number_input(
            "Gebäudehöhe [m] (kein IFC vorhanden)",
            value=st.session_state["manual_inputs"].get("height_m") or 0.0,
            min_value=0.0,
            step=0.1,
            key="manual_height_start",
        )
        st.markdown("**Geschossflächen manuell erfassen**")
        updated_storeys = []
        for idx, storey in enumerate(manual_storeys):
            c1, c2 = st.columns([2, 1])
            name_val = c1.text_input(
                f"Geschoss {idx+1} Bezeichnung",
                value=storey.get("name", f"Geschoss {idx+1}"),
                key=f"manual_storey_name_{idx}",
            )
            area_val = c2.number_input(
                "Fläche [m²]",
                value=float(storey.get("area", 0.0) or 0.0),
                min_value=0.0,
                step=1.0,
                key=f"manual_storey_area_{idx}",
            )
            updated_storeys.append({"name": name_val, "area": area_val})

        col_add, col_del = st.columns([1, 1])
        if col_add.button("Geschoss hinzufügen"):
            updated_storeys.append({"name": f"Geschoss {len(updated_storeys)+1}", "area": 0.0})
        if updated_storeys and col_del.button("Letztes Geschoss entfernen"):
            updated_storeys = updated_storeys[:-1]

        # Summe bilden und in Session puffern
        total_manual_area = sum(s["area"] for s in updated_storeys)
        st.session_state["manual_storeys"] = updated_storeys
        st.session_state["manual_inputs"]["building_area_m2"] = total_manual_area
        st.caption(f"Summierte Geschossfläche: {total_manual_area:.2f} m²")
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
                st.session_state["manual_storeys"] = []
            else:
                # Kein IFC: manuelle Felder befüllen
                st.session_state["ifc_result"] = {"height": None, "area": None, "error": None}
                st.session_state["manual_inputs"] = {
                    "height_m": manual_height_start,
                    "building_area_m2": st.session_state["manual_inputs"].get("building_area_m2"),
                    "storeys": st.session_state.get("manual_storeys", []),
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

            # Abgeleitete Werte für Fluchtwege
            area_for_escape_form = None
            if st.session_state["ifc_result"].get("area"):
                area_for_escape_form = st.session_state["ifc_result"]["area"].building_area_m2
            if area_for_escape_form is None:
                area_for_escape_form = st.session_state["manual_inputs"].get("building_area_m2")
            escape_count_form = vertical_escape_routes(area_for_escape_form)

            def render_question_field(question, label_visibility: str = "visible"):
                current_val = st.session_state["question_answers"].get(question.key, question.default)
                if question.options and question.widget == "select":
                    st.selectbox(
                        question.prompt,
                        options=question.options,
                        index=question.options.index(current_val) if current_val in (question.options or []) else 0,
                        key=f"question_{question.key}",
                        label_visibility=label_visibility,
                    )
                elif question.options:
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
                        label_visibility=label_visibility,
                    )
                else:
                    st.text_input(
                        question.prompt,
                        value=current_val,
                        key=f"question_{question.key}",
                        label_visibility=label_visibility,
                    )

            for category, questions in grouped.items():
                st.subheader(category)
                if category.lower() == "qualitätssicherung":
                    for question in questions:
                        render_question_field(question)
                    img_cols = st.columns(2)
                    with img_cols[0]:
                        st.image(
                            "/Users/hannazaugg/Library/Mobile Documents/com~apple~CloudDocs/HSLU/HS25/DT_Programming/Brandschutzkochbuch/Code/Tabellen/3.3.1 QSS.png",
                            caption="VKF Tabelle Qualitätssicherung",
                            use_container_width=True,
                        )
                    with img_cols[1]:
                        st.image(
                            "/Users/hannazaugg/Library/Mobile Documents/com~apple~CloudDocs/HSLU/HS25/DT_Programming/Brandschutzkochbuch/Code/Tabellen/3.4.1 QSS.png",
                            caption="VKF Tabelle Qualitätssicherung (3.4.1)",
                            use_container_width=True,
                        )
                elif category.lower() == "gebäudehülle":
                    col_left, col_right = st.columns([2, 1])
                    with col_left:
                        for question in questions:
                            render_question_field(question)
                    with col_right:
                        st.image(
                            "/Users/hannazaugg/Library/Mobile Documents/com~apple~CloudDocs/HSLU/HS25/DT_Programming/Brandschutzkochbuch/Code/Tabellen/3.2.8 Anforderungen Aussenwandbekleidungssysteme.png",
                            caption="3.2.8 Anforderungen Aussenwandbekleidungssysteme",
                            use_container_width=True,
                        )
                        st.image(
                            "/Users/hannazaugg/Library/Mobile Documents/com~apple~CloudDocs/HSLU/HS25/DT_Programming/Brandschutzkochbuch/Code/Tabellen/3.3.4 Anforderungen Bedachungen.png",
                            caption="3.3.4 Anforderungen Bedachungen",
                            use_container_width=True,
                        )
                elif category.lower() == "tragwerke und brandabschnitte":
                    # Konzept-Frage mit Definitionen über gesamte Breite
                    hints_concept = """
                    <div style="border:1px solid #d9d9d9; border-radius:8px; padding:10px; background:#f9fafb; margin:6px 0 8px 0;">
                        <div style="font-weight:700; margin-bottom:6px;">Definitionen</div>
                        <div style="font-weight:600;">Bauliches Konzept</div>
                        <div style="margin-bottom:8px;">Die Schutzziele werden durch bauliche Brandschutzmassnahmen erreicht. Nutzungsbezogen können technische Brandschutzmassnahmen erforderlich sein.</div>
                        <div style="font-weight:600;">Löschanlagenkonzept</div>
                        <div>Bei einem Löschanlagenkonzept werden zu den baulichen Brandschutzmassnahmen VKF-anerkannte, stationäre Löschanlagen berücksichtigt.</div>
                    </div>
                    """
                    for question in questions:
                        if question.key == "concept_type":
                            st.markdown(f"**{question.prompt}**")
                            st.markdown(hints_concept, unsafe_allow_html=True)
                            render_question_field(question, label_visibility="collapsed")
                    # Restliche Fragen und Tabelle nebeneinander
                    col_left, col_right = st.columns([2, 1])
                    with col_left:
                        for question in questions:
                            if question.key != "concept_type":
                                render_question_field(question)
                    with col_right:
                        vkf_cat = (summary_values().get("vkf_cat") or "").lower()
                        img_path = None
                        caption = ""
                        if "geringer höhe" in vkf_cat:
                            img_path = "/Users/hannazaugg/Library/Mobile Documents/com~apple~CloudDocs/HSLU/HS25/DT_Programming/Brandschutzkochbuch/Code/Tabellen/3.7.1 Anforderungen geringe Höhe.png"
                            caption = "3.7.1 Anforderungen geringe Höhe"
                        elif "mittlerer höhe" in vkf_cat:
                            img_path = "/Users/hannazaugg/Library/Mobile Documents/com~apple~CloudDocs/HSLU/HS25/DT_Programming/Brandschutzkochbuch/Code/Tabellen/3.7.1 Anforderungen mittlere Höhe.png"
                            caption = "3.7.1 Anforderungen mittlere Höhe"
                        elif "hochhaus" in vkf_cat:
                            img_path = "/Users/hannazaugg/Library/Mobile Documents/com~apple~CloudDocs/HSLU/HS25/DT_Programming/Brandschutzkochbuch/Code/Tabellen/3.7.1 Anforderungen Hochhaus.png"
                            caption = "3.7.1 Anforderungen Hochhaus"
                        if img_path:
                            st.image(img_path, caption=caption, use_container_width=True)
                else:
                    if category.lower() == "flucht- & rettungswege":
                        hints = {
                            "compliance_exit_free": "Vertikale Fluchtwege müssen an einen sicheren Ort im Freien führen. Mehrere vertikale Fluchtwege müssen unabhängig voneinander an einen sicheren Ort im Freien führen.",
                            "compliance_doors": f"<50 Per.: ein Ausgang mit 0.9 m; <100 Personen: zwei Ausgänge mit je 0.9 m; <200 Personen: drei Ausgänge mit je 0.9 m oder zwei Ausgänge mit 0.9 m und 1.2 m; >200 Personen: mehrere Ausgänge mit mindestens je 1.2 m; Büros/Gewerbe/Industrie: Ausgänge 0.9 m zulässig. Ergebnis: {escape_count_form}",
                            "compliance_vertical_routes": f"{escape_count_form}",
                            "compliance_width": "Die Mindestbreite von horizontalen Fluchtwegen muss 1.2 m betragen.",
                            "compliance_room_sequence": "Innerhalb der Nutzungseinheit darf der Fluchtweg über maximal einen angrenzenden Raum (z. B. Kombizonen) zu einem horizontalen oder vertikalen Fluchtweg führen.",
                            "compliance_vertical_count": f"Errechnete Mindestanzahl: {escape_count_form}",
                        }
                        for question in questions:
                            if question.key in hints:
                                st.markdown(f"**{question.prompt}**")
                                st.markdown(
                                    f"""<div style="border:1px solid #d9d9d9; border-radius:8px; padding:8px; background:#f9fafb; margin:6px 0 8px 0;">
                                            <div style="font-weight:700; margin-bottom:4px;">Hinweis</div>
                                            <div>{hints[question.key]}</div>
                                        </div>""",
                                    unsafe_allow_html=True,
                                )
                                render_question_field(question, label_visibility="collapsed")
                            else:
                                render_question_field(question)
                    else:
                        for question in questions:
                            render_question_field(question)

            # WICHTIG: Submit-Button bleibt im Form-Block
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
        # Personenbelegung (Raum > / < 300) aufbereiten
        occ_raw = (st.session_state["question_answers"].get("occupancy_over_300", "nein") or "nein").lower()
        occ_txt = "Raum >300 Per." if occ_raw == "ja" else "Raum <300 Per."
        if "Flucht- & Rettungswege" in grouped_answers:
            adjusted: list[tuple[str, str, str]] = []
            for excel, prompt, ans in grouped_answers["Flucht- & Rettungswege"]:
                if excel == "Personenbelegung":
                    adjusted.append((excel, prompt, occ_txt))
                else:
                    adjusted.append((excel, prompt, ans))
            grouped_answers["Flucht- & Rettungswege"] = adjusted
        else:
            grouped_answers["Flucht- & Rettungswege"] = [("Personenbelegung", "Personenbelegung", occ_txt)]

        # Abgeleitete Kategorie für vertikale Fluchtwege
        area_for_escape = None
        if st.session_state["ifc_result"].get("area"):
            area_for_escape = st.session_state["ifc_result"]["area"].building_area_m2
        if area_for_escape is None:
            area_for_escape = st.session_state["manual_inputs"].get("building_area_m2")
        escape_count = vertical_escape_routes(area_for_escape)
        # Nur die Flucht-/Rettungs-Fragen anzeigen (ohne Definitionstexte)
        flucht_keys = {
            "compliance_exit_free": "Ausgang ins Freie",
            "compliance_doors": "Anzahl Ausgänge / Türbreiten",
            "compliance_vertical_routes": "Vertikale Fluchtwege",
            "compliance_width": "Abmessungen min. 1.20m",
            "compliance_room_sequence": "Raumabfolge",
            "compliance_vertical_count": "Vertikale Fluchtwege (Anzahl)",
            "occupancy_over_300": "Personenbelegung",
        }
        filtered = []
        for excel, prompt, ans in grouped_answers.get("Flucht- & Rettungswege", []):
            # map by key if possible
            filtered.append((excel, prompt, ans))
        # Sicherstellen, dass nur die 6 Kernfragen + Personenbelegung stehen
        grouped_answers["Flucht- & Rettungswege"] = filtered

        categories = [c for c in grouped_answers.keys() if c.lower() != "projekt"]
        cols = st.columns(2)
        # Farbige Kacheln in Rot-/Brauntönen
        palette = ["#3b1a1a", "#4a2222", "#5a2a2a", "#6b3333", "#7c3c3c", "#8e4646"]
        for idx, cat in enumerate(categories):
            bg = palette[idx % len(palette)]
            with cols[idx % 2]:
                st.markdown(
                    f"""
                    <div style="background:{bg}; padding:12px 14px; border-radius:8px; margin-bottom:12px; color:#fff;">
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

# Excel-Download (nur wenn IFC-Ergebnisse vorhanden)
with tab_dashboard:
    if st.session_state.get("project_started") and st.session_state["ifc_result"].get("height") and st.session_state["ifc_result"].get("area"):
        height_res = st.session_state["ifc_result"]["height"]
        area_res = st.session_state["ifc_result"]["area"]
        extra_cols = answers_for_excel(st.session_state["question_answers"], DEFAULT_QUESTIONS)

        template_path = "/Users/hannazaugg/Library/Mobile Documents/com~apple~CloudDocs/HSLU/HS25/DT_Programming/Brandschutzkochbuch/Code/Excel/10000_BSKo-Kochbuch_JJJJ-MM-TT.xlsx"

        if st.button("Excel exportieren"):
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
            tmp.close()
            data = None
            try:
                try:
                    from excel import write_result_to_template
                    write_result_to_template(height_res, area_res, template_path, tmp.name, extra_columns=extra_cols)
                except FileNotFoundError:
                    from excel import write_result_to_excel
                    write_result_to_excel(height_res, area_res, tmp.name, extra_columns=extra_cols)

                with open(tmp.name, "rb") as f:
                    data = f.read()
            finally:
                try:
                    os.unlink(tmp.name)
                except Exception:
                    pass

            if data:
                proj_num = st.session_state.get("project_info", {}).get("number") or "00000"
                today = datetime.now().strftime("%Y-%m-%d")
                file_name = f"{proj_num}_BSKo-Kochbuch_{today}.xlsx"
                st.download_button(
                    "Download Excel",
                    data=data,
                    file_name=file_name,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
