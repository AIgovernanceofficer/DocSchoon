# 🔒 PII-anonimiseren

[![tests](https://github.com/JOUW-GEBRUIKERSNAAM/pii-anonimiseren/actions/workflows/tests.yml/badge.svg)](https://github.com/JOUW-GEBRUIKERSNAAM/pii-anonimiseren/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Een lokaal draaiende tool die persoonsgegevens (PII) verwijdert uit
**Word-, PowerPoint-, Excel- en tekstbestanden**. Je uploadt een bestand,
de tool spoort persoonsgegevens op en vervangt ze, en je downloadt een schone
versie — met behoud van de oorspronkelijke opmaak.

De tool is gericht op het **Nederlands**, met optionele uitbreiding naar het
**Engels**. Alle verwerking gebeurt op je eigen machine; er gaan geen
gegevens naar een externe dienst.

---

## ⚠️ Belangrijk vooraf: privacy en juridisch

- **Lokaal en zonder cloud.** De detectie gebruikt open-source modellen die
  volledig op je eigen computer draaien. Geüploade bestanden verlaten je
  machine niet. Dat maakt de tool geschikt voor AVG-gevoelig materiaal.
- **De-identificatie is geen garantie op anonimiteit.** Automatische detectie
  verkleint het *risico* op herleiding, maar het resultaat is juridisch
  doorgaans **gepseudonimiseerd**, niet volledig anoniem. Combinaties van
  resterende gegevens kunnen iemand alsnog identificeerbaar maken.
- **Controleer altijd handmatig.** Geen enkel model haalt 100% van de
  gegevens. Juist de gemiste gevallen vormen het risico. Beschouw de tool als
  een krachtige eerste stap, niet als eindcontrole.

---

## Ondersteunde bestandstypen

| Type | Extensie | Bibliotheek |
|------|----------|-------------|
| Word | `.docx` | python-docx |
| PowerPoint | `.pptx` | python-pptx |
| Excel | `.xlsx` | openpyxl |
| Platte tekst | `.txt` | — |

Oudere formaten (`.doc`, `.ppt`, `.xls`) worden niet rechtstreeks ondersteund;
sla die eerst op als het moderne formaat.

---

## Installatie

> Vereist: **Python 3.10 of hoger**.

```bash
# 1. Repository ophalen
git clone https://github.com/JOUW-GEBRUIKERSNAAM/pii-anonimiseren.git
cd pii-anonimiseren

# 2. Virtuele omgeving aanmaken en activeren
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Afhankelijkheden installeren
pip install -r requirements.txt

# 4. Taalmodel(len) downloaden  ← belangrijke stap!
python -m spacy download nl_core_news_lg      # Nederlands (vereist)
python -m spacy download en_core_web_lg       # Engels (optioneel)
```

**Waarom stap 4 apart staat:** de spaCy-taalmodellen zijn groot (~500 MB per
stuk) en worden daarom niet automatisch meegeïnstalleerd. Zonder model draait
de tool in **beperkte modus** (zie hieronder).

### Beperkte modus (regex-terugval)

Zolang het taalmodel nog niet is gedownload, werkt de tool in een
terugvalmodus die alleen **gestructureerde gegevens** vindt: e-mailadressen,
telefoonnummers, IBAN, BSN, postcodes, IP-adressen, URL's en creditcardnummers.
**Namen, locaties en organisaties worden dan níét herkend**, omdat daarvoor het
taalmodel nodig is. De interface toont duidelijk in welke modus je zit.

---

## Gebruik

### Optie A — Webinterface (aanbevolen)

```bash
streamlit run app.py
```

Er opent een pagina in je browser. Daar kun je:

1. in de zijbalk de **taal** kiezen (Nederlands of Engels);
2. kiezen hoe gegevens vervangen worden — een **leesbaar label** (`[NAAM]`)
   of **zwart maken** (████);
3. de **zekerheidsdrempel** instellen (lager = meer vinden, hoger = alleen
   zekere treffers);
4. aanvinken **welke soorten gegevens** je wilt verwijderen;
5. één of meer bestanden **uploaden** en op **Anonimiseer** klikken;
6. per bestand een overzicht van de vervangingen zien en de **schone versie
   downloaden**.

### Optie B — Opdrachtregel (voor batch/automatisering)

```bash
# Eén bestand, standaardinstellingen (Nederlands, labels)
python cli.py document.docx

# Meerdere bestanden naar een uitvoermap, met zwart maken
python cli.py *.docx --stijl redact --uitvoer schoon/

# Engels, hogere drempel
python cli.py report.pptx --taal en --drempel 0.5
```

Schone bestanden krijgen het achtervoegsel `_geanonimiseerd`, bijvoorbeeld
`document_geanonimiseerd.docx`.

---

## Hoe het werkt

De tool bestaat uit twee losse delen:

**1. Detectie van persoonsgegevens** — gebouwd op
[Microsoft Presidio](https://microsoft.github.io/presidio/). Presidio
combineert:

- een **NER-taalmodel** (via spaCy) dat namen, locaties en organisaties
  herkent op basis van context, en
- **regelgebaseerde herkenners** voor gegevens met een vast patroon
  (e-mail, IBAN, telefoon, enzovoort).

Daar bovenop zitten **Nederlandse maatwerk-herkenners**:

- **BSN** met een echte *elfproef*-validatie (alleen geldige nummers worden
  als BSN gemarkeerd, wat vals alarm sterk vermindert);
- **postcode** (`1234 AB`);
- **telefoonnummers** in Nederlandse notatie (06-nummers en vaste nummers).

**2. Bestandsverwerking met behoud van opmaak.** In Word en PowerPoint is een
alinea opgebouwd uit "runs" — stukjes tekst met elk hun eigen opmaak. Eén naam
kan over meerdere runs verdeeld zijn. De tool plakt daarom eerst de tekst van
een hele alinea aan elkaar, detecteert daarop, en zet de vervangingen terug op
de exacte tekenposities in de juiste runs. Zo blijven lettertype, vet en kleur
van de omliggende tekst intact en worden ook gegevens gevonden die over
meerdere runs lopen.

---

## Nederlands en Engels (en verder uitbreiden)

De taalkeuze bepaalt welk NLP-model wordt geladen:

| Taal | spaCy-model |
|------|-------------|
| Nederlands (`nl`) | `nl_core_news_lg` |
| Engels (`en`) | `en_core_web_lg` |

Een andere taal of een ander model toevoegen kan in
[`src/config.py`](src/config.py): voeg een regel toe aan `LANGUAGE_MODELS`
(taalcode → spaCy-modelnaam) en eventueel vertaalde labels aan
`ENTITY_LABELS`. Download daarna het bijbehorende spaCy-model. De Nederlandse
maatwerk-herkenners (BSN, postcode) blijven taalspecifiek en worden alleen bij
`nl` geladen.

> Wil je een sterker of domeinspecifiek model gebruiken (bijvoorbeeld een
> getraind transformer-model van Hugging Face)? Presidio ondersteunt dat via
> een eigen NER-herkenner. Dat valt buiten deze basisversie, maar de opzet
> (`_build_analyzer` in `src/anonymizer.py`) is daarop voorbereid.

---

## Welke gegevens worden herkend

| Entiteit | Omschrijving | Vereist taalmodel? |
|----------|--------------|:------------------:|
| Naam | Persoonsnamen incl. initialen/voorvoegsels | ja |
| Locatie | Plaatsen, adressen, geografische locaties | ja |
| Organisatie | Bedrijven, instellingen | ja |
| E-mailadres | E-mailadressen | nee |
| Telefoonnummer | Telefoonnummers (NL-notatie) | nee |
| IBAN | Rekeningnummers | nee |
| BSN | Burgerservicenummers (met elfproef) | nee |
| Postcode | Nederlandse postcodes | nee |
| Creditcard | Creditcardnummers | nee |
| IP-adres | IP-adressen | nee |
| URL | Webadressen | nee |
| Datum | Datums en tijdstippen | ja |

De entiteiten zonder taalmodel werken ook in de beperkte (regex-)modus.

---

## Beperkingen en aandachtspunten

- **Geen volledige garantie.** De recall (aandeel gevonden gegevens) is hoog
  maar nooit 100%. Controleer het resultaat.
- **Vals alarm komt voor.** Vooral bij namen die ook gewone woorden zijn.
  Stel de zekerheidsdrempel af op je documenttype.
- **Modellen zijn algemeen.** De standaard spaCy-modellen zijn niet getraind
  op een specifiek domein (zoals onderwijs of zorg). Voor gespecialiseerd
  materiaal kan een domeinspecifiek model betere resultaten geven.
- **Tabellen, kop- en voetteksten en notities** worden meegenomen; tekst in
  afbeeldingen (gescande documenten) niet — daarvoor is OCR nodig.

---

## Projectstructuur

```
pii-anonimiseren/
├── app.py                     # Streamlit-webinterface
├── cli.py                     # Opdrachtregel-interface
├── requirements.txt
├── README.md
├── LICENSE
├── src/
│   ├── config.py              # talen, entiteiten, maatwerk-herkenners
│   ├── anonymizer.py          # detectie (Presidio + regex-terugval)
│   └── document_handlers.py   # lezen/anonimiseren/schrijven per formaat
├── examples/                  # voorbeeldbestanden met fictieve gegevens
├── tests/                     # pytest-tests
└── .github/workflows/         # CI: tests bij elke push
```

---

## Tests

```bash
pytest -q
```

De tests draaien in regex-terugvalmodus en hebben het zware taalmodel dus niet
nodig. Ze controleren onder andere de elfproef-validatie, de overlap-
afhandeling, de opmaakbehoudende run-bewerking en de volledige round-trip per
bestandstype.

---

## Licentie

[MIT](LICENSE). Gebruik, aanpassing en verspreiding zijn vrij toegestaan, met
behoud van de licentievermelding. De tool wordt geleverd zonder garantie;
de verantwoordelijkheid voor correcte anonimisering blijft bij de gebruiker.
