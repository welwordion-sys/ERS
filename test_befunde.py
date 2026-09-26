"""Befund-Reproduzierer fuer den Setter (Pruefung 2026-09-26, v0.6 -> v0.7).

Jeder Test beschreibt das RICHTIGE Verhalten. Gegen v0.6 laufen gelassen, zeigt ein
FAIL, dass der Befund real ist; gegen v0.7 muss alles PASS sein. Damit ist dieselbe
Datei Reproduzierer (vorher) und Regressionstest (nachher).

    python test_befunde.py            # alle Befunde, Exit 0 nur wenn alle PASS

Befunde:
  A  ground() nimmt negation_handling vom Aufrufer an  -> I5 umgehbar
  B  Neu-Grounden derselben id ersetzt die Aussage ohne revises -> I8 umgehbar
  C  assumed->given nach einem GESCHEITERTEN Check      -> I3 umgehbar
  D  Commit trotz gescheitertem Falsifikator gegen die aktuelle Antwort
  E  reuse() eines abgeleiteten Anspruchs scheitert (I2)
  F  import_prior_commit() eines abgeleiteten Anspruchs scheitert (I1)
  G  save() stuerzt unter Windows bei Nicht-ASCII ab (cp1252)
  H  reg_id kollidiert bei wiederholtem Commit auf denselben Pfad; reuse nimmt den ERSTEN
  I  outcome/kind werden nicht geprueft (vertauschte Felder, freies Vokabular)
  K  reuse() ignoriert registry_path
  T  test_setter.py Fall A wird von I9 verweigert statt von I4/I5 (Test prueft nicht, was er sagt)
  L  Kompatibilitaet: Altdateien laden, Verfahren-Regex auf die Label-Reparatur greift
"""
import contextlib
import glob
import io
import json
import os
import re
import sys
import tempfile
import traceback

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
from reason_setter import ReasonSetter  # noqa: E402

TMP = tempfile.mkdtemp(prefix="ers_befunde_")
REG = os.path.join(TMP, "claims_registry.json")


def _fals(s, tgt, outcome="survived", kid=None):
    return s.check([{"id": kid or f"f_{tgt}_{outcome}_{len(s.checks)}", "kind": "falsifier",
                     "target": tgt, "method": "m", "result": "r", "outcome": outcome}])


def _rel(s, tgt):
    return s.check([{"id": f"rel_{tgt}_{len(s.checks)}", "kind": "relevance", "target": tgt,
                     "method": "m", "result": "bears on goal", "outcome": "survived"}])


def _committed_file(name, claims, answer):
    """Ein committetes Arbeitsfile mit einem abgeleiteten Anspruch und seinen Eltern."""
    p = os.path.join(TMP, name)
    s = ReasonSetter.prepare("goal widget " + name, p, registry_path=REG)
    assert s.ground(claims).ok
    _fals(s, answer)
    _rel(s, answer)
    cb = s.commit(answer, "derived", [], registry_path=REG)
    assert cb.ok, cb.reason
    s.save(p)
    return p, s


# ---------------------------------------------------------------- A
def test_A_negation_handling_from_caller():
    s = ReasonSetter("A")
    cb = s.ground([{"id": "a1", "statement": "x", "status": "assumed",
                    "negation_handling": "checked"}])
    assert not cb.ok, "Aufrufer darf negation_handling nicht selbst setzen"
    assert "I5" in cb.reason


# ---------------------------------------------------------------- B
def test_B_same_id_rewrite_needs_revises():
    s = ReasonSetter("B")
    assert s.ground([{"id": "c1", "statement": "original", "status": "given"}]).ok
    assert s.ground([{"id": "c1", "statement": "original", "status": "given"}]).ok, \
        "identisches Wiederholen bleibt erlaubt"
    cb = s.ground([{"id": "c1", "statement": "anders", "status": "given"}])
    assert not cb.ok and "I8" in cb.reason, "stilles Umschreiben muss verweigert werden"
    cb = s.ground([{"id": "c1", "statement": "anders", "status": "given",
                    "revises": {"target": "c1", "prior_text": "original", "why": "w"}}])
    assert cb.ok, cb.reason
    cb = s.ground([{"id": "c1", "statement": "dritte", "status": "given",
                    "revises": {"target": "c1", "prior_text": "falsch zitiert", "why": "w"}}])
    assert not cb.ok and "I8" in cb.reason, "prior_text muss woertlich stimmen"


# ---------------------------------------------------------------- C
def test_C_promotion_needs_survived_check():
    s = ReasonSetter("C")
    s.ground([{"id": "a1", "statement": "x", "status": "assumed"}])
    _fals(s, "a1", "failed")
    cb = s.ground([{"id": "a1", "statement": "x", "status": "given"}])
    assert not cb.ok and "I3" in cb.reason, "ein gescheiterter Check lizenziert keine Befoerderung"
    _fals(s, "a1", "survived")
    assert s.ground([{"id": "a1", "statement": "x", "status": "given"}]).ok


