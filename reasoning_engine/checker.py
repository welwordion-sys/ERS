"""
checker.py — part-3 v1 checker, SHAPE half only.

part3_question_generator v1_checker: "A question passes v1 if:
  (a) SHAPE - names a content-target, uses a recognized extraction-act,
      carries a traversal-link to a live intent;
  (b) TENDENCIES - satisfies drive-appropriate harvested criteria..."

We implement (a) ONLY. (b) inherits the carried 6/7-domain harvest assumption
(see question_taxonomy_coverage open_question) — building it now would build on
an unsettled sample. Excluded deliberately, not forgotten.

Each check returns an individual verdict so a failure names its own reason —
mirrors the 'each individually checkable' requirement in the spec.
"""

from __future__ import annotations
from dataclasses import dataclass
from library import Library, Role
from question import Question, ExtractionAct


@dataclass
class CheckResult:
    passed: bool
    reasons: list[str]  # one line per failed check; empty if passed

    @property
    def summary(self) -> str:
        return "PASS" if self.passed else "FAIL: " + "; ".join(self.reasons)


def check_shape(q: Question, lib: Library, live_intents: set[str]) -> CheckResult:
    reasons: list[str] = []

    # (a.1) content-target names a real role-slot that has material to aim at.
    # A vector pointing at an empty slot can't discriminate anything.
    if not isinstance(q.content_target, Role):
        reasons.append("content_target is not a Role")
    elif not lib.used_in_role(q.content_target):
        reasons.append(
            f"content_target {q.content_target.value} resolves to no concepts "
            f"in library (nothing used in that role yet)"
        )

    # (a.2) extraction-act is recognized.
    if not isinstance(q.extraction_act, ExtractionAct):
        reasons.append("extraction_act is not a recognized act")

    # (a.3) traversal-link points at a LIVE intent.
    if q.intent_link not in live_intents:
        reasons.append(
            f"intent_link {q.intent_link!r} is not a live intent"
        )

    return CheckResult(passed=not reasons, reasons=reasons)
