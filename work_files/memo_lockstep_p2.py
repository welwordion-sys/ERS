"""ERS memo_lockstep Phase 2: Messungen, I8-Revision der k!-Praemisse,
Antwort, Commit."""
import sys
sys.path.insert(0, '/home/claude/handover/ers')
import os
os.chdir('/home/claude/handover/ers')
from reason_setter import ReasonSetter

def must(cb, what):
    ok = getattr(cb, 'ok', cb)
    if not ok:
        raise SystemExit(f"REFUSED {what}: {getattr(cb, 'reason', '')}")
    return cb

s, _stage = ReasonSetter.resume("memo_lockstep.json")

must(s.ground([
 dict(id='g_equiv_ok', status='given', source='Messung 2026-07-20: sweep4.py (sweep3 auf enum_core3), test_enum3.py, isolierter 300er-Lauf',
      statement='Verlustfreiheit VERIFIZIERT: beide Hebel zusammen 300/300 Vertrag + Familie PASS '
                '+ 7/7 Haertefaelle; isoliert je 300/300 gegen enum_core2 (memo only, r1 only). '
                'o_lossless, o_not_d6, o_not_t29 erfuellt (Memo skippt nur Zustands-Revisits, '
                'R1 nur Typ-Ebene ueber ganz B).'),
 dict(id='g_zero_revisits', status='given', source='Instrumentierter Lauf, Seed 1 des Wandpaars, PYTHONHASHSEED=0',
      statement='2.000.000 distinkte Zustaende in 25s, Revisit-Treffer <0.05% (Anzeige 0.0M). '
                'STRUKTURELLER GRUND, kein Sampling: a_node=min(frontier) ist eine Funktion des '
                'Zustands, also ist die Entscheidungsfolge jedes erreichbaren Zustands per Replay '
                'eindeutig rekonstruierbar — jeder Zustand hat genau EINEN erzeugenden Pfad. '
                'Der Suchbaum von enum_core2 IST bereits die zustandskanonische Aufzaehlung.'),
 dict(id='g_memo_revised', status='derived',
      derived_from=[dict(parents=['g_zero_revisits', 'g_code_state'], rule='eindeutiger Erzeugerpfad => keine Revisits => Memo trifft nie')],
      revises=dict(target='g_memo_spec',
                   prior_text='Verlustfrei, WEIL die Expansion eine Funktion genau dieses Schluessels ist (g_code_state). KEIN D6-Risiko: D6 uebersprang SEEDS (fremde Suchbaeume), das Memo dedupliziert ZUSTAENDE innerhalb EINES Seed-Suchbaums.',
                   why='Die Verlustfreiheit stand und steht; FALSCH war die implizite Nutzen-Praemisse aus g_directive/HANDOVER ("bis k! Wiederholungen desselben Zustands"): sie beschreibt eine Implementierung OHNE kanonische Knotenwahl. enum_core2 kanonisiert bereits per min(frontier).'),
      statement='Das Zustands-Memo ist verlustfrei, aber auf enum_core2 NUTZLOS (keine Revisits '
                'vorhanden) und auf Wandmaterial SCHAEDLICH: es speichert jeden distinkten Zustand '
                '(>12M, OOM/Kill nach ~25-90s), verwandelt die Zeitwand in eine Speicherwand. '
                'default kuenftig use_memo=False; Flag bleibt fuer Tests.'),
 dict(id='g_r1_weak', status='given', source='Signatur-Analyse Wandpaar',
      statement='Knoten-R1 auf echtem Material schwach: nur 2 Kantensignaturen (STRUCTURAL/'
                'OPERATIONAL, typ=None) => admissible-Groessen 5-14 von 15. Korrekt und gratis, '
                'zahlt aber erst bei Typ-Diversitaet — analog zum |Aut|=1-Befund fuer D3.'),
 dict(id='g_wall_stays', status='given', source='Messung: Paarlauf 300s-Budget gekillt; Einzelseed >90s/OOM',
      statement='WAND STEHT: bit_add_00_c1_cont_cont_2bit x cont_term_2bit terminiert nicht im '
                'Budget. Ursache PRAEZISIERT: nicht Pfad-Duplikation, sondern die KARDINALITAET '
                'der distinkten Zustaende selbst (~Verzweigung 10-13 hoch Tiefe 14, plus '
                'Ausschluss-Zweige). Vollenumeration injektiver Teilabbildungen skaliert nicht; '
                'noetig ist Schnitt WAEHREND der Suche (Dominanz/Branch-and-Bound, in savings.json '
                'als offen benannt) oder eine andere Zerlegung.'),
]), 'ground_measured')

