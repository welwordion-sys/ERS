"""ERS table_reassembly Phase 2: Messungen, Antwort, Commit."""
import sys, os
sys.path.insert(0, '/home/claude/handover/ers')
os.chdir('/home/claude/handover/ers')
from reason_setter import ReasonSetter

def must(cb, what):
    ok = getattr(cb, 'ok', cb)
    if not ok:
        raise SystemExit(f"REFUSED {what}: {getattr(cb, 'reason', '')}")
    return cb

s, _ = ReasonSetter.resume('table_reassembly.json')

must(s.ground([
 dict(id='g_reasm_ok', status='given', source='Messung 2026-07-20: pair_table.reassemble gegen ref_full_cores',
      statement='Zusammensetzen VERIFIZIERT verlustfrei: maximale knotendisjunkte Vereinigung der '
                'Seed-Komponenten == Referenz-Volleinbettungen, 300/300 + gezielt konstruierte '
                'Teilkomponenten-Falle (C1_gross konkurriert um B-Knoten, C1_klein disjunkt) PASS. '
                'chk_reasm_pre aufgeloest: das Teilkomponenten-Risiko realisiert sich NICHT — unter '
                'dem Vertrag sind die noetigen Teilkomponenten als eigene maximale Seed-Komponenten '
                'praesent, weil jeder ihrer Knoten als eigener Seed auftritt.'),
 dict(id='g_table_key_bug', status='given', source='Messung: erste Tabellenversion 285/300, Diagnose + Fix 300/300',
      statement='FALLE gefunden und behoben: den Vertragsschnitt (_seed_comp_leaf) in den gecachten '
                'WERT zu legen macht ihn seed-relativ — ein anderer Seed, der denselben (node_map, '
                'excluded)-Zustand erreicht, schneidet die Komponente ANDERS und bekam faelschlich '
                'die des Erstsehers (15/300 Verluste). Fix: den ROHEN Blatt-node_map cachen '
                '(seed-invariant), den Vertragsschnitt erst beim Auslesen PRO SEED anwenden. Danach '
                '300/300 verlustfrei. Gleiche Fehlerklasse wie D6 (seed-relatives Ergebnis geteilt), '
                'eine Ebene subtiler.'),
 dict(id='g_table_inert', status='given', source='Messung: 14.7% Cross-Seed-Zustaende (Zufallsgraphen) vs echtes 9x9-Paar',
      statement='Tabelle verlustfrei, aber gegen die Wand WIRKUNGSLOS. Auf Zufallsgraphen teilen '
                '14.7% der Zustaende mehr als einen seed_a; auf echten Regeln (add_init 9x9, fast '
                'identische Spine-Ketten) speichert die Tabelle 1.84M Rohzustaende und ist LANGSAMER '
                '(35s vs 26s ohne) — nicht genug Treffer, um die Speicherkosten hereinzuholen. '
                'cand_table_inert bestaetigt: die Wand ist die KARDINALITAET distinkter Zustaende, '
                'nicht ihre Wiederholung; ein Memo kann nichts gegen echte Vielfalt.'),
 dict(id='g_cand_min', status='given', source='Sven-Praezisierung + Konsistenz mit _matched',
      statement='Die Kandidatenregel mode=any ist ein MINIMUMFILTER (notwendige Bedingung), nie eine '
                'Entscheidung — Natur des Subgraph-Matchings. Sie ueber-generiert; der Match wird am '
                'Blatt via _matched bestimmt, Dominanz putzt. Korrektheit ruht auf der Blattberechnung. '
                'Konsequenz: auf 2-Sorten-Material schneidet sie nichts (g_cand_weak), das ist '
                'erwartungskonform, kein Fehler.'),
]), 'ground_measured')

