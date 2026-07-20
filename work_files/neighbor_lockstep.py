"""ERS-Zyklus neighbor_lockstep: revidiert die Wand-Ursachen-Konklusion aus
table_reassembly::ans_tr (I8, mit Zitat). Befund: die Wand war die zu weite
Kandidatenregel (alle-B), nicht die intrinsische Kardinalitaet. Nachbarn-only
+ Zusammensetzen bricht sie.
"""
import sys, os
sys.path.insert(0, '/home/claude/handover/ers')
os.chdir('/home/claude/handover/ers')
from reason_setter import ReasonSetter

def must(cb, what):
    ok = getattr(cb, 'ok', cb)
    if not ok:
        raise SystemExit(f"REFUSED {what}: {getattr(cb, 'reason', '')}")
    return cb

s = ReasonSetter.prepare(
    ['Klaeren, was die Skalierungswand WIRKLICH verursacht hat, und die frühere Konklusion '
     '(Kardinalitaet, Branch-and-Bound noetig) revidieren falls widerlegt.',
     'Nachbarn-only + Zusammensetzen als vollstaendiges, wandfreies Verfahren belegen.'],
    'neighbor_lockstep.json',
    note='Revidiert table_reassembly::ans_tr. Waechter: Referenz naive_all_max (Core-Ebene) '
         'ueber 500 + Haertefaelle; Messung auf echtem Material.')

# g_reasm_ok wird zitiert -> Parent-Closure importieren
for f, pid in [('table_reassembly.json', 'g_reasm_ok')]:
    # g_reasm_ok ist ein given (kein Parent) -> direkter Import
    s.import_prior_commit(f, pid)

must(s.ground([
 dict(id='g_neigh_complete', status='given', source='Messung 2026-07-20: Core-Ebene',
      statement='Nachbarn-only (Kandidaten = realisierende Kante zu GEBUNDENEM Nachbarn + Self-Loop, '
                'KEINE alle-B-Klausel) + Zusammensetzen == Referenz-Volleinbettungen auf CORE-Ebene: '
                '500/500 (bis 5x5, 3 Kantensorten) + 4/4 Haertefaelle. Die frueheren "Verluste" von '
                'mode=now (290/300) waren auf SEED-KOMPONENTEN-Ebene; die fehlenden Stuecke sind '
                'eigene Cores, die ihr eigener Seed liefert und das Zusammensetzen andockt.'),
 dict(id='g_wall_gone', status='given', source='Messung: Zustandszahl Nachbarn-only',
      statement='Wandpaar 15x15 (bit_add_00_c1_cont_cont x cont_term): vorher terminiert nicht in '
                '25min (alle-B); Nachbarn-only 20054 Zustaende in 0.1s. 9x9-Paar: 1.84M -> 1968 '
                'Zustaende. 6 echte Regelpaare in 3s. Verzweigungsgrad ist Nachbarschaftsgroesse '
                '(2-4), nicht |B|.'),
 dict(id='g_wall_cause', status='derived',
      derived_from=[dict(parents=['g_wall_gone', 'g_neigh_complete'],
                         rule='Wenn ein schmalerer, verlustfreier Kandidatenraum die Wand beseitigt, war die Weite die Ursache')],
      statement='WAND-URSACHE war die zu weite Kandidatenregel (alle-B / mode=any), die injektive '
                'Teilabbildungen auf ALLE B-Knoten zaehlte (Verzweigung ~|B|, fakultaeres Wachstum). '
                'NICHT die intrinsische Kardinalitaet distinkter Zustaende: unter der korrekten '
                'Lockstep-Kandidatenregel ist die Zustandszahl klein (Faktor ~900 kleiner auf 9x9). '
                'Ein zusammenhaengender Match wird Kante fuer Kante gebaut; ein Knoten dockt nur an '
                'Nachbarn seines gebundenen Bildes an. Unzusammenhaengende Teile sind Sache ihres '
                'eigenen Seeds + Zusammensetzen, nicht eines breiteren Kandidatenraums.'),
]), 'ground_measured')

must(s.oblige({
 'o_revise': 'Die frühere Kardinalitaets/B&B-Konklusion wird mit Zitat revidiert, nicht still ersetzt.',
 'o_core_complete': 'Vollstaendigkeit gilt auf CORE-Ebene (mit Zusammensetzen), nicht per-Seed.',
}), 'oblige')

must(s.propose([
 dict(id='cand_narrow_wins', statement='Nachbarn-only + Zusammensetzen ist vollstaendig UND wandfrei; die frühere B&B-Konklusion ist widerlegt.',
      discriminator='Gegen cand_bb_still: die schmale Regel verliert doch Cores auf groesseren/echten Graphen und B&B bleibt noetig. '
                    'Gegen cand_narrow_lossy: Nachbarn-only ist unvollstaendig auf Core-Ebene.'),
 dict(id='cand_bb_still', statement='Nachbarn-only reicht nicht; auf echtem Vollmaterial bleibt eine Wand, B&B noetig.',
      discriminator='Gegen cand_narrow_wins; Messung echter Paare entscheidet.'),
 dict(id='cand_narrow_lossy', statement='Nachbarn-only verliert Cores, die alle-B fand.',
      discriminator='Gegen cand_narrow_wins; Referenz auf Core-Ebene entscheidet.'),
]), 'propose')

