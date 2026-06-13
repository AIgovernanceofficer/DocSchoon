# 🫥 DocSchoon

**Verwijder persoonsgegevens uit Word-, PowerPoint-, Excel- en tekstbestanden — direct in je browser, zonder installatie.**

> ⚠️ **Geen officiële privacy-applicatie.** Dit is een experimenteel hulpmiddel,
> niet gevalideerd door een toezichthouder en zonder juridische garanties.
> Controleer het resultaat altijd handmatig. Zie [Beperkingen](#beperkingen-en-juridische-status)
> hieronder.

---

## Wat doet DocSchoon?

Je uploadt een document, DocSchoon spoort persoonsgegevens op (namen,
e-mailadressen, BSN's, telefoonnummers, adressen, enzovoort), vervangt ze, en
je downloadt direct een schone versie — met behoud van de oorspronkelijke
opmaak (lettertype, vet, kleur, lay-out blijven intact).

Alles gebeurt **in je browser**. Er is geen installatie, geen account en geen
server nodig.

👉 **[Open de app](index.html)**

---

## Ondersteunde bestanden

| Type | Extensie |
|------|----------|
| Word | `.docx` |
| PowerPoint | `.pptx` |
| Excel | `.xlsx` |
| Platte tekst | `.txt` |

---

## Welke AI wordt gebruikt — en hoe

DocSchoon werkt op **twee niveaus** van detectie. Je kiest zelf of je alleen
het eerste niveau gebruikt, of ook het tweede inschakelt.

### 1. Standaard: lokale patroonherkenning (geen AI)

Zonder verdere instellingen detecteert DocSchoon **gestructureerde
gegevens** met vaste patronen (reguliere expressies), volledig lokaal in je
browser:

- e-mailadressen
- telefoonnummers (Nederlandse notatie)
- BSN — met een echte **elfproef-validatie**, zodat alleen geldige
  burgerservicenummers worden gemarkeerd
- IBAN-rekeningnummers
- Nederlandse postcodes
- IP-adressen
- URL's
- creditcardnummers

Hier is **geen AI bij betrokken** en verlaat **geen tekst je browser**. Dit
niveau vindt geen namen, locaties of organisaties — daarvoor is begrip van
de zin nodig, en dat kan een patroon niet.

### 2. Optioneel: AI-detectie met Claude (Anthropic)

Voor **namen, locaties, organisaties en datums** is begrip van de context
nodig. Daarvoor kun je in de app de schakelaar *"Anthropic API inschakelen"*
aanzetten en je eigen API-sleutel invoeren.

Wat er dan gebeurt:

- De tekst van je document (tot ongeveer 8.000 tekens per onderdeel) wordt
  via een directe API-aanroep naar **Claude** (het taalmodel van Anthropic)
  gestuurd.
- Claude analyseert de tekst en geeft terug welke stukken tekst namen,
  locaties, organisaties of datums zijn.
- DocSchoon gebruikt die informatie om de gevonden tekst te vervangen, net
  als bij de patroonherkenning.

**Belangrijk om te weten:**

- Dit gebeurt **alleen als jij de schakelaar zelf aanzet**. Standaard staat
  hij uit.
- Je gebruikt **je eigen API-sleutel**, die je rechtstreeks bij
  [console.anthropic.com](https://console.anthropic.com) aanvraagt. De
  sleutel wordt alleen lokaal in je browser gebruikt voor de API-aanroep en
  nergens door DocSchoon opgeslagen.
- Zodra je deze optie gebruikt, **verlaat de inhoud van je document je
  browser** en gaat naar Anthropic's API. Gebruik dit **niet** voor strikt
  vertrouwelijke documenten zonder dat je hiervoor toestemming of een
  verwerkersovereenkomst hebt geregeld.
- Anthropic's eigen voorwaarden en privacybeleid zijn van toepassing op
  gegevens die via de API worden verstuurd, niet het beleid van DocSchoon
  zelf.

---

## Hoe je gegevens worden vervangen

Je kiest tussen twee weergaven:

- **Label tonen** — bijvoorbeeld `[NAAM]`, `[E-MAILADRES]`, `[BSN]`. Zo blijft
  zichtbaar *wat* er is weggehaald, zonder dat de oorspronkelijke waarde
  zichtbaar is.
- **Zwart maken** — de gevonden tekst wordt vervangen door blokjes (████) van
  dezelfde lengte.

In **beide gevallen** wordt de oorspronkelijke tekst uit het bestand
verwijderd en vervangen. De waarde is **niet terug te halen** uit het
gedownloade, schone bestand — er wordt niets "verborgen onder" een laag die
je kunt verwijderen, zoals soms bij zwart gelakte PDF's het geval is. De tekst
is er simpelweg niet meer.

> Let op: dit geldt voor het *uitvoerbestand*. Je oorspronkelijke,
> geüploade bestand blijft natuurlijk bestaan op je eigen computer zoals je
> het had opgeslagen.

---

## Welke taal kun je gebruiken?

DocSchoon ondersteunt **Nederlands** en **Engels**. De taalkeuze bepaalt:

- de labels waarmee gegevens worden vervangen (bijv. `[NAAM]` versus
  `[NAME]`);
- welke Nederlandse patronen actief zijn (BSN en postcode zijn
  Nederlandsspecifiek en blijven ook bij Engelse documenten beschikbaar,
  omdat een Nederlands BSN ook in een Engelstalig document kan voorkomen).

---

## Stap voor stap

1. Open [de app](index.html).
2. Sleep je document naar het uploadvak, of klik om te bladeren.
3. Kies hoe gegevens vervangen moeten worden (label of zwart maken) en de
   documenttaal.
4. Vink aan welke soorten gegevens je wilt verwijderen. Items met een
   sterretje (*) vereisen de optionele AI-detectie.
5. *(Optioneel)* Zet de AI-schakelaar aan en voer je Anthropic API-sleutel in
   als je ook namen, locaties, organisaties of datums wilt laten herkennen.
6. Klik op **Anonimiseer document**.
7. Bekijk het overzicht van gevonden en vervangen gegevens.
8. Download het schone bestand en **controleer het resultaat handmatig**
   voordat je het deelt of verstuurt.

---

## Beperkingen en juridische status

- **Geen 100% garantie.** Automatische detectie — met of zonder AI — mist
  altijd een deel van de gevallen, en kan soms ook onterecht iets markeren.
  Juist de gemiste gevallen vormen het risico.
- **Risico verkleind, niet weggenomen.** Het risico op herleiding is
  verkleind, maar het document kan nog steeds herleidbaar zijn tot een
  persoon op basis van de andere, niet-persoonsgegevens in de tekst
  (bijvoorbeeld een functietitel plus een afdeling plus een datum samen).
- **Geen ondersteuning voor gescande documenten of afbeeldingen.** Tekst die
  als afbeelding in een document staat, wordt niet herkend (daarvoor is OCR
  nodig, wat DocSchoon niet doet).
- **Geen officiële privacytool.** DocSchoon is niet getoetst of goedgekeurd
  door een toezichthoudende instantie. Gebruik het als hulpmiddel bij, niet
  als vervanging van, je eigen beoordeling van de AVG-status van een
  document.

---

## Privacy van DocSchoon zelf

- DocSchoon is een statische webpagina (HTML/JavaScript). Er is geen eigen
  server die je documenten ontvangt of opslaat.
- Bij gebruik **zonder** de AI-optie verlaat je document nooit je browser.
- Bij gebruik **met** de AI-optie wordt de tekst rechtstreeks van jouw browser
  naar Anthropic's API gestuurd, met jouw eigen API-sleutel. DocSchoon zelf
  ziet of bewaart die gegevens niet.

---

## Licentie

Open source ([MIT](LICENSE)). Gebruik, aanpassing en verspreiding zijn vrij
toegestaan. De tool wordt geleverd zonder garantie; de verantwoordelijkheid
voor correcte en rechtmatige verwerking van persoonsgegevens blijft bij de
gebruiker.