# ---------------------------------------------------------------- D
def test_D_failed_falsifier_blocks_commit():
    s = ReasonSetter("D")
    s.ground([{"id": "ans", "statement": "answer", "status": "given"}])
    _fals(s, "ans", "failed")
    _rel(s, "ans")
    cb = s.commit("ans", "derived", [])
    assert not cb.ok and "I4" in cb.reason, "nur gescheiterter Falsifikator -> verweigern"
    _fals(s, "ans", "survived")
    cb = s.commit("ans", "derived", [])
    assert not cb.ok and "I4" in cb.reason, "gescheitert UND ueberlebt gegen dieselbe Fassung -> verweigern"


def test_D_revision_after_refutation_is_legal():
    s = ReasonSetter("D2")
    s.ground([{"id": "ans", "statement": "old thesis", "status": "given"}])
    _fals(s, "ans", "failed")
    cb = s.ground([{"id": "ans", "statement": "corrected thesis", "status": "given",
                    "revises": {"target": "ans", "prior_text": "old thesis",
                                "why": "falsifier refuted the old version"}}])
    assert cb.ok, cb.reason
    _rel(s, "ans")
    cb = s.commit("ans", "derived", [])
    assert not cb.ok and "I4" in cb.reason, \
        "der Falsifikator gegen die ALTE Fassung zaehlt nicht fuer die neue"
    _fals(s, "ans", "survived")
    cb = s.commit("ans", "derived", [])
    assert cb.ok, cb.reason


def test_M_check_ids_are_append_only():
    s = ReasonSetter("M")
    s.ground([{"id": "ans", "statement": "a", "status": "given"}])
    _fals(s, "ans", "failed", kid="k1")
    cb = _fals(s, "ans", "survived", kid="k1")
    assert not cb.ok, "ein Check darf nicht unter derselben id ueberschrieben werden"
    assert s.checks["k1"].outcome == "failed"


def test_R_flawed_falsifier_can_be_retracted_visibly():
    s = ReasonSetter("R")
    s.ground([{"id": "ans", "statement": "a", "status": "given"}])
    _fals(s, "ans", "failed", kid="k_bad")
    _fals(s, "ans", "survived", kid="k_good")
    _rel(s, "ans")
    assert not s.commit("ans", "derived", []).ok
    assert not s.retract_check("k_bad", "").ok, "Rueckzug ohne Grund ist Verschweigen"
    assert s.retract_check("k_bad", "Messung lief gegen den falschen Build (Beleg: Hash abc)").ok
    cb = s.commit("ans", "derived", [])
    assert cb.ok, cb.reason
    assert s.committed["retracted_checks"] == {"k_bad": "Messung lief gegen den falschen Build (Beleg: Hash abc)"}


# ---------------------------------------------------------------- E / F
_DERIVED = [{"id": "g1", "statement": "widget base", "status": "given"},
            {"id": "a1", "statement": "widget assumption", "status": "assumed"},
            {"id": "d1", "statement": "widget derived", "status": "derived",
             "derived_from": [{"parents": ["g1"], "rule": "r"}]}]


def test_F_import_prior_commit_derived():
    p, _ = _committed_file("f_src.json", _DERIVED[:1] + _DERIVED[2:], "d1")
    s = ReasonSetter("F")
    lid = s.import_prior_commit(p, "d1")
    assert s.claims[lid].status == "derived"
    parents = s.claims[lid].derived_from[0]["parents"]
    assert all(q in s.claims for q in parents), "Eltern muessen mitkommen"
    assert s.claims[parents[0]].status == "given"


def test_E_reuse_derived():
    p, _ = _committed_file("e_src.json", _DERIVED[:1] + _DERIVED[2:], "d1")
    reg = json.load(open(REG, encoding="utf-8"))
    rid = next(e["reg_id"] for e in reg if e["source_path"] == p and e["claim_id"] == "d1")
    s = ReasonSetter("E")
    lid = s.reuse(rid, registry_path=REG)
    assert s.claims[lid].status == "derived"
    assert all(q in s.claims for q in s.claims[lid].derived_from[0]["parents"])


# ---------------------------------------------------------------- G
def test_G_non_ascii_save_roundtrip():
    p = os.path.join(TMP, "g.json")
    s = ReasonSetter("Ziel → mit Pfeil ≥ und Umlaut ä")
    s.ground([{"id": "c", "statement": "Aussage — mit Strich → Pfeil", "status": "given"}])
    s.save(p)
    s2, stage = ReasonSetter.run(p)
    assert s2.claims["c"].statement == "Aussage — mit Strich → Pfeil"


