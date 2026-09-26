"""ERS-Gate fuer den Entwurf setter v0.7 — VOR dem Bau gelaufen (meta.workflow ers_enforcement:
Aenderung an einer stehenden Regel). Werkzeug: setter v0.6 (Verfahren-Kopie mit utf-8-Fix).

    python gate_setter_v07.py      # schreibt decision_setter_v07.json neben diese Datei

Reproduzierer der Givens: ../../test_befunde.py gegen v0.6 (Ausgabe ../../befunde_v06_output.txt),
Arbeitsdatei-Scan: scan_failed_falsifiers.py (neben dieser Datei).
"""
import json
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.environ.get("ERS_GATE_TOOL", r"D:\Projects\verfahren\ers"))
from reason_setter import ReasonSetter  # noqa: E402

PFAD = os.path.join(HIER, "decision_setter_v07.json")
REG = os.path.join(HIER, "..", "claims_registry.json")


def zeige(schritt, cb):
    print(f"[{schritt}] ok={cb.ok} {cb.reason}")
    for w in cb.warnings:
        print("   warn:", w)
    if not cb.ok:
        print("   repair:", cb.repair)
        sys.exit(1)


s = ReasonSetter.prepare(
    ["Welche Aenderungen an reason_setter v0.6 sind fuer v0.7 lizenziert, insbesondere: "
     "verweigert I4 einen Commit, dessen Falsifikator gegen die Antwort gescheitert ist (D)?"],
    PFAD, note="Sitzung 2026-09-26, Befunde A-M aus test_befunde.py", registry_path=REG)
print("prior_candidates:", len(s._prior_candidates))

zeige("ground", s.ground([
    {"id": "g_repro", "status": "given", "statement":
        "test_befunde.py gegen v0.6: A,B,C,D,F,G,H,I,M,T scheitern mit der jeweils benannten Luecke; "
        "E und H-Altfall zusaetzlich ueber die Standard-Registry bestaetigt (reuse abgeleitet -> I2-"
        "Verweigerung; doppelte reg_id -> still der ERSTE Eintrag). Ausgabe befunde_v06_output.txt."},
    {"id": "g_crit", "status": "given", "statement":
        "KB ers.setter_substrate_design_v0_3.hard_invariants_criterion: harte Invarianten muessen "
        "Wahrheitsbedingungen sein - keine legitime Episode darf sie verletzen; alles mit legitimem "
        "Gegenbeispiel bleibt beratend."},
    {"id": "g_scan", "status": "given", "statement":
        "Scan von 52 Arbeitsdateien (ERS/work_files + Verfahren): genau eine committete Antwort mit "
        "gescheitertem Falsifikator, serialized_grouping_result.json k_mech -> ans_win. Dessen Ergebnis "
        "sagt, die Antwort sei nach der Widerlegung umgeschrieben worden; die widerlegte These steht "
        "als eigener Anspruch prior_multiply. Der Check traf also eine fruehere Fassung."},
    {"id": "g_legacy", "status": "given", "statement":
        "Altdateien nutzen outcome-Werte survived, failed, branch_traced, satisfied sowie in drei "
        "Dateien (memo_lockstep, neighbor_lockstep, table_reassembly) vertauschte Felder mit "
        "result in {pass, fail, open}; 'Offen bis Messung' ging als durchgefuehrter Check durch."},
    {"id": "g_callers", "status": "given", "statement":
        "Verfahren-Aufrufer: ablauf.abschluss liest das Label aus der Reparatur per Regex "
        "use evidence_label='(\\w+)', setzt outcome aus 'ausgang' (Vorgabe survived), nutzt die "
        "kinds falsifier und relevance; kein Aufrufer uebergibt negation_handling an ground()."},
    {"id": "g_openitem", "status": "given", "statement":
        "KB ers.setter_substrate_design_v0_3.open_items[0]: 'negation-handled detection: how does "
        "setter verify branched status is genuine vs asserted' - im Code v0.6 gar nicht, der Aufrufer "
        "kann den Status direkt setzen (Befund A)."},
    {"id": "a_noleg", "status": "assumed", "statement":
        "Keine legitime Episode muss eine Antwort committen, gegen deren AKTUELLE Fassung ein "
        "Falsifikator gescheitert ist, ohne diesen Fehlschlag sichtbar zu behandeln."},
    {"id": "a_impl", "status": "assumed", "statement":
        "Die Implementierung wird der hier committeten Regel entsprechen; belegt erst durch "
        "test_befunde.py (D, D2, M, R und die uebrigen) gegen v0.7 nach dem Bau."},
]))