must(s.check([
 dict(id='chk_reasm_res', kind='falsifier', target='cand_reasm_gap',
      method='chk_reasm_pre aufgeloest: konstruierte Teilkomponenten-Falle + 300 Zufall.',
      result='pass',
      outcome='cand_reasm_gap FALSIFIZIERT: die maximale disjunkte Vereinigung ist vollstaendig. '
              'Grund (dispose FIXED): der Vertrag stellt jede benoetigte Teilkomponente als eigene '
              'maximale Seed-Komponente bereit (jeder Knoten ist ein Seed).'),
 dict(id='chk_table_res', kind='falsifier', target='cand_both_ok',
      method='Tabelle gegen tabellenlos, verlustfrei UND schneidend?',
      result='fail',
      outcome='cand_both_ok FALSIFIZIERT im schneidenden Teil: Tabelle verlustfrei (nach Key-Fix), '
              'aber inert gegen die Wand (g_table_inert). Ueberlebt: cand_table_inert. Disposition '
              'FILED: Tabelle bleibt als korrekter Baustein (nuetzt bei hoher Cross-Seed-Redundanz), '
              'ist aber nicht der Wand-Hebel.'),
 dict(id='chk_rel_tr', kind='relevance', target='cand_table_inert',
      method='I9: beide Ziele adressiert?',
      result='pass',
      outcome='Ziel 1 (Tabelle verlustfrei + Wand messen): gebaut, verlustfrei 300/300, gemessen — '
              'inert. Ziel 2 (Zusammensetzen verlustfrei): gebaut, verifiziert 300/300 + Konstruktion.'),
]), 'checks_measured')

must(s.ground([
 dict(id='ans_tr', status='derived',
      derived_from=[dict(parents=['g_reasm_ok', 'g_table_key_bug', 'g_table_inert', 'g_cand_min'],
                         rule='Verifikation Zusammensetzen + Falsifikation des schneidenden Tabellenteils => uebrig cand_table_inert')],
      statement='Zwei verlustfreie Bausteine stehen, einer davon lueckenlos verifiziert, keiner '
                'bricht die Wand. (1) ZUSAMMENSETZEN: maximale knotendisjunkte Vereinigung der '
                'Seed-Komponenten rekonstruiert exakt die Referenz-Volleinbettungen (300/300 + '
                'Teilkomponenten-Konstruktion); Koexistenz = beidseitige Knotendisjunktheit, '
                'Konkurrenz = geteilter A- oder B-Knoten. Das ist der Konsumenten-Schritt aus dem '
                'Vertrag, jetzt konkret und getestet. (2) CROSS-SEED-TABELLE: verlustfrei NUR wenn '
                'der rohe Blatt-node_map gecacht und der Vertragsschnitt pro Seed beim Auslesen '
                'angewandt wird (den Schnitt in den Wert zu legen ist ein D6-artiger seed-relativer '
                'Fehler, 15/300); aber gegen die Wand inert, weil diese die Kardinalitaet distinkter '
                'Zustaende ist (echtes 9x9-Paar: 1.84M Zustaende, Tabelle langsamer). Die '
                'Kandidatenregel mode=any ist ein Minimumfilter und schneidet auf 2-Sorten-Material '
                'ebenfalls nichts. FAZIT: der Wand-Hebel ist WEDER Kandidatenregel NOCH Memo NOCH '
                'Tabelle, sondern muss WAEHREND der Suche schneiden (Branch-and-Bound / Dominanz '
                'live, savings.json offen) ODER die Enumeration injektiver Teilabbildungen durch '
                'etwas Struktursensitiveres ersetzen. Naechster GATE-Zyklus.'),
]), 'ground_answer')

must(s.check([
 dict(id='chk_f_tr', kind='falsifier', target='ans_tr',
      method='Staerkster Angriff: die Tabelle koennte auf ANDEREN Paaren (hohe Symmetrie/Redundanz) '
             'doch schneiden — "inert" waere dann uebergeneralisiert.',
      result='pass',
      outcome='Eingegrenzt statt widerlegt: die Aussage ist NICHT "Tabelle nuetzt nie", sondern '
              '"Tabelle nuetzt nicht gegen DIESE Wand (Kardinalitaet, nicht Redundanz)". Bei echter '
              'Cross-Seed-Redundanz (viele Automorphismen) kann sie zahlen — dann aber zahlt auch '
              'D3/Symmetrie-Kollaps, und das Material zeigt |Aut|=1 (auto_filter). Auf DIESEM '
              'Material inert; die schwaechere, attributierte Form haelt.'),
 dict(id='chk_r_tr', kind='relevance', target='ans_tr',
      method='I9: Evidenz->Ziele.',
      result='pass',
      outcome='g_reasm_ok deckt Ziel 2, g_table_inert+g_table_key_bug decken Ziel 1; der '
              'Wand-Ausblick benennt den naechsten Zyklus (kein stiller Rest).'),
]), 'checks_answer')

must(s.commit('ans_tr', evidence_label='derived', assumptions_carried=[]), 'commit')
s.save('table_reassembly.json')
print('COMMIT OK table_reassembly.json')
