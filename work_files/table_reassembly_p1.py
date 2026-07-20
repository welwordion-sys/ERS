"""ERS-Zyklus table_reassembly, Phase 1 (PRE-CODE).
Zwei Entwuerfe: (1) Cross-Seed-Tabelle (settled-Teilbindungen ueber Seeds
teilen), (2) Zusammensetzen unzusammenhaengender Cores. Falsifikatoren
VORAB — insbesondere die D6-Abgrenzung (D6 uebersprang Seeds, widerlegt).
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
    ['Cross-Seed-Tabelle: identische Teilbindungen, die mehrere Seeds erreichen, nur einmal '
     'expandieren — verlustfrei gegen die tabellenlose Vollenumeration, und messbar gegen die Wand.',
     'Zusammensetzen: aus den per-Seed zusammenhaengenden Komponenten die maximalen '
     '(ggf. unzusammenhaengenden) Cores rekonstruieren, verlustfrei gegen die Brute-Force-Referenz.'],
    'table_reassembly.json',
    note='PRE-CODE. Kandidatenregel mode=any ist NUR ein Minimumfilter (notwendig, nicht '
         'entscheidend); Korrektheit ruht auf der Blatt-_matched-Berechnung. Waechter: '
         'Referenz naive_all_max unter Vertrag (300) + 7 Haertefaelle.')

for f, pid in [('savings.json', 'g_d6_dead'), ('savings.json', 'g_wall'),
               ('chain.json', 'g_pos_monotone'), ('impl_s1.json', 'g_contract'),
               ('memo_lockstep.json', 'g_zero_revisits')]:
    s.import_prior_commit(f, pid)

must(s.ground([
 dict(id='g_cand_complete', status='given', source='Messung 2026-07-20: mode=any 300/300 gegen Referenz',
      statement='Vollstaendige Kandidatenregel steht: b ist Kandidat fuer a, wenn IRGENDEINE Kante '
                'von a (Self-Loop b->b(k,y); Kante zu gebundenem Nachbarn realisiert JETZT; Kante zu '
                'ungebundenem Nachbarn ueber Typ-Existenz (k,y) in B) an b andocken kann. Minimumfilter '
                '(notwendig); Match wird am Blatt via _matched entschieden. mode=now (ohne '
                'ungebundene-Nachbar-Kante) verliert 10/300.'),
 dict(id='g_cand_weak', status='given', source='Messung Wandpaar: mode=any 1 Seed >3M/OOM',
      statement='Auf echtem Material (2 Kantensorten STRUCTURAL/OPERATIONAL, Typ None) kollabiert '
                'mode=any Richtung "alle B" — der Filter schneidet nichts, die Wand steht voll. '
                'Der schneidende Hebel muss die Tabelle sein, nicht die Kandidatenregel.'),
 dict(id='g_table_spec', status='derived',
      derived_from=[dict(parents=['imported_g_zero_revisits', 'imported_g_pos_monotone'],
                         rule='Innerhalb EINES Seeds sind Zustaende revisit-frei (min-Frontier); '
                              'ZWISCHEN Seeds kann dieselbe Teilbindung wiederkehren')],
      statement='Tabelle = Cross-Seed-Memo ueber ZUSTAENDE (frozenset(node_map.items()), '
                'frozenset(excluded)), geteilt ueber die aeussere Seed-Schleife. Wert = die von '
                'diesem Zustand erzeugte Menge maximaler Seed-Komponenten. Innerhalb eines Seeds '
                'nutzlos (revisit-frei, memo_lockstep); der Nutzen ist REIN cross-seed: Seed S2 '
                'trifft einen Zustand, den S1 schon voll expandiert hat, und uebernimmt dessen '
                'Ergebnis statt neu zu expandieren.'),
 dict(id='g_not_d6', status='derived',
      derived_from=[dict(parents=['imported_g_d6_dead', 'g_table_spec'], rule='Abgrenzung per Objekt-Ebene')],
      statement='SCHARFE D6-ABGRENZUNG: D6 uebersprang ganze SEEDS (fremde Suchbaeume) auf Basis '
                '"war irgendwo gebunden" — widerlegt (8/150), weil ein Seed-Suchbaum MEHR enthaelt '
                'als die Embeddings mit diesem Paar. Die Tabelle ueberspringt keine Seeds und keine '
                'Suchbaeume, sondern dedupliziert IDENTISCHE ZUSTAENDE (exakt gleiche node_map UND '
                'excluded). Die Expansion ist eine Funktion genau dieses Zustands (memo_lockstep '
                'chk_memo_key), also ist die Uebernahme verlustfrei — unabhaengig davon, welcher '
                'Seed den Zustand zuerst erreichte.'),
 dict(id='g_reasm_spec', status='derived',
      derived_from=[dict(parents=['imported_g_contract', 'imported_g_pos_monotone'],
                         rule='Vertrag liefert Seed-Komponenten; Vereinigung disjunkter Komponenten ist Konsumenten-Ableitung')],
      statement='Zusammensetzen = Konsumenten-Schritt. Zwei zusammenhaengende Komponenten C1 '
                '(A-Knoten S1, B-Knoten T1) und C2 (S2,T2) KOEXISTIEREN in einem Embedding gdw '
                'S1∩S2=∅ UND T1∩T2=∅ (Injektivitaet beidseitig); sonst KONKURRIEREN sie. Maximale '
                'Cores = maximale knotendisjunkte Vereinigungen von Komponenten. OFFENES RISIKO '
                '(vorab benannt): eine maximale disjunkte Vereinigung koennte eine NICHT-maximale '
                'Teilkomponente brauchen (C1_gross konkurriert mit C2, aber C1_klein∪C2 hat mehr '
                'Kanten) — dann reicht die Vereinigung MAXIMALER Komponenten nicht. Muss gegen die '
                'Referenz getestet werden, nicht angenommen.'),
]), 'ground_specs')

must(s.oblige({
 'o_table_lossless': 'Tabelle: kanonische Core-Gleichheit mit/ohne Tabelle auf sweep + Haertefaellen.',
 'o_table_notd6': 'Tabelle dedupliziert nur identische (node_map, excluded)-Zustaende; ueberspringt nie Seeds.',
 'o_table_cuts': 'Tabelle auf dem Wandpaar messen: sinkt die Arbeit gegen tabellenlos messbar?',
 'o_reasm_lossless': 'Zusammensetzen: rekonstruierte maximale Cores == Referenz-Volleinbettungen (300 + Haertefaelle).',
 'o_reasm_subcomp': 'Das Teilkomponenten-Risiko wird explizit getestet, nicht wegangenommen.',
}), 'oblige')

must(s.propose([
 dict(id='cand_both_ok', statement='Tabelle verlustfrei + schneidet cross-seed; Zusammensetzen via maximaler disjunkter Vereinigung verlustfrei.',
      discriminator='Gegen cand_table_inert: die Tabelle trifft cross-seed kaum (Zustaende seed-spezifisch), Wand bleibt. '
                    'Gegen cand_reasm_gap: das Teilkomponenten-Risiko realisiert sich — maximale Vereinigung verliert Cores.'),
 dict(id='cand_table_inert', statement='Die Cross-Seed-Treffer sind selten (Zustaende tragen den Seed implizit ueber die Bindung), Tabelle bringt wenig gegen die Wand.',
      discriminator='Gegen cand_both_ok; messbar an der Trefferquote.'),
 dict(id='cand_reasm_gap', statement='Vereinigung MAXIMALER Komponenten ist unvollstaendig; es braucht auch Teilkomponenten fuer manche maximale disjunkte Cores.',
      discriminator='Gegen cand_both_ok; der Referenzvergleich feuert.'),
]), 'propose')

must(s.check([
 dict(id='chk_notd6', kind='falsifier', target='cand_both_ok',
      method='Kann die Tabelle einen Core verlieren wie D6? D6 verlor, weil es einen SEED uebersprang, '
             'dessen Baum anders schneidet. Tut die Tabelle das?',
      result='pass',
      outcome='Nein: die Tabelle ueberspringt keinen Seed und keinen Ast, sie liefert fuer einen '
              'IDENTISCHEN Zustand dasselbe Ergebnis, das die Expansion ohnehin (deterministisch, '
              'als Zustandsfunktion) erzeugt haette. Der uebernehmende Seed setzt die Expansion mit '
              'demselben Ergebnis fort. RESTRISIKO (Ergebnis haengt doch am Seed) an o_table_lossless delegiert.'),
 dict(id='chk_reasm_pre', kind='falsifier', target='cand_both_ok',
      method='Konstruiere den Teilkomponenten-Fall vorab: C1_gross konkurriert mit C2 (teilen einen '
             'B-Knoten), aber C1_klein (Submap) ist disjunkt und C1_klein∪C2 hat mehr Kanten als beide '
             'einzeln. Liefert die per-Seed-Enumeration C1_klein ueberhaupt (Dominanzfilter entfernt es)?',
      result='open',
      outcome='Offen bis Test. Hypothese: der Dominanzfilter entfernt C1_klein innerhalb des Seeds, '
              'also fehlt es dem Zusammensetzen — dann ist die maximale Vereinigung unvollstaendig und '
              'cand_reasm_gap trifft. Gegenhypothese: unter dem Vertrag sind alle relevanten '
              'Komponenten als eigene maximale Seed-Komponenten praesent. Wird gemessen (o_reasm_subcomp).'),
]), 'checks_precode')

s.save('table_reassembly.json')
print('PHASE1 OK — table_reassembly.json, chk_reasm_pre offen bis Test.')