must(s.check([
 dict(id='chk_wall_res', kind='falsifier', target='cand_break',
      method='chk_wall aufgeloest durch Messung (300s Paar-Budget, 90s Einzelseed, Zustandszaehlung).',
      result='pass',
      outcome='cand_break FALSIFIZIERT: verlustfrei ja, Wand gebrochen nein. Nebenbefund mit '
              'Disposition FILED (fliesst in den naechsten Designzyklus): Memo verschiebt die '
              'Wand von Zeit nach Speicher; R1-Schwaeche ist Materialeigenschaft (2 Signaturen).'),
 dict(id='chk_alt_head2head', kind='falsifier', target='cand_insufficient',
      method='Head-to-head gegen cand_lossy: haetten die Waechter gefeuert, waere lossy richtig. '
             'Gegen cand_break: Messung. Bleibt eine dritte Erklaerung (Messartefakt: nur 1 Seed, '
             'zu kleines Budget)?',
      result='pass',
      outcome='cand_lossy tot (alle Aequivalenztests gruen). Messartefakt ausgeschlossen: die '
              'Zustandszaehlung ist strukturell untermauert (Eindeutiger-Pfad-Argument) und der '
              'Zustandsraum ~11^14 liegt Groessenordnungen ueber jedem Budget. cand_insufficient '
              'ist die ueberlebende Erklaerung — in der NARROWED Form: nicht "Memo+R1 reichen '
              'nicht", sondern "das Duplikationsproblem, das Memo loesen sollte, existiert in '
              'enum_core2 gar nicht".'),
 dict(id='chk_rel_ml', kind='relevance', target='cand_insufficient',
      method='I9: beide Ziele adressiert?',
      result='pass',
      outcome='Ziel 1 (verlustfrei bauen): gebaut, verifiziert 300/300+300/300+300/300+7/7. '
              'Ziel 2 (Wand messen): gemessen, steht, Ursache praezisiert und von der falschen '
              'k!-Praemisse befreit (g_memo_revised).'),
]), 'checks_measured')

must(s.ground([
 dict(id='ans_ml', status='derived',
      derived_from=[dict(parents=['g_equiv_ok', 'g_memo_revised', 'g_r1_weak', 'g_wall_stays'],
                         rule='Verifikation + Falsifikation von cand_break => uebrig bleibt cand_insufficient in narrowed Form')],
      statement='Beide Direktive-Mechanismen sind gebaut und VERLUSTFREI (enum_core3.py, schaltbar; '
                'sweep4/test_enum3/isolierte Laeufe alle gruen). Die Wand brechen sie NICHT: '
                'enum_core2 kanonisiert die Suchreihenfolge bereits per min(frontier), es gibt '
                'strukturell null Zustands-Revisits — die k!-Duplikations-Praemisse der Direktive '
                'beschreibt diese Implementierung nicht. Das Memo ist daher nutzlos bis schaedlich '
                '(Speicherwand), R1 auf 2-Signatur-Material fast wirkungslos. Die Wand ist die '
                'Kardinalitaet der distinkten Zustaende; naechster Schritt ist der in savings.json '
                'offen benannte Branch-and-Bound-Entwurf (Dominanz WAEHREND der Suche) — eigener '
                'GATE-Zyklus, nicht hier entworfen.'),
]), 'ground_answer')

must(s.check([
 dict(id='chk_f_ans', kind='falsifier', target='ans_ml',
      method='Staerkster Angriff: "null Revisits" koennte am EINEN vermessenen Seed liegen; andere '
             'Seeds/Paare koennten revisit-reich sein und das Memo doch lohnen.',
      result='pass',
      outcome='Haelt nicht: das Eindeutiger-Pfad-Argument ist seed- und paarunabhaengig (es folgt '
              'allein aus a_node=min(frontier) als Zustandsfunktion). Revisits sind fuer JEDEN '
              'Lauf von enum_core2/3 exakt null moeglich... praeziser: der Replay rekonstruiert '
              'den Pfad eindeutig, also null Revisits, ueberall. Die Messung bestaetigt, das '
              'Argument traegt.'),
 dict(id='chk_r_ans', kind='relevance', target='ans_ml',
      method='I9: Evidenz->Ziele.',
      result='pass',
      outcome='g_equiv_ok deckt Ziel 1, g_wall_stays+g_memo_revised decken Ziel 2; die Revision '
              'ist mit Prior-Text dokumentiert (I8).'),
]), 'checks_answer')

must(s.commit('ans_ml', evidence_label='derived', assumptions_carried=[]), 'commit')
s.save('memo_lockstep.json')
print('COMMIT OK memo_lockstep.json')
