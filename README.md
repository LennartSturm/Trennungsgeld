# Trennungsgeldrechner

Dieses Projekt stellt einen leichtgewichtigen Rechner zur Verfügung, mit dem sich
der voraussichtliche Trennungsgeldanspruch auf Bundesebene nach
Bundesreisekostengesetz (BRKG) inklusive Reisekosten überschlägig ermitteln lässt.
Der Fokus liegt auf Transparenz und Nachvollziehbarkeit der Rechenschritte.

## Funktionsumfang

* Berechnung von Verpflegungsmehraufwand und Übernachtungskosten anhand der
  BRKG-Pauschalen (Stand 2024)
* Ermittlung erstattungsfähiger Reisekosten inkl. An- und Abreise,
  genehmigter Heimfahrten sowie täglicher Pendelfahrten
* Unterstützung von Kilometerpauschalen für Pkw, Motorrad und Fahrrad oder der
  Eingabe tatsächlicher Kosten
* Optionales Einlesen der Eingabedaten aus einer JSON-Datei
* Kommandozeilenwerkzeug `trennungsgeld`

## Annahmen

Das Bundesreisekostengesetz kennt zahlreiche Sonder- und Übergangsregelungen.
Der Rechner bildet die wichtigsten Standardfälle ab und trifft folgende Annahmen:

* Für die Verpflegungspauschalen gelten 28 EUR für volle 24-Stunden-Tage sowie
  14 EUR für An- bzw. Abreisetage und weitere Tage mit mehr als acht Stunden
  Abwesenheit.
* Übernachtungskosten können entweder als belegte Gesamtsumme angegeben werden
  oder – falls keine Belege vorliegen – über eine Pauschale von 20 EUR pro Nacht.
* Reisekosten werden standardmäßig über Kilometerpauschalen berechnet. Sofern
  tatsächliche Kosten angegeben werden, überschreiben sie die Pauschalen.
* Heimfahrten werden mit der Entfernung einer einfachen Strecke angesetzt.

Die getroffenen Annahmen orientieren sich an den bundeseinheitlichen Vorgaben.
Für Spezialfälle (z. B. Trennungsentschädigung nach längeren Abordnungen,
Mischformen mit Umzugskostenrecht oder landesspezifische Abweichungen) ist eine
manuelle Prüfung erforderlich.

## Installation

Das Projekt nutzt Python 3.11 oder neuer. Optional lässt sich ein virtuelles
Umfeld verwenden:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

Tests werden mit `pytest` ausgeführt:

```bash
pytest
```

## Nutzung

Nach der Installation steht der Befehl `trennungsgeld` zur Verfügung. Alternativ
kann das Modul direkt mit Python ausgeführt werden:

```bash
python -m trennungsgeld.cli --full-days 5 --arrival-days 2 --partial-days 3 \
  --overnight-receipts 4 --overnight-costs 320 --overnight-flat 2 \
  --vehicle car --initial-trip-km 500 --home-trips 3 --home-trip-km 400 \
  --commuting-days 10 --commuting-distance 15 --additional-costs 50
```

Die Ausgabe enthält eine übersichtliche Aufschlüsselung aller Teilbeträge.

### Eingabe über JSON

Eingaben können in einer JSON-Datei strukturiert werden. Beispiel `daten.json`:

```json
{
  "meal_allowance": {
    "full_days": 5,
    "arrival_departure_days": 2,
    "partial_days": 3,
    "overnight_stays_with_receipts": 4,
    "overnight_costs_total": 320,
    "overnight_stays_without_receipts": 2
  },
  "travel_costs": {
    "vehicle": "car",
    "initial_trip_distance_km": 500,
    "weekly_home_trips": 3,
    "home_trip_distance_km": 400,
    "commuting_days": 10,
    "commuting_distance_km": 15,
    "additional_costs": 50
  }
}
```

Aufruf:

```bash
python -m trennungsgeld.cli --input daten.json
```

## Lizenz

Veröffentlicht unter der MIT-Lizenz.