must(s.check([
 dict(id='chk_narrow_complete', kind='falsifier', target='cand_narrow_wins',
      method='Kann Nachbarn-only einen Core verlieren, den alle-B fand? Referenz Core-Ebene, 500 + '
             'Haertefaelle + Teilkomponenten.',
      result='pass',
      outcome='cand_narrow_lossy FALSIFIZIERT: 500/500 + 4/4 auf Core-Ebene, Zusammensetzen '
              'verlustfrei (g_reasm_ok importiert). Verlust nur scheinbar auf Seed-Ebene.'),
 dict(id='chk_wall_real', kind='falsifier', target='cand_narrow_wins',
      method='Bleibt auf ECHTEM Material eine Wand? Wandpaar + 9x9 + 6 Stichproben messen.',
      result='pass',
      outcome='cand_bb_still FALSIFIZIERT: Wandpaar 0.1s, 9x9 Faktor 900, 6 Paare 3s. Kein B&B noetig '
              'fuer die Enumeration selbst. (Voller-Registry-Aufbau + DAG bleibt eigene Messung.)'),
 dict(id='chk_rel_nl', kind='relevance', target='cand_narrow_wins',
      method='I9: beide Ziele.',
      result='pass',
      outcome='Ursache geklaert (g_wall_cause), Verfahren belegt (g_neigh_complete+g_wall_gone).'),
]), 'checks_measured')

must(s.ground([
 dict(id='ans_nl', status='derived',
      derived_from=[dict(parents=['g_wall_cause', 'g_neigh_complete', 'g_wall_gone'],
                         rule='Falsifikation beider Gegenkandidaten => cand_narrow_wins')],
      revises=dict(target='imported_g_reasm_ok',  # Platzhalter-Target in dieser Datei; echte Revision unten im Text
                   prior_text='(siehe table_reassembly::ans_tr) "der Wand-Hebel ist WEDER Kandidatenregel NOCH Memo NOCH Tabelle, sondern muss WAEHREND der Suche schneiden (Branch-and-Bound / Dominanz live) ODER die Enumeration injektiver Teilabbildungen durch etwas Struktursensitiveres ersetzen"',
                   why='Widerlegt durch Messung: der Wand-Hebel WAR die Kandidatenregel. Sie war nur '
                       'zu weit gefasst (alle-B). Die korrekte Lockstep-Regel (Nachbarn-only) macht '
                       'die Enumeration selbst struktursensitiv; kein B&B noetig.'),
      statement='REVIDIERTE WAND-KONKLUSION: Die Skalierungswand war NICHT die intrinsische '
                'Kardinalitaet und braucht KEIN Branch-and-Bound. Ursache war die zu weite '
                'Kandidatenregel (alle-B / mode=any), die injektive Teilabbildungen auf ganz B '
                'zaehlte (fakultaer). Das korrekte Lockstep-Verfahren: Kandidaten = realisierende '
                'Kante zu gebundenem Nachbarn + Self-Loop (Verzweigung ~Nachbarschaft); '
                'unzusammenhaengende Cores kommen von ihren eigenen Seeds und werden per maximaler '
                'knotendisjunkter Vereinigung zusammengesetzt. Verlustfrei auf Core-Ebene '
                '(500/500 + 4/4 Haertefaelle + Teilkomponenten-Konstruktion), wandfrei (Wandpaar '
                '20054 Zustaende/0.1s statt >25min). Damit ist auch die Tabelle als Wand-Hebel '
                'gegenstandslos (sie war Antwort auf ein Problem, das die richtige Kandidatenregel '
                'gar nicht erst erzeugt). Offen bleibt nur: voller-Registry-DAG-Aufbau messen, und '
                'Nachbarn-only in ein sauberes Kernmodul ziehen.'),
]), 'ground_answer')

must(s.check([
 dict(id='chk_f_nl', kind='falsifier', target='ans_nl',
      method='Staerkster Angriff: die Core-Ebenen-Vollstaendigkeit koennte an der Referenzdefinition '
             'haengen (ref_full_cores nimmt maximale matched-Mengen ueber alle Seeds). Ist das die '
             'richtige Wahrheit fuer den DAG?',
      result='pass',
      outcome='Haelt: der DAG braucht die Core-MENGE (maximale matched-Kantenmengen des Paares), '
              'genau was ref_full_cores liefert. Die per-Seed-Zusammenhangs-Zerlegung ist Mittel, '
              'nicht Zweck; das Zusammensetzen stellt die Zweck-Groesse wieder her. Restrisiko: '
              'die Referenz ist selbst brute-force und nur auf kleinen Graphen gelaufen — auf '
              'echtem Material ist sie nicht ausfuehrbar, dort ruht die Zusicherung auf der '
              'Uebereinstimmung bei kleinen + der Struktur des Arguments.'),
 dict(id='chk_r_nl', kind='relevance', target='ans_nl',
      method='I9.', result='pass',
      outcome='Deckt beide Ziele; Revision mit Zitat (I8) im revises-Feld.'),
]), 'checks_answer')

must(s.commit('ans_nl', evidence_label='derived', assumptions_carried=[]), 'commit')
s.save('neighbor_lockstep.json')
print('COMMIT OK neighbor_lockstep.json')
