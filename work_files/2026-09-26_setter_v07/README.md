# 2026-09-26 — setter v0.7 design gate

| Datei | Inhalt |
|---|---|
| `gate_setter_v07.py` | Das ERS-Gate, **vor** dem Bau gelaufen, mit setter v0.6 (Verfahren-Kopie mit utf-8-Fix). Erzeugt `decision_setter_v07.json`. |
| `decision_setter_v07.json` | Committet, Antwort `ans`, Label `assumed`, getragen `a_noleg` (verzweigt) und `a_impl` (getragen, unerforscht). |
| `scan_failed_falsifiers.py` | Reproduzierer fuer `g_scan` / `g_legacy`. |

Reproduzierer der uebrigen Givens: `../../test_befunde.py` (gegen v0.6: 2/15 PASS, gegen v0.7:
17/17 PASS), Ausgabe gegen v0.6 in `../../befunde_v06_output.txt`.

## Nach dem Bau

**`a_impl` entlastet**: `python test_befunde.py` gegen v0.7 → 17/17 PASS, `python test_setter.py`
→ alle Faelle scheitern jetzt an der Invariante, die sie pruefen (I4, I5, I3). Die Arbeitsdatei selbst
ist eingefroren und fuehrt `a_impl` weiter als getragen; diese Zeile ist die Entlastung.

**Korrektur an `g_scan`** (Wortlaut, nicht Substanz): „Scan von 52 Arbeitsdateien" zaehlte alle
gelesenen JSON-Dateien. Dateien mit Checks: 50 (51 mit dieser Gate-Datei). Die Aussage „genau eine
committete Antwort mit gescheitertem Falsifikator" steht; drei weitere Treffer des Scans sind die
Dateien mit vertauschten Feldern, deren Falsifikatoren in der Sache bestanden.

## Reihenfolge, ehrlich

Die tragende Wende — vom einfachen Verweigern zum fassungsgebundenen Verweigern mit sichtbarem
Rueckzug — entstand in meiner Ueberlegung unmittelbar vor dem Schreiben des Gates (Episode
„fehlerhafter Falsifikator"). Die Datei haelt die widerlegten Alternativen fest, beweist aber die
Reihenfolge nicht (LF2). Commit-Verweigerungen: 0.