zeige("oblige", s.oblige({
    "o_legacy": "Alle Arbeitsdateien in ERS/work_files laden weiter per run()/resume().",
    "o_verfahren": "ablauf.abschluss committet weiter; lauf.py im Verfahren bleibt ALLES GRUEN.",
    "o_scan_case": "Die serialized_grouping-Episode hat unter der Regel eine legale, genauere Buchung.",
    "o_flawed_falsifier": "Eine Episode mit selbst fehlerhaftem Falsifikator kann committen - sichtbar.",
}))

zeige("propose", s.propose([
    {"id": "cand_plain", "statement":
        "I4 verweigert jeden Commit, gegen dessen Antwort-id ein Falsifikator mit outcome failed steht.",
     "discriminator": "id-gebunden, keine Rueckzugsmoeglichkeit"},
    {"id": "cand_warn", "statement":
        "Commit bleibt erlaubt; ein gescheiterter Falsifikator gegen die Antwort erzeugt nur eine Warnung.",
     "discriminator": "beratend statt hart"},
    {"id": "cand_versioned", "statement":
        "I4 verlangt >=1 ueberlebten Falsifikator gegen die AKTUELLE Fassung der Antwort und verweigert, "
        "solange ein gescheiterter Falsifikator gegen diese Fassung nicht per retract_check(id, grund) "
        "zurueckgezogen ist; Rueckzuege stehen im Commit-Block. Checks binden an den Aussagetext zum "
        "Pruefzeitpunkt; Check-ids sind nur anhaengbar.",
     "discriminator": "fassungsgebunden, sichtbarer Rueckzug"},
]))

zeige("check", s.check([
    {"id": "k_plain", "kind": "falsifier", "target": "cand_plain",
     "method": "o_flawed_falsifier: Episode 'Falsifikator selbst fehlerhaft (falscher Build gemessen), "
               "Antwort richtig' gegen die Regel durchgespielt.",
     "result": "Unter cand_plain bleibt der gescheiterte Check fuer immer an der id; die richtige Antwort "
               "ist nie committbar, ausser man vergibt eine neue id und umgeht damit die Regel. Legitime "
               "Episode blockiert -> nach g_crit keine Wahrheitsbedingung.",
     "outcome": "failed"},
    {"id": "k_warn", "kind": "falsifier", "target": "cand_warn",
     "method": "o_scan_case: serialized_grouping-Buchung unter cand_warn nachgespielt.",
     "result": "Die Fehlbuchung (failed gegen ans_win statt gegen prior_multiply) committet mit einer "
               "Warnung, die niemand lesen muss; die genauere Buchung wird nicht erzwungen. Dieselbe "
               "Form wie session6_review: der Gate fing es, es ging trotzdem durch.",
     "outcome": "failed"},
    {"id": "k_vers", "kind": "falsifier", "target": "cand_versioned",
     "method": "Drei Episoden gegen den Regeltext: (1) serialized_grouping, (2) fehlerhafter Falsifikator, "
               "(3) Umschreiben derselben id nach Widerlegung; plus Umgehung durch Ueberschreiben der "
               "Check-id (Befund M).",
     "result": "(1) legal genauer buchbar: failed gegen prior_multiply oder gegen die alte Fassung, "
               "survived gegen die neue. (2) retract_check mit Grund -> committbar, Rueckzug im Block "
               "sichtbar. (3) revises mit woertlichem prior_text aendert die Fassung, alter Fehlschlag "
               "zaehlt nicht fuer die neue, neuer Falsifikator noetig. Ueberschreiben der id wird durch "
               "Nur-Anhaengen verweigert. Haelt - Bau muss es bestaetigen (a_impl).",
     "outcome": "survived",
     "side_findings": [{"finding": "Befund M: check() ueberschreibt eine bestehende Check-id still; "
                                   "damit waere jede Outcome-Regel umgehbar.",
                        "disposition": "fixed"}]},
    {"id": "k_neg_noleg", "kind": "negation", "target": "a_noleg",
     "method": "Negation verfolgt: gibt es eine legitime Episode, die gegen einen gescheiterten "
               "Falsifikator auf der aktuellen Fassung committen MUSS?",
     "result": "Ja - der fehlerhafte Falsifikator. Die Negation kippt die einfache Regel (cand_plain) und "
               "verlangt den sichtbaren Rueckzug; unter cand_versioned ist der Fall abgedeckt, weil der "
               "Fehlschlag behandelt (zurueckgezogen) statt verborgen wird. Polaritaet der Antwort kippt "
               "damit nicht, sie wird eingegrenzt.",
     "outcome": "branch_traced"},
    {"id": "k_obl_legacy", "kind": "obligation", "target": "cand_versioned",
     "method": "o_legacy: Regeltext gegen die Ladefunktionen.",
     "result": "Neue Felder (target_statement am Check, retracted am Check) haben Vorgaben; Altdateien "
               "ohne sie laden. Pruefung des outcome-Vokabulars nur in check(), nicht beim Laden.",
     "outcome": "survived"},
    {"id": "k_obl_verf", "kind": "obligation", "target": "cand_versioned",
     "method": "o_verfahren: ablauf.abschluss gegen den Regeltext.",
     "result": "abschluss grounded die Antwort, prueft sie danach mit ausgang=survived und kind "
               "relevance/survived; der Reparaturtext fuer das Label bleibt woertlich. Bestaetigung "
               "durch lauf.py nach dem Tausch der Setterkopie.",
     "outcome": "survived"},
    {"id": "k_rel", "kind": "relevance", "target": "cand_versioned",
     "method": "Bezug auf das Ziel",
     "result": "Das Ziel fragt nach lizenzierten Aenderungen und nach D. cand_versioned beantwortet D "
               "(verweigern, mit sichtbarem Rueckzug) und nennt die Aenderungen, die D erst wirksam "
               "machen (Fassungsbindung, Nur-Anhaengen, Vokabular); die uebrigen Befunde stuetzen sich "
               "auf g_repro.",
     "outcome": "survived"},
]))

