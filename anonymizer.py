"""
Detectie en vervanging van persoonsgegevens (PII).

Hoofdpad: Microsoft Presidio met een spaCy-model per taal. Presidio levert
naam-/locatie-/organisatieherkenning (NER) plus regelgebaseerde herkenners.

Terugvalpad: als Presidio of het spaCy-model niet geïnstalleerd is, gebruikt
de tool een eenvoudige regex-detector. Die vindt alleen *gestructureerde*
gegevens (e-mail, telefoon, IBAN, BSN, postcode, IP, URL, creditcard) en dus
GEEN namen of locaties. De interface meldt dit duidelijk aan de gebruiker.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from . import config


@dataclass
class Detection:
    """Eén gevonden stuk persoonsgegeven in een tekst."""

    start: int
    end: int
    entity_type: str
    score: float


# ---------------------------------------------------------------------------
# Regex-terugval (geen NER; alleen gestructureerde gegevens)
# ---------------------------------------------------------------------------
_FALLBACK_PATTERNS: list[tuple[str, re.Pattern, float]] = [
    ("EMAIL_ADDRESS", re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"), 0.9),
    ("IBAN_CODE", re.compile(r"\b[A-Z]{2}[0-9]{2}[ ]?(?:[A-Z0-9]{4}[ ]?){2,7}[A-Z0-9]{1,4}\b"), 0.8),
    ("IP_ADDRESS", re.compile(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b"), 0.6),
    ("URL", re.compile(r"\bhttps?://[^\s]+\b"), 0.8),
    ("CREDIT_CARD", re.compile(r"\b(?:[0-9]{4}[ \-]?){3}[0-9]{4}\b"), 0.5),
    ("PHONE_NUMBER", re.compile(r"\b(?:\+31\s?6|06)[-\s]?[0-9]{8}\b"), 0.7),
    ("NL_POSTCODE", re.compile(r"\b[1-9][0-9]{3}\s?[A-Za-z]{2}\b"), 0.6),
]


def _fallback_detect(text: str) -> list[Detection]:
    found: list[Detection] = []
    for entity_type, pattern, score in _FALLBACK_PATTERNS:
        for m in pattern.finditer(text):
            found.append(Detection(m.start(), m.end(), entity_type, score))
    # BSN met elfproef-validatie
    for m in re.finditer(r"\b[0-9]{8,9}\b", text):
        if config._bsn_is_valid(m.group()):
            found.append(Detection(m.start(), m.end(), "NL_BSN", 0.85))
    return found


# ---------------------------------------------------------------------------
# Overlap-afhandeling
# ---------------------------------------------------------------------------
def resolve_overlaps(detections: list[Detection]) -> list[Detection]:
    """
    Verwijder overlappende detecties. Bij overlap wint de detectie met de
    hoogste score; bij gelijke score de langste. Het resultaat is een lijst
    niet-overlappende detecties, gesorteerd op startpositie.
    """
    ordered = sorted(detections, key=lambda d: (-d.score, -(d.end - d.start), d.start))
    chosen: list[Detection] = []
    for d in ordered:
        if any(not (d.end <= c.start or d.start >= c.end) for c in chosen):
            continue  # overlapt met een al gekozen (sterkere) detectie
        chosen.append(d)
    chosen.sort(key=lambda d: d.start)
    return chosen


# ---------------------------------------------------------------------------
# Anonymizer
# ---------------------------------------------------------------------------
class PIIAnonymizer:
    """
    Detecteert en vervangt persoonsgegevens in losse tekstfragmenten.

    De analyzer wordt per taal opgebouwd en gecachet. Wanneer Presidio niet
    beschikbaar is, valt de klasse terug op regex-detectie.
    """

    def __init__(
        self,
        language: str = config.DEFAULT_LANGUAGE,
        entities: list[str] | None = None,
        score_threshold: float = 0.4,
    ):
        self.language = language
        self.entities = entities if entities is not None else list(config.DEFAULT_ENTITIES)
        self.score_threshold = score_threshold
        self._analyzer = None
        self._engine_name = "regex-fallback"
        self._build_analyzer()

    # -- opbouw ----------------------------------------------------------
    def _build_analyzer(self) -> None:
        """Probeer een Presidio-analyzer te bouwen; val anders terug op regex."""
        try:
            import spacy.util
            from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
            from presidio_analyzer.nlp_engine import NlpEngineProvider
        except ImportError:
            self._analyzer = None
            self._engine_name = "regex-fallback"
            return

        model_name = config.LANGUAGE_MODELS.get(self.language)
        if model_name is None:
            raise ValueError(f"Niet-ondersteunde taal: {self.language}")

        # Controleer of het spaCy-model geïnstalleerd is vóórdat we het laden.
        # Doen we dat niet, dan probeert spaCy het model via pip te downloaden
        # (wat mislukt en het programma kan afbreken).
        if not spacy.util.is_package(model_name):
            self._analyzer = None
            self._engine_name = "regex-fallback"
            self._engine_error = f"spaCy-model '{model_name}' is niet geïnstalleerd"
            return

        try:
            nlp_configuration = {
                "nlp_engine_name": "spacy",
                "models": [{"lang_code": self.language, "model_name": model_name}],
            }
            provider = NlpEngineProvider(nlp_configuration=nlp_configuration)
            nlp_engine = provider.create_engine()

            registry = RecognizerRegistry()
            registry.load_predefined_recognizers(
                languages=[self.language], nlp_engine=nlp_engine
            )

            # Nederlandse maatwerk-herkenners toevoegen
            if self.language == "nl":
                for recognizer in config.build_custom_recognizers():
                    registry.add_recognizer(recognizer)

            self._analyzer = AnalyzerEngine(
                registry=registry,
                nlp_engine=nlp_engine,
                supported_languages=[self.language],
            )
            self._engine_name = f"presidio + spaCy ({model_name})"
        except (Exception, SystemExit) as exc:  # model niet (correct) geladen
            self._analyzer = None
            self._engine_name = "regex-fallback"
            self._engine_error = str(exc)

    # -- eigenschappen ---------------------------------------------------
    @property
    def engine_name(self) -> str:
        return self._engine_name

    @property
    def uses_ner(self) -> bool:
        """True als namen/locaties herkend kunnen worden (volledig model actief)."""
        return self._analyzer is not None

    # -- detectie --------------------------------------------------------
    def detect(self, text: str) -> list[Detection]:
        """Vind persoonsgegevens in een tekst en geef niet-overlappende treffers."""
        if not text or not text.strip():
            return []

        if self._analyzer is not None:
            results = self._analyzer.analyze(
                text=text,
                language=self.language,
                entities=self.entities,
                score_threshold=self.score_threshold,
            )
            detections = [
                Detection(r.start, r.end, r.entity_type, r.score) for r in results
            ]
        else:
            detections = [
                d
                for d in _fallback_detect(text)
                if d.entity_type in self.entities and d.score >= self.score_threshold
            ]

        return resolve_overlaps(detections)

    # -- vervanging ------------------------------------------------------
    def build_replacements(
        self, text: str, style: str = "tag"
    ) -> list[tuple[int, int, str]]:
        """
        Bouw een lijst (start, eind, vervangtekst) voor een tekst.

        style:
          - "tag":    vervang door een leesbaar label, bijv. [NAAM]
          - "redact": vervang door blokjes (████) van dezelfde lengte
        """
        replacements: list[tuple[int, int, str]] = []
        for d in self.detect(text):
            if style == "redact":
                repl = "█" * (d.end - d.start)
            else:  # "tag"
                repl = f"[{config.label_for(d.entity_type, self.language)}]"
            replacements.append((d.start, d.end, repl))
        return replacements

    def anonymize_text(self, text: str, style: str = "tag") -> tuple[str, list[Detection]]:
        """Anonimiseer een losse tekst en geef het resultaat plus de treffers terug."""
        detections = self.detect(text)
        replacements = []
        for d in detections:
            if style == "redact":
                repl = "█" * (d.end - d.start)
            else:
                repl = f"[{config.label_for(d.entity_type, self.language)}]"
            replacements.append((d.start, d.end, repl))
        # rechts-naar-links toepassen zodat posities geldig blijven
        for start, end, repl in sorted(replacements, key=lambda x: x[0], reverse=True):
            text = text[:start] + repl + text[end:]
        return text, detections
