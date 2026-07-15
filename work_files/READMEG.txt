ERS work files — session 2026-07-15, grouping/serialization.

WICHTIG: grouping_memo_build.json enthaelt ans_core_dominates, einen Befund
der ZURUECKGEZOGEN wurde (find_core lief faelschlich im Dispatch-Pfad; die
gemessenen 0.04x waren ein Bau-Artefakt, kein Mechanismus-Beleg). Der Rueckzug
steht in tree_store_format.json als ans_retract. Einzeln gelesen ist
grouping_memo_build.json irrefuehrend — beide oder keins.

Reihenfolge der Entstehung:
  grouping_memo_build.json      ans_core_dominates  [ZURUECKGEZOGEN]
  tree_store_format.json        ans_format + ans_retract
  rule_delta_fix.json           ans_store (korrigiert ans_format)
  serialized_grouping_result.json  ans_win (1.33x, EIN sample)
  selfsimilarity.json           ans_ss (arbeitspunkt gemessen, richtung abgeleitet)
  determinism_fix.json          ans_det (fix UNVOLLSTAENDIG)

Alle evidence_label=assumed. Reproducer: grouping/bench_serialized.py,
grouping/tree_store.py.
