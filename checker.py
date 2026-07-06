#!/usr/bin/env python3
"""ERS claims-file checker. Usage: python3 checker.py <claims.json>

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

def report(errors, warnings):
    for e in errors:   print("ERROR  ", e)
    for w in warnings: print("WARNING", w)
    if not errors and not warnings:
        print("clean")
    else:
        print(f"-- {len(errors)} error(s), {len(warnings)} warning(s)")

if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
