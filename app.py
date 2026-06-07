"""
Webinterface voor de PII-anonimiseringstool.

Start lokaal met:
    streamlit run app.py

De app draait volledig op de eigen machine. Geüploade bestanden worden
verwerkt in het werkgeheugen/tijdelijke mappen en niet naar een externe dienst
verstuurd.
"""

from __future__ import annotations

import os
import tempfile

import streamlit as st

from src import config
from src.anonymizer import PIIAnonymizer
from src.document_handlers import SUPPORTED_EXTENSIONS, anonymize_file

st.set_page_config(page_title="PII-anonimiseren", page_icon="🔒", layout="centered")


@st.cache_resource(show_spinner="NLP-model laden…")
def get_anonymizer(language: str) -> PIIAnonymizer:
    """Bouw (en cache) één analyzer per taal."""
    return PIIAnonymizer(language=language)


# ---------------------------------------------------------------------------
# Kop
# ---------------------------------------------------------------------------
st.title("🔒 Persoonsgegevens verwijderen")
st.markdown(
    "Upload een Word-, PowerPoint-, Excel- of tekstbestand. De tool spoort "
    "persoonsgegevens op, vervangt ze, en geeft een schone versie terug om te "
    "downloaden. **Alles draait lokaal** — er gaan geen gegevens naar internet."
)

# ---------------------------------------------------------------------------
# Zijbalk: instellingen
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("Instellingen")

    language = st.selectbox(
        "Taal van de documenten",
        options=list(config.LANGUAGE_MODELS.keys()),
        format_func=lambda code: config.LANGUAGE_LABELS.get(code, code),
        index=list(config.LANGUAGE_MODELS.keys()).index(config.DEFAULT_LANGUAGE),
        help="Nederlands is de standaard. Engels gebruikt een ander NLP-model.",
    )

    anonymizer = get_anonymizer(language)

    style_label = st.radio(
        "Manier van vervangen",
        options=["Label tonen (bijv. [NAAM])", "Zwart maken (████)"],
        help="Een label houdt leesbaar wát er weg is; zwart maken verbergt dat ook.",
    )
    style = "redact" if style_label.startswith("Zwart") else "tag"

    threshold = st.slider(
        "Zekerheidsdrempel",
        min_value=0.0,
        max_value=1.0,
        value=0.4,
        step=0.05,
        help="Lager = meer vinden (meer kans op vals alarm). "
        "Hoger = alleen zekere treffers.",
    )
    anonymizer.score_threshold = threshold

    st.subheader("Welke gegevens?")
    selected = []
    for entity in config.DEFAULT_ENTITIES:
        desc = config.ENTITY_DESCRIPTIONS.get(entity, entity)
        if st.checkbox(desc, value=True, key=f"ent_{entity}"):
            selected.append(entity)
    anonymizer.entities = selected

# ---------------------------------------------------------------------------
# Status van de motor
# ---------------------------------------------------------------------------
if anonymizer.uses_ner:
    st.success(f"Actieve motor: **{anonymizer.engine_name}** — namen en locaties worden herkend.")
else:
    st.warning(
        "**Beperkte modus (regex-terugval).** Het taalmodel is nog niet "
        "geïnstalleerd, dus alleen gestructureerde gegevens (e-mail, telefoon, "
        "IBAN, BSN, postcode, IP, URL, creditcard) worden gevonden — **geen "
        "namen, locaties of organisaties**. Zie de README om het volledige "
        "model te installeren."
    )

# ---------------------------------------------------------------------------
# Upload en verwerking
# ---------------------------------------------------------------------------
uploaded = st.file_uploader(
    "Kies één of meer bestanden",
    type=[ext.lstrip(".") for ext in SUPPORTED_EXTENSIONS],
    accept_multiple_files=True,
)

if uploaded and not selected:
    st.error("Selecteer minstens één type gegeven in de zijbalk.")

if uploaded and selected:
    if st.button("Anonimiseer", type="primary"):
        with tempfile.TemporaryDirectory() as tmp:
            for file in uploaded:
                in_path = os.path.join(tmp, file.name)
                with open(in_path, "wb") as f:
                    f.write(file.getbuffer())

                base, ext = os.path.splitext(file.name)
                out_name = f"{base}_geanonimiseerd{ext}"
                out_path = os.path.join(tmp, out_name)

                try:
                    with st.spinner(f"Bezig met {file.name}…"):
                        result = anonymize_file(in_path, out_path, anonymizer, style)
                except Exception as exc:  # nette foutmelding i.p.v. crash
                    st.error(f"{file.name}: er ging iets mis — {exc}")
                    continue

                with st.container(border=True):
                    st.markdown(f"### {file.name}")
                    if result.total_replacements == 0:
                        st.info("Geen persoonsgegevens gevonden.")
                    else:
                        st.write(
                            f"**{result.total_replacements}** vervangingen gemaakt:"
                        )
                        for entity_type, n in sorted(
                            result.counts_by_type.items(), key=lambda x: -x[1]
                        ):
                            label = config.label_for(entity_type, language)
                            st.write(f"- {label}: {n}")

                    with open(out_path, "rb") as f:
                        st.download_button(
                            label=f"⬇️ Download {out_name}",
                            data=f.read(),
                            file_name=out_name,
                            key=f"dl_{file.name}",
                        )

# ---------------------------------------------------------------------------
# Voetnoot met waarschuwing
# ---------------------------------------------------------------------------
st.divider()
st.caption(
    "⚠️ Controleer het resultaat altijd handmatig. Automatische detectie is "
    "nooit 100% sluitend. De-identificatie verkleint het risico op herleiding "
    "maar levert juridisch doorgaans gepseudonimiseerde, niet volledig anonieme "
    "gegevens op."
)