zeige("carry", s.carry("a_impl", "Kippt, falls test_befunde.py gegen v0.7 nicht vollstaendig PASS ist "
                                  "- dann gilt die Antwort nur fuer den Entwurf, nicht fuer den Code."))

zeige("ground-ans", s.ground([
    {"id": "ans", "status": "derived", "statement":
        "v0.7 ist lizenziert mit: (1) I4 fassungsgebunden - >=1 ueberlebter Falsifikator gegen die "
        "aktuelle Fassung, kein ungezogener gescheiterter gegen sie; Rueckzug nur per retract_check(id, "
        "grund), im Commit-Block gelistet. (2) Checks tragen den Aussagetext zum Pruefzeitpunkt; Check-ids "
        "nur anhaengbar (M). (3) kind/outcome geschlossenes Vokabular, 'satisfied' als Alias (I). (4) "
        "ground() nimmt kein negation_handling vom Aufrufer (A). (5) Aendern der Aussage einer bestehenden "
        "id verlangt revises mit woertlichem prior_text (B, I8). (6) I3 und I9 zaehlen nur ueberlebte "
        "Checks (C). (7) import/reuse holen die Elternhuelle (E, F). (8) reg_ids je Commit eindeutig, "
        "Altdubletten verweigert statt still aufgeloest, reuse achtet registry_path (H, K). (9) utf-8 "
        "ueberall (G). Unveraendert: der Reparaturtext fuer evidence_label.",
     "derived_from": [{"parents": ["g_repro", "g_crit", "g_scan", "g_legacy", "g_callers", "g_openitem",
                                   "a_noleg", "a_impl"],
                       "rule": "cand_versioned ueberlebte den Falsifikator, cand_plain und cand_warn "
                               "scheiterten; Einzelposten folgen den Reproduzierern"}]}]))

zeige("check-ans", s.check([
    {"id": "k_ans_f", "kind": "falsifier", "target": "ans",
     "method": "Ist die Antwort mehr als cand_versioned plus Einzelposten - schmuggelt sie etwas ein?",
     "result": "Punkte 3-9 sind je an einen reproduzierten Befund gebunden; Punkt 1-2 ist cand_versioned "
               "woertlich. Keine Aenderung ohne Befund, keine Aenderung am Reparaturtext.",
     "outcome": "survived"},
    {"id": "k_ans_rel", "kind": "relevance", "target": "ans",
     "method": "Bezug auf das Ziel", "result": "Beantwortet D und listet die lizenzierten Aenderungen.",
     "outcome": "survived"},
]))

cb = s.commit("ans", "assumed", ["a_noleg", "a_impl"], registry_path=REG)
zeige("commit", cb)
print(json.dumps(s.committed, ensure_ascii=False, indent=1))
print("stage:", s.save(PFAD))
