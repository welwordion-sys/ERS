"""ERS-Zyklus memo_lockstep: Zustands-Memo + Knoten-Regime-1 gegen die
Skalierungswand. Phase 1 = PRE-CODE (prepare/import/ground/oblige/propose/
Falsifikatoren vorab). Phase 2 (Messung, Antwort, Commit) laeuft nach Bau+Sweep.
"""
import sys
sys.path.insert(0, '/home/claude/handover/ers')
import os
os.chdir('/home/claude/handover/ers')   # claims_registry.json der Session
from reason_setter import ReasonSetter

def must(cb, what):
    ok = getattr(cb, 'ok', cb)
    if not ok:
        raise SystemExit(f"REFUSED {what}: {getattr(cb, 'reason', '')}")
    return cb

s = ReasonSetter.prepare(
    ['Die Skalierungswand brechen ohne Vollstaendigkeitsverlust: Zustands-Memo '
     'ueber Suchpfade + Knoten-Regime-1-Kandidatenfilter (Svens Lockstep-Direktive), '
     'beide verlustfrei gegen sweep3 + Haertefaelle.',
     'Das ungeschnittene Regelpaar (14-15 Knoten) erneut messen: terminiert es jetzt?'],
    'memo_lockstep.json',
    note='PRE-CODE Phase. Beide Mechanismen muessen die Ergebnis-Menge exakt erhalten. '
         'Waechter: sweep3 (300 randomisiert + Familie) und die 7 Haertefaelle, die D6 fingen.')

cb = s.callbacks[-1] if hasattr(s, 'callbacks') else None
# prior_candidates werden von prepare in die Datei geschrieben; Sichtung unten im Log.

for f, pid in [('savings.json', 'g_wall'), ('savings.json', 'g_d6_dead'),
               ('chain.json', 'g_pos_monotone'), ('chain.json', 'g_neg_nonmonotone'),
               ('impl_s1.json', 'g_contract')]:
    s.import_prior_commit(f, pid)

must(s.ground([
 dict(id='g_directive', status='given', source='Sven, Sitzungsende 2026-07-19 (HANDOVER.md §5) + Bestaetigung 2026-07-20',
      statement='Svens Direktive: A und B im Lockstep wachsen; eine schon probierte a-b-Paarung '
                'nicht erneut probieren. Abgeleitet und bestaetigt zu bauen: (1) Zustands-Memo, '
                '(2) Kandidaten fuer a_node = B-Knoten, die mindestens eine Kante von a_node '
                'UEBERHAUPT IN B typkompatibel realisieren KOENNTEN (Quantor ueber ganz B).'),
 dict(id='g_code_state', status='given', source='enum_core2.py, Code-Lesung 2026-07-20',
      statement='expand(node_map, node_map_r, excluded) liest nur node_map, dessen Inverse und '
                'excluded plus konstante Globals (A_edges, b_set, a_idx, b_nodes). Frontier wird '
                'als Liste in Einfuegereihenfolge gesammelt, aber a_node = min(frontier) — die '
                'Auswahl ist ordnungsunabhaengig. Kandidaten = ALLE ungebundenen B-Knoten. '
                'Leaf-Ergebnisse gehen in ein dict (dedupliziert). Damit ist die von expand '
                'erzeugte LEAF-MENGE eine Funktion des Zustands (frozenset(node_map.items()), '
                'frozenset(excluded)) — der Suchbaum behandelt den Zustand aber als FOLGE: '
                'k gebundene Knoten koennen ueber bis zu k! Pfade denselben Zustand erreichen, '
                'jeder wird heute voll expandiert.'),
 dict(id='g_memo_spec', status='derived',
      derived_from=[dict(parents=['g_code_state', 'g_directive'], rule='Funktion des Zustands => Revisit-Skip aendert die Leaf-Menge nicht')],
      statement='Zustands-Memo: seen-Set ueber Schluessel (frozenset(node_map.items()), '
                'frozenset(excluded)); bei Revisit sofort return. Verlustfrei, WEIL die Expansion '
                'eine Funktion genau dieses Schluessels ist (g_code_state). KEIN D6-Risiko: D6 '
                'uebersprang SEEDS (fremde Suchbaeume), das Memo dedupliziert ZUSTAENDE innerhalb '
                'EINES Seed-Suchbaums.'),
 dict(id='g_r1_spec', status='derived',
      derived_from=[dict(parents=['g_directive', 'imported_g_contract'], rule='notwendige Bedingung + Vertrag: kantenlose Bindung liegt nie in der Seed-Komponente')],
      statement='Knoten-Regime-1: Signatur eines A-Knotens a = Menge (richtung, kind, typ) seiner '
                'inzidenten Kanten; Signatur eines B-Knotens b analog. Kandidat b fuer a nur wenn '
                'Schnitt nichtleer. Bindungsunabhaengig (Quantor ueber ganz B), also monoton. '
                'Verlustfrei unter dem Vertrag: ist der Schnitt leer, wird NIE eine Kante von a '
                'an b realisiert, a liegt in keinem Leaf in der Seed-Komponente; jedes Leaf des '
                'geschnittenen Teilbaums existiert identisch im unbedingten Ausschluss-Zweig '
                '(der b zudem freilaesst). SCHARF ZU TRENNEN vom widerlegten trial-29-Filter '
                '"realisiert JETZT eine Ankerkante" — der quantifizierte ueber den Bindungsstand.'),
]), 'ground_specs')

