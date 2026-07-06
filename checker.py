#!/usr/bin/env python3
"""ERS claims-file checker.

Usage:
  python3 checker.py <claims.json>                 full check (exit 0 = clean)
  python3 checker.py <claims.json> --retract ID    simulate withdrawing an
        assumption/hypothesis: list every claim losing support, transitively.
        Read-only — reports impact, does not modify the file.
  python3 checker.py <claims.json> --explain ID    print the derivation tree
        for a claim: parents, rules, status, evidence class, hypothesis deps.

Mechanical checks only — no semantics:
  1. id uniqueness and referential integrity (derived_from.parents,
     hypothesis_deps, contradicts all point at existing ids)
  2. provenance completeness (status=derived requires derived_from;
     non-derived must NOT carry derived_from)
  3. hypothesis-dependency closure (a derived claim's hypothesis_deps
     must include the union of its parents' deps plus any parent that
     is itself assumed/hypothesis) — catches hypothesis contamination
  4. contradiction scan (both members of a contradicts pair accepted,
     i.e. given/derived, and not separated by disjoint hypotheses)
  5. reproducer discipline (evidence_class beyond 'none' requires a
     reproducer; 'UNREPRODUCED' is legal but counted and reported)
  6. cycle check over derived_from (a claim may not be its own ancestor)

Exit 0 = clean (UNREPRODUCED entries alone do not fail the check but
are listed). Exit 1 = violations found.
"""
import json, sys

def main(path):
    data = json.load(open(path))
    claims = data["claims"]
    by_id = {}
    errors, warnings = [], []

    for c in claims:
        if c["id"] in by_id:
            errors.append(f"duplicate id: {c['id']}")
        by_id[c["id"]] = c

    def exists(ref, owner, field):
        if ref not in by_id:
            errors.append(f"{owner}: {field} references unknown id '{ref}'")

    for c in claims:
        cid = c["id"]
        for ref in (c.get("derived_from", {}).get("parents") or []):
            exists(ref, cid, "derived_from")
        for ref in c.get("hypothesis_deps", []):
            exists(ref, cid, "hypothesis_deps")
            if ref in by_id and by_id[ref]["status"] not in ("assumed", "hypothesis"):
                errors.append(f"{cid}: hypothesis_deps entry '{ref}' has status "
                              f"{by_id[ref]['status']} (must be assumed/hypothesis)")
        for ref in c.get("contradicts", []):
            exists(ref, cid, "contradicts")

        if c["status"] == "derived" and "derived_from" not in c:
            errors.append(f"{cid}: derived without derived_from")
        if c["status"] != "derived" and "derived_from" in c:
            errors.append(f"{cid}: status={c['status']} but carries derived_from")
        if c.get("evidence_class", "none") != "none":
            rep = c.get("reproducer")
            if not rep:
                errors.append(f"{cid}: evidence_class={c['evidence_class']} "
                              f"without reproducer")
            elif rep == "UNREPRODUCED":
                warnings.append(f"{cid}: verdict is UNREPRODUCED "
                                f"({c['evidence_class']})")

    if errors:  # referential integrity gates the graph passes below
        report(errors, warnings); return 1

    # cycle check
    def ancestors(cid, seen):
        for p in (by_id[cid].get("derived_from", {}).get("parents") or []):
            if p == cid or p in seen:
                errors.append(f"{cid}: cyclic derivation via '{p}'"); return
            ancestors(p, seen | {p})
    for c in claims:
        ancestors(c["id"], set())

    # hypothesis closure
    def full_deps(cid):
        c = by_id[cid]
        deps = set(c.get("hypothesis_deps", []))
        for p in (c.get("derived_from", {}).get("parents") or []):
            if by_id[p]["status"] in ("assumed", "hypothesis"):
                deps.add(p)
            deps |= full_deps(p)
        return deps
    for c in claims:
        need = full_deps(c["id"])
        have = set(c.get("hypothesis_deps", []))
        missing = need - have
        if missing:
            errors.append(f"{c['id']}: hypothesis_deps missing inherited "
                          f"deps {sorted(missing)} — hypothesis contamination")

    # contradiction scan: both accepted and hypothesis sets not disjoint-branch
    for c in claims:
        for ref in c.get("contradicts", []):
            o = by_id[ref]
            if c["status"] in ("given", "derived") and o["status"] in ("given", "derived"):
                a, b = full_deps(c["id"]), full_deps(ref)
                if not (a - b) and not (b - a):  # same conditional footing
                    errors.append(f"CONTRADICTION live: {c['id']} vs {ref} "
                                  f"(same hypothesis footing) — walk provenance "
                                  f"to the guilty premise")
                else:
                    warnings.append(f"contradiction {c['id']} vs {ref} held apart "
                                    f"only by hypothesis branches {sorted(a ^ b)}")

    report(errors, warnings)
    return 1 if errors else 0