# ---------------------------------------------------------------- H
def test_H_reg_ids_unique_across_commits():
    p = os.path.join(TMP, "h.json")
    for text in ("first answer", "second answer"):
        s = ReasonSetter.prepare("goal h", p, registry_path=REG)
        s.ground([{"id": "ans", "statement": text, "status": "given"}])
        _fals(s, "ans"); _rel(s, "ans")
        assert s.commit("ans", "derived", [], registry_path=REG).ok
        s.save(p)
    reg = json.load(open(REG, encoding="utf-8"))
    ids = [e["reg_id"] for e in reg if e["source_path"] == p]
    assert len(ids) == 2 and len(set(ids)) == 2, f"reg_ids kollidieren: {ids}"


def test_H_legacy_duplicate_reg_id_is_not_silently_resolved():
    reg = os.path.join(TMP, "legacy_reg.json")
    json.dump([{"reg_id": "x.json::ans", "claim_id": "ans", "statement": "OLD", "status": "given",
                "negation_handling": None, "derived_from": None, "source_path": "x.json", "goals": []},
               {"reg_id": "x.json::ans", "claim_id": "ans", "statement": "NEW", "status": "given",
                "negation_handling": None, "derived_from": None, "source_path": "x.json", "goals": []}],
              open(reg, "w", encoding="utf-8"))
    s = ReasonSetter("H2")
    try:
        lid = s.reuse("x.json::ans", registry_path=reg)
    except ValueError as e:
        assert "ambig" in str(e).lower() or "mehrdeutig" in str(e).lower(), str(e)
        return
    raise AssertionError(f"mehrdeutige reg_id still aufgeloest zu {s.claims[lid].statement!r}")


# ---------------------------------------------------------------- I
def test_I_outcome_vocabulary():
    s = ReasonSetter("I")
    s.ground([{"id": "ans", "statement": "a", "status": "given"}])
    swapped = s.check([{"id": "k", "kind": "falsifier", "target": "ans", "method": "m",
                        "result": "pass", "outcome": "Nein: haelt, weil ..."}])
    assert not swapped.ok, "vertauschte result/outcome-Felder muessen auffallen"
    bad_kind = s.check([{"id": "k2", "kind": "falsfier", "target": "ans", "method": "m",
                         "result": "r", "outcome": "survived"}])
    assert not bad_kind.ok, "Tippfehler im kind muss auffallen"
    alias = s.check([{"id": "k3", "kind": "relevance", "target": "ans", "method": "m",
                      "result": "r", "outcome": "satisfied"}])
    assert alias.ok and s.checks["k3"].outcome == "survived", "'satisfied' ist Alias fuer survived"


# ---------------------------------------------------------------- K
def test_K_reuse_honours_registry_path():
    p, _ = _committed_file("k_src.json", [{"id": "g1", "statement": "kval", "status": "given"}], "g1")
    reg = json.load(open(REG, encoding="utf-8"))
    rid = next(e["reg_id"] for e in reg if e["source_path"] == p)
    s = ReasonSetter("K")
    lid = s.reuse(rid, registry_path=REG)
    assert s.claims[lid].statement == "kval"


# ---------------------------------------------------------------- T
def test_T_smoke_test_checks_what_it_claims():
    import test_setter
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        test_setter.case_a_false_commit()
    text = out.getvalue()
    a1 = re.search(r"A1 refused.*", text).group(0)
    a2 = re.search(r"A2 refused.*", text).group(0)
    assert "(I4)" in a1, f"A1 soll an I4 scheitern, nicht: {a1}"
    assert "(I5)" in a2, f"A2 soll an I5 scheitern, nicht: {a2}"


# ---------------------------------------------------------------- L
def test_L_legacy_work_files_still_load():
    n = 0
    for f in glob.glob(os.path.join(HIER, "work_files", "**", "*.json"), recursive=True):
        blob = json.load(open(f, encoding="utf-8"))
        if not (isinstance(blob, dict) and "stage" in blob and "goals" in blob):
            continue
        ReasonSetter.run(f)
        n += 1
    assert n > 0


def test_L_verfahren_label_repair_regex():
    s = ReasonSetter("L")
    s.ground([{"id": "ans", "statement": "a", "status": "given"}])
    _fals(s, "ans"); _rel(s, "ans")
    cb = s.commit("ans", "measured", [])
    assert not cb.ok
    m = re.search(r"use evidence_label='(\w+)'", cb.repair or "")
    assert m and m.group(1) == "derived", cb.repair


if __name__ == "__main__":
    # commits without prepare() fall back to ./claims_registry.json - keep them out of the repo
    os.chdir(TMP)
    tests = [(k, v) for k, v in sorted(globals().items()) if k.startswith("test_")]
    fails = 0
    for name, fn in tests:
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                fn()
            print(f"PASS  {name}")
        except Exception as e:
            fails += 1
            msg = (str(e) or type(e).__name__).splitlines()[0][:150]
            print(f"FAIL  {name}: {type(e).__name__}: {msg}")
    print(f"\n{len(tests) - fails}/{len(tests)} PASS   (tmp: {TMP})")
    sys.exit(1 if fails else 0)
