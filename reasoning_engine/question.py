"""
question.py — the currency of part 3.

part3_question_generator: "A question is a TRAVEL-VECTOR in modelling space:
  direction  = content-target (which four-role slot it aims at)
  rendering  = extraction-act (open/closed/probing/gap-implying; swappable)
  selection  = traversal-order (priority over open vectors)"

insertability: every question also carries an answer CONTRACT (C1..C6) — the
typed shape the answer must fill. Off-contract prose has nowhere to land.

An Intent is the thing a question serves. part3_split_v2: the intent layer is
distinct currency from the question layer. Here we model intent minimally — a
question must LINK to a live intent, and the checker verifies that link exists.
"""

from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from library import Role


class ExtractionAct(Enum):
    OPEN = "open"
    CLOSED = "closed"
    PROBING = "probing"
    GAP_IMPLYING = "gap-implying"
    CHECKLIST = "checklist"


class Contract(Enum):
    # from insertability node contract_types
    C1_CONCEPT_LIST = "C1"     # list of {concept, relation_to_target}
    C2_METHOD_LIST = "C2"      # list of {method, preconditions, subtasks, effects}
    C3_BINARY = "C3"           # {answer: yes/no, discriminating_evidence}
    C4_ORDERING = "C4"         # ranked node-refs + {dimension}, mints an Attribute
    C5_BINDING = "C5"          # {concept} single fill for one open slot
    C6_DIFFERENCE_LIST = "C6"  # list of {difference, blocking: yes/no}


@dataclass(frozen=True)
class Intent:
    """A live intent the question serves. Untyped seed (achieve/know/do) — we
    don't model the goal-tree yet, just its existence as a link target."""
    iid: str
    description: str


@dataclass(frozen=True)
class Question:
    """A travel-vector. Direction / rendering / selection + answer contract."""
    qid: str
    content_target: Role        # DIRECTION: which role-slot it aims at
    extraction_act: ExtractionAct  # RENDERING
    intent_link: str            # SELECTION anchor: id of a live intent it serves
    contract: Contract          # answer shape (insertability)
    template: str = ""          # human-readable render (optional here)
