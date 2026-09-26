"""Reproduzierer fuer g_scan / g_legacy in decision_setter_v07.json.

Durchsucht alle Arbeitsdateien unter ERS/work_files (und optional weitere Ordner als
Argumente) nach Falsifikatoren, deren outcome nicht 'survived' ist, und zaehlt das
benutzte outcome-Vokabular je kind.

    python scan_failed_falsifiers.py [weitere_ordner ...]
"""
import collections
import glob
import json
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
ordner = [os.path.join(HIER, "..")] + sys.argv[1:]
dateien = [f for o in ordner for f in glob.glob(os.path.join(o, "**", "*.json"), recursive=True)
           if not f.endswith("claims_registry.json")]

vokabular = collections.Counter()
treffer = []
mit_checks = committed = 0
for f in dateien:
    try:
        b = json.load(open(f, encoding="utf-8"))
    except (ValueError, OSError):
        continue
    if not isinstance(b, dict) or "checks" not in b:
        continue
    mit_checks += 1
    com = b.get("committed")
    committed += bool(com)
    for k, c in b["checks"].items():
        o = c.get("outcome", "")
        vokabular[(c.get("kind"), o if len(o) <= 20 else "<Freitext>")] += 1
        if c.get("kind") == "falsifier" and o != "survived":
            auf_antwort = bool(com) and c.get("target") == com.get("answer")
            treffer.append((os.path.relpath(f, HIER), k, c.get("target"),
                            o if len(o) <= 20 else "<Freitext>", c.get("result", "")[:40],
                            "AUF COMMITTETER ANTWORT" if auf_antwort else "anderes Ziel"))

print(f"Dateien mit checks: {mit_checks}, davon committed: {committed}")
for (kind, o), n in sorted(vokabular.items(), key=lambda x: -x[1]):
    print(f"  {kind:12} {o:22} {n}")
print("\nFalsifikatoren mit outcome != survived:")
for t in treffer:
    print("  ", t)
print("\nauf committeter Antwort:", sum(t[-1] == "AUF COMMITTETER ANTWORT" for t in treffer))