must(s.oblige({
 'o_lossless': 'Beide Mechanismen: kanonische Ergebnisgleichheit gegen enum_core2 auf sweep3 '
               '(300 randomisiert, Vertrag + Familie) UND den 7 Haertefaellen. Jede Abweichung = Verwerfung.',
 'o_not_d6': 'Das Memo ueberspringt niemals Seeds — nur Zustands-Revisits innerhalb eines Seed-Suchbaums.',
 'o_not_t29': 'R1 quantifiziert ausschliesslich ueber ganz B (Typ-Ebene), niemals ueber den aktuellen Bindungsstand.',
 'o_wall_measured': 'Das ungeschnittene 14-15-Knoten-Paar wird mit beiden Mechanismen erneut gemessen (Timeout-bewehrt), Ergebnis dokumentiert.',
}), 'oblige')

must(s.propose([
 dict(id='cand_break', statement='Memo + Knoten-R1 sind verlustfrei UND brechen die Wand (Paar terminiert in Minuten statt >25min).',
      discriminator='Gegen cand_insufficient: verlustfrei, aber die Zustandszahl selbst ist zu gross — Wand bleibt, Branch-and-Bound noetig. '
                    'Gegen cand_lossy: der Memo-Schluessel ist unvollstaendig (Expansion haengt an etwas ausserhalb (node_map, excluded)) oder R1 schneidet doch erreichbare Embeddings.'),
 dict(id='cand_insufficient', statement='Beide Mechanismen verlustfrei, aber das Paar terminiert weiterhin nicht — naechster Schritt Branch-and-Bound (Dominanz WAEHREND der Suche).',
      discriminator='Gegen cand_break.'),
 dict(id='cand_lossy', statement='Mindestens ein Mechanismus aendert die Ergebnismenge; wahrscheinlichste Stelle: Memo-Schluessel ignoriert einen versteckten Zustandsanteil.',
      discriminator='Gegen cand_break; Waechter sweep3+Haertefaelle muessen feuern.'),
]), 'propose')

must(s.check([
 dict(id='chk_memo_key', kind='falsifier', target='cand_break',
      method='Code-Lesung enum_core2.expand: existiert ein Input der Expansion ausserhalb '
             '(node_map, excluded) und der konstanten Globals? Kandidaten: Frontier-REIHENFOLGE, '
             'node_map_r, Rekursionskontext.',
      result='pass',
      outcome='Nein: frontier_nodes-Reihenfolge wird durch min() neutralisiert; node_map_r ist '
              'reine Inverse von node_map; kein weiterer Zustand. Leaf-Schreibungen sind '
              'idempotent (dict-Key). Der Schluessel (bindings, excluded) ist vollstaendig. '
              'RESTRISIKO an den Sweep delegiert (o_lossless).'),
 dict(id='chk_r1_nec', kind='falsifier', target='cand_break',
      method='Kann eine Bindung a->b mit leerem Signatur-Schnitt in irgendeinem Leaf zur '
             'Seed-Komponente beitragen? (Das war der Mechanismus, der trial-29 brach: spaetere '
             'Bindungen realisieren Kanten nachtraeglich.)',
      result='pass',
      outcome='Nein: nachtraegliche Realisierung einer Kante (a,x,k,y) an (b,bx) setzt voraus, '
              'dass B IRGENDEINE (richtung,k,y)-Kante an b hat — genau das schliesst der leere '
              'Schnitt aus, unabhaengig vom Bindungsstand. trial-29 scheiterte am Quantor '
              '(JETZT realisierbar); R1 quantifiziert ueber ganz B. RESTRISIKO an Sweep delegiert.'),
 dict(id='chk_wall', kind='falsifier', target='cand_break',
      method='Empirisch: das ungeschnittene Paar (bit_add_00_c1_* 15 Knoten/17 Kanten, '
             'addition_tree.json, repo welwordion-sys/perspective) mit Memo+R1 messen.',
      result='open',
      outcome='Offen bis Messung (Phase 2).'),
]), 'checks_precode')

s.save('memo_lockstep.json')
print('PHASE1 OK — Datei geschrieben, chk_wall offen bis Messung.')
