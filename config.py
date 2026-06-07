"""
Configuratie voor de PII-anonimiseringstool.

Bevat:
- de talen en bijbehorende NLP-modellen,
- de standaard te detecteren entiteiten,
- de Nederlandse/Engelse labels die in de plaats van gevonden gegevens komen,
- maatwerk-herkenners voor Nederlandse gegevens (BSN, postcode, telefoonnummer).

Het detectiedeel leunt op Microsoft Presidio. Presidio combineert een
NER-model (via spaCy) met regelgebaseerde herkenners. Per taal wordt één
spaCy-model geladen. Nederlands is de standaard; Engels is optioneel
beschikbaar door een ander spaCy-model in te laden.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Talen en modellen
# ---------------------------------------------------------------------------
# Per taalcode het spaCy-model dat Presidio gebruikt voor naam-, locatie- en
# organisatieherkenning. De "lg" (large) modellen geven duidelijk betere
# resultaten dan de "sm" (small) modellen, ten koste van geheugen en snelheid.
LANGUAGE_MODELS: dict[str, str] = {
    "nl": "nl_core_news_lg",
    "en": "en_core_web_lg",
}

DEFAULT_LANGUAGE = "nl"

LANGUAGE_LABELS: dict[str, str] = {
    "nl": "Nederlands",
    "en": "Engels (English)",
}

# ---------------------------------------------------------------------------
# Entiteiten
# ---------------------------------------------------------------------------
# De entiteiten die de tool standaard probeert te vinden. De NER-entiteiten
# (PERSON, LOCATION, ORGANIZATION) komen uit het spaCy-model; de overige komen
# uit regelgebaseerde herkenners van Presidio of uit maatwerk hieronder.
DEFAULT_ENTITIES: list[str] = [
    "PERSON",
    "LOCATION",
    "ORGANIZATION",
    "EMAIL_ADDRESS",
    "PHONE_NUMBER",
    "IBAN_CODE",
    "CREDIT_CARD",
    "IP_ADDRESS",
    "URL",
    "DATE_TIME",
    "NL_BSN",
    "NL_POSTCODE",
]

# Vervangingslabels per taal. De gevonden tekst wordt vervangen door het label,
# bijvoorbeeld "Jan Jansen" -> "[NAAM]".
ENTITY_LABELS: dict[str, dict[str, str]] = {
    "nl": {
        "PERSON": "NAAM",
        "LOCATION": "LOCATIE",
        "ORGANIZATION": "ORGANISATIE",
        "EMAIL_ADDRESS": "E-MAILADRES",
        "PHONE_NUMBER": "TELEFOONNUMMER",
        "IBAN_CODE": "IBAN",
        "CREDIT_CARD": "CREDITCARD",
        "IP_ADDRESS": "IP-ADRES",
        "URL": "URL",
        "DATE_TIME": "DATUM",
        "NL_BSN": "BSN",
        "NL_POSTCODE": "POSTCODE",
        "_DEFAULT": "GEGEVEN",
    },
    "en": {
        "PERSON": "NAME",
        "LOCATION": "LOCATION",
        "ORGANIZATION": "ORGANIZATION",
        "EMAIL_ADDRESS": "EMAIL",
        "PHONE_NUMBER": "PHONE",
        "IBAN_CODE": "IBAN",
        "CREDIT_CARD": "CREDIT_CARD",
        "IP_ADDRESS": "IP_ADDRESS",
        "URL": "URL",
        "DATE_TIME": "DATE",
        "NL_BSN": "BSN",
        "NL_POSTCODE": "POSTCODE",
        "_DEFAULT": "REDACTED",
    },
}

# Korte, leesbare omschrijving per entiteit voor de gebruikersinterface.
ENTITY_DESCRIPTIONS: dict[str, str] = {
    "PERSON": "Persoonsnamen (incl. initialen en voorvoegsels)",
    "LOCATION": "Plaatsen, adressen, geografische locaties",
    "ORGANIZATION": "Namen van organisaties, bedrijven, instellingen",
    "EMAIL_ADDRESS": "E-mailadressen",
    "PHONE_NUMBER": "Telefoonnummers",
    "IBAN_CODE": "IBAN-rekeningnummers",
    "CREDIT_CARD": "Creditcardnummers",
    "IP_ADDRESS": "IP-adressen",
    "URL": "Webadressen (URL's)",
    "DATE_TIME": "Datums en tijdstippen",
    "NL_BSN": "Burgerservicenummers (met 11-proefcontrole)",
    "NL_POSTCODE": "Nederlandse postcodes (1234 AB)",
}


def label_for(entity_type: str, language: str) -> str:
    """Geef het vervangingslabel voor een entiteit in de gekozen taal."""
    labels = ENTITY_LABELS.get(language, ENTITY_LABELS["nl"])
    return labels.get(entity_type, labels["_DEFAULT"])


# ---------------------------------------------------------------------------
# Maatwerk-herkenners voor Nederland
# ---------------------------------------------------------------------------
# Deze worden alleen geladen wanneer de bibliotheek 'presidio_analyzer'
# beschikbaar is. Ze worden lui (lazy) gebouwd zodat config.py ook zonder
# Presidio importeerbaar blijft (handig voor tests en voor de regex-fallback).


def _bsn_is_valid(digits: str) -> bool:
    """
    Controleer een BSN met de elfproef.

    Een geldig BSN heeft 8 of 9 cijfers. De gewogen som
    (9*d1 + 8*d2 + ... + 2*d8 - 1*d9) moet deelbaar zijn door 11.
    """
    if not digits.isdigit():
        return False
    if len(digits) not in (8, 9):
        return False
    if len(set(digits)) == 1:  # 000000000 e.d. uitsluiten
        return False
    digits = digits.zfill(9)
    weights = [9, 8, 7, 6, 5, 4, 3, 2, -1]
    total = sum(int(d) * w for d, w in zip(digits, weights))
    return total % 11 == 0


def build_custom_recognizers():
    """
    Bouw de Nederlandse maatwerk-herkenners.

    Retourneert een lijst met Presidio-herkenners. Alleen aanroepen wanneer
    presidio_analyzer geïnstalleerd is.
    """
    from presidio_analyzer import Pattern, PatternRecognizer

    # --- BSN -------------------------------------------------------------
    class BsnRecognizer(PatternRecognizer):
        """Herkent een BSN en valideert met de elfproef."""

        def __init__(self):
            patterns = [
                Pattern(
                    name="bsn_9_cijfers",
                    regex=r"\b[0-9]{8,9}\b",
                    score=0.3,  # lage basisscore; validatie verhoogt deze
                )
            ]
            super().__init__(
                supported_entity="NL_BSN",
                patterns=patterns,
                context=["bsn", "burgerservicenummer", "sofinummer"],
                supported_language="nl",
            )

        def validate_result(self, pattern_text: str):
            cleaned = pattern_text.replace(" ", "").replace("-", "")
            return _bsn_is_valid(cleaned)

    # --- Postcode --------------------------------------------------------
    nl_postcode = PatternRecognizer(
        supported_entity="NL_POSTCODE",
        patterns=[
            Pattern(
                name="nl_postcode",
                # 1234 AB / 1234AB; eerste cijfer niet 0
                regex=r"\b[1-9][0-9]{3}\s?[A-Za-z]{2}\b",
                score=0.6,
            )
        ],
        context=["postcode", "adres", "woonplaats"],
        supported_language="nl",
    )

    # --- Telefoonnummer (NL) --------------------------------------------
    # Aanvulling op de ingebouwde PhoneRecognizer, specifiek voor 06-nummers
    # en vaste nummers met landcode of kengetal.
    nl_phone = PatternRecognizer(
        supported_entity="PHONE_NUMBER",
        patterns=[
            Pattern(
                name="nl_mobiel",
                regex=r"\b(?:\+31\s?6|06)[-\s]?[0-9]{8}\b",
                score=0.7,
            ),
            Pattern(
                name="nl_vast",
                regex=r"\b(?:\+31\s?|0)[1-9][0-9]{1,2}[-\s]?[0-9]{6,7}\b",
                score=0.5,
            ),
        ],
        context=["telefoon", "tel", "telefoonnummer", "mobiel", "bereikbaar"],
        supported_language="nl",
    )

    return [BsnRecognizer(), nl_postcode, nl_phone]