def load(path):
    data = json.load(open(path))
    return data["claims"], {c["id"]: c for c in data["claims"]}

def retract(path, rid):
    """Simulate withdrawing claim rid: which claims lose support?
    A claim loses support if rid is among its hypothesis_deps, its
    derivation parents, or (transitively) any ancestor is lost."""
    claims, by_id = load(path)
    if rid not in by_id:
        print(f"unknown id: {rid}"); return 1
    st = by_id[rid]["status"]
    if st not in ("assumed", "hypothesis"):
        print(f"note: {rid} has status={st}; retracting a given/derived claim "
              f"means the SOURCE was wrong — impact analysis is the same.")
    lost = {rid}
    changed = True
    while changed:               # propagate to fixpoint
        changed = False
        for c in claims:
            if c["id"] in lost: continue
            parents = set(c.get("derived_from", {}).get("parents") or [])
            deps    = set(c.get("hypothesis_deps", []))
            if (parents | deps) & lost:
                lost.add(c["id"]); changed = True
    lost.discard(rid)
    if not lost:
        print(f"retracting {rid}: no other claim depends on it")
    else:
        print(f"retracting {rid}: {len(lost)} claim(s) lose support:")
        for c in claims:         # file order, with the broken link named
            if c["id"] not in lost: continue
            parents = set(c.get("derived_from", {}).get("parents") or [])
            deps    = set(c.get("hypothesis_deps", []))
            via = sorted((parents | deps) & (lost | {rid}))
            print(f"  {c['id']} ({c['status']}) via {', '.join(via)}: "
                  f"{c['statement'][:70]}")
    return 0

def explain(path, cid, depth=0, seen=None):
    """Print the derivation tree for cid, root first."""
    claims, by_id = load(path) if seen is None else (None, seen[1])
    if seen is None:
        if cid not in by_id: print(f"unknown id: {cid}"); return 1
        seen = (set(), by_id)
    visited, by_id = seen
    c = by_id[cid]
    pad = "  " * depth
    ev = c.get("evidence_class", "none")
    hy = c.get("hypothesis_deps", [])
    line = f"{pad}{cid} [{c['status']}, evidence={ev}"
    if hy: line += f", conditional on {','.join(hy)}"
    line += f"] {c['statement'][:70]}"
    print(line)
    rep = c.get("reproducer")
    if rep: print(f"{pad}  reproducer: {rep[:90]}")
    if cid in visited:
        print(f"{pad}  (already expanded above)"); return 0
    visited.add(cid)
    df = c.get("derived_from")
    if df:
        print(f"{pad}  rule: {df['rule'][:90]}")
        for p in df["parents"]:
            explain(path, p, depth + 1, seen)
    return 0

def report(errors, warnings):
    for e in errors:   print("ERROR  ", e)
    for w in warnings: print("WARNING", w)
    if not errors and not warnings:
        print("clean")
    else:
        print(f"-- {len(errors)} error(s), {len(warnings)} warning(s)")

if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) == 3 and args[1] == "--retract":
        sys.exit(retract(args[0], args[2]))
    if len(args) == 3 and args[1] == "--explain":
        sys.exit(explain(args[0], args[2]))
    sys.exit(main(args[0]))
