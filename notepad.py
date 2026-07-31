"""
notepad.py — Konzept-Relations-Notizblock, v0-Prototyp.

WIRING STATUS: eigenstaendig lauffaehig (`python3 notepad.py` fuehrt die Demo aus).
Haengt an world_model.py (AtMostOneOf, Origin) — die beiden ERS-gegateten Primitive
werden BENUTZT, nicht nachgebaut. Kein Aufrufer auf dem reason_setter-Pfad; das
Modul ist Werkzeug fuer die Session, nicht Teil der Setter-Maschinerie.

HERKUNFT: ERS-Zyklus work_files/konzept_notizblock_gate.json, Antwort `ans`,
evidence_label='assumed' (die Antwort traegt die Annahme a_drift). Wer diesen
Prototyp aendert, liest zuerst dort nach, was schon falsifiziert wurde.

WAS DAS IST
  Ein Notizblock, in den Aussagen als TEXT geschrieben und in Entitaeten/Relationen
  uebersetzt werden. Beim Commit expandiert die Maschinerie die einmal deklarierten
  Relationsregeln gegen die vorhandenen Instanzen zu AtMostOneOf-Kollisionen und
  meldet jeden Widerspruch — mit den Ursprungstexten beider Seiten.

WAS DAS FUER EIN DING IST (Sven, diese Session — die Rahmung, nicht Beiwerk)
  Der Notizblock ist NICHT die Quelle der Wahrheit, sondern eine ZUSAETZLICHE
  PRUEFUNG DES TEXTES. Er reduziert Fehler, er eliminiert sie nicht. Was er
  liefert, ist zusaetzliche INFORMATION — was davon benutzt wird, entscheidet der
  Lesende, nicht das Modul. Folge fuer die Auslegung jeder Ausgabe: eine Meldung
  heisst "hier lohnt ein Blick", nie "das ist falsch"; und SCHWEIGEN heisst
  ausdruecklich NICHT "das ist in Ordnung" — es kann ebensogut heissen, dass der
  Bestand zu duenn ist, um zu widersprechen, oder dass zwei Namen fuer dieselbe
  Sache nie zusammengefuehrt wurden. Wer das Schweigen als Evidenz nimmt, benutzt
  das Modul wieder als Orakel, und dann taeuscht es.
  Sein groesserer Nutzen liegt ohnehin nicht im Fangen einzelner Kollisionen,
  sondern darin, beim VERFOLGEN VON ABHAENGIGKEITEN Dinge sichtbar zu machen, die
  in verstreuten Aussagen unsichtbar bleiben.

WAS DAS NICHT IST (aus dem Gate, vor dem Bauen falsifiziert — nicht ueberlesen)
  - KEIN Wahrheitsbeweis. Der Zweck ist, auf MOEGLICHE Widersprueche aufmerksam zu
    machen. Ein falscher, aber kollisionsfreier Eintrag wird aufgenommen.
  - Der Fang kommt vom KOLLISIONSPRIMITIV, nicht von der Aussagenschicht. v0 faengt
    dieselbe Kollision. Die Aussagenschicht liefert die HANDHABBARKEIT: Ursprungstext,
    Mehrfachstuetzung/Ruecknahme, lesbares Protokoll.
  - AUSLASSUNGSDRIFT wird strukturell NICHT erfasst. Wenn eine Aussage einfach nicht
    mehr wiederholt wird, gibt es keine zweite Behauptung und damit keine Kollision.
    Gleiche Klasse wie v0s "faengt Frame-/Scope-Ueberdehnung gar nicht".
  - Die TREUE DER UEBERSETZUNG Text->Tripel ist ungeprueft. Der Fehler ist nicht
    beseitigt, sondern an den Uebersetzungsakt verlagert, wo er neben dem Originaltext
    steht und von Hand pruefbar ist. Deshalb zeigt jede Meldung beide Texte: die erste
    Frage lautet "habe ich richtig uebersetzt?", nicht "die Welt ist inkonsistent".
  - VOKABULARDRIFT: der Fang beruht auf Literal-Identitaet (aus v0 geerbt). Ein NICHT
    deklariertes Alias erzeugt keine Kollision, sondern Schweigen. `alias()` deckt nur
    ab, was jemand erklaert hat; `overview()['namensnah']` ist eine HEURISTIK auf
    Oberflaechenaehnlichkeit, kein Konflikt und keine Vollstaendigkeitsgarantie.
  - FALSCHES Alias verschmilzt zwei Dinge. Das ist die LAUTE Fehlerrichtung (Literale
    werden nur hinzugefuegt, nie entfernt — eine Verschmelzung kann Kollisionen nur
    erzeugen, nie unterdruecken), deshalb wurden Entitaets-Aliase zugelassen. ABER:
    (a) beschreiben die verschmolzenen Dinge disjunkte Slots, bleibt es still und es
    entsteht eine gut vernetzt aussehende Chimaere; (b) die Isolations-Heuristik in
    overview() verliert sie, weil ihr Grad steigt. Deshalb fuehrt jedes Literal seine
    rohen Schreibweisen mit und der Report zeigt sie.
  - LOGIKKETTEN WERDEN ZU ENDE VERFOLGT (Sven, diese Session): _close() bildet den
    Fixpunkt ueber implies/inverse/transitive, ohne Tiefenlimit. Eine Abkuerzung hier
    waere ein Defekt, kein Entwurf — sie erzeugte Schweigen, das die Regeln nicht
    decken. Abgeleitetes wird nach jeder Aenderung NEU BERECHNET, nie fortgeschrieben;
    damit ist die Ruecknahme ohne eigene Verfolgungslogik korrekt.
    Die Konfliktpruefung waehrend der Ableitung ist auf den EINGEFUEGTEN Fakt
    beschraenkt (_constraints_touching): der Bestand davor ist bereits geprueft, also
    kann nur verletzt werden, woran der neue Fakt selbst beteiligt ist. Gemessen
    gleiches Ergebnis bei 1 statt 190 gebauten Constraints pro Ableitung (60
    Entitaeten / 200 Fakten).
    Kosten, die bleiben: transitiver Abschluss ist im schlechtesten Fall quadratisch
    in den Entitaeten. Das ist jetzt die erste Stelle, die bei grossen Bestaenden
    reisst.
  - ANTISYMMETRISCH != IRREFLEXIV. Antisymmetrie erlaubt Selbstschleifen (aRb & bRa
    => a=b); nur irreflexiv verbietet sie. Bis zum Umbau kollabierte das erzeugte
    Literalpaar bei x==y zur Einermenge, wodurch antisymmetrisch STILL wie irreflexiv
    wirkte — gefunden durch Differenztest, nicht durch Lesen.
  - Wiederholt recheck() denselben Fund, ist das KEIN Rauschen: ein 'filed' heisst
    "echter Konflikt, bleibt offen stehen" — die Wiederholung meldet zutreffend, dass
    er noch dasteht. Nur 'fixed' beseitigt ihn. Was fehlt, ist die Unterscheidung
    "neu" vs "steht seit N offen", nicht Unterdrueckung.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date

from world_model import AtMostOneOf, Origin


# --------------------------------------------------------------------------
# SCHEMA — Relationen mit Rollen, einmal deklariert (behebt v0s Pro-Paar-Listung)
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class RelationDef:
    """Eine Relation als erstklassiges Objekt.

    v0 kennt nur Edge(src, relation, dst) ohne Typen, und kodiert Antisymmetrie
    als handgelistetes Literalpaar pro Entitaetenpaar (Origin.ENUMERATED_PAIR,
    generalisiert ausdruecklich nicht). Hier wird die Eigenschaft EINMAL an der
    Relation deklariert und beim Commit gegen die tatsaechlichen Instanzen
    expandiert.
    """
    name: str
    roles: tuple[str, ...]
    role_types: dict = field(default_factory=dict)   # rolle -> Konzeptname
    functional_on: tuple[str, ...] = ()              # Rolle(n) mit at-most-one Wert
    antisymmetric: bool = False
    irreflexive: bool = False
    symmetric: bool = False
    transitive: bool = False


@dataclass(frozen=True)
class RelationRule:
    """Regel ZWISCHEN Relationen. In v0 gibt es dafuer keinerlei Entsprechung."""
    kind: str          # implies | incompatible | inverse
    left: str
    right: str


# --------------------------------------------------------------------------
# AUSSAGEN-/WISSENSSCHICHT
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class Statement:
    """Der echte Text. Traegt Zeit/Session, weil Designdrift zwischen Sessions lebt."""
    id: str
    text: str
    session: str
    at: str = field(default_factory=lambda: date.today().isoformat())


@dataclass(frozen=True)
class Assertion:
    """Eine Relationsinstanz: Relation plus Rollenbelegung."""
    relation: str
    binding: tuple[tuple[str, str], ...]   # ((rolle, entitaet), ...) sortiert

    @staticmethod
    def of(relation: str, **roles) -> "Assertion":
        return Assertion(relation, tuple(sorted(roles.items())))

    def literal(self) -> str:
        inner = ",".join(f"{r}={e}" for r, e in self.binding)
        return f"{self.relation}({inner})"

    def entities(self) -> set[str]:
        return {e for _, e in self.binding}


@dataclass
class Conflict:
    id: str
    kind: str                  # schema | type | collision
    detail: str
    literals: list
    texts: list                # (statement_id, text, session, at) beider Seiten
    disposition: str = ""      # fixed | filed | carried  (I7)
    note: str = ""
    surfaces: dict = field(default_factory=dict)   # literal -> rohe Schreibweisen


# --------------------------------------------------------------------------
# DER NOTIZBLOCK
# --------------------------------------------------------------------------

class Notepad:
    def __init__(self):
        self.relations: dict[str, RelationDef] = {}
        self.rules: list[RelationRule] = []
        self.isa: dict[str, set[str]] = {}          # konzept -> oberkonzepte
        self.disjoint: list[tuple[str, frozenset]] = []
        self.entity_types: dict[str, set[str]] = {}  # entitaet -> konzepte
        self.statements: dict[str, Statement] = {}
        self.support: dict[str, set[str]] = {}       # literal -> {statement_id}
        self.assertions: dict[str, Assertion] = {}   # literal -> Assertion
        self.derived: dict[str, tuple] = {}          # literal -> (regel, elternliteral)
        self.conflicts: list[Conflict] = []
        self.aliases: dict[str, dict[str, str]] = {  # art -> {alias: kanonisch}
            "entity": {}, "concept": {}, "relation": {}}
        self.surface: dict[str, set[str]] = {}       # literal -> rohe Schreibweisen
        self._cn = 0
        self._n = 0

    # ---- Deklarationen ---------------------------------------------------
    def declare_relation(self, rd: RelationDef):
        self.relations[rd.name] = rd

    def declare_rule(self, rule: RelationRule):
        self.rules.append(rule)

    def declare_concept(self, name, parents=()):
        self.isa.setdefault(name, set()).update(parents)

    def declare_disjoint(self, name, members):
        self.disjoint.append((name, frozenset(members)))

    def alias(self, art, alias_name, canonical):
        """Alias deklarieren. Aufloesung geschieht beim SCHREIBEN, nicht beim Pruefen:
        sonst liegen beide Formen im Bestand und der Speicher wird mehrdeutig. So
        traegt jede Sache genau einen Namen, und ein falsches Alias ist ein sichtbarer
        DEKLARATIONSFEHLER — dieselbe Verlagerung wie bei v0s Channel."""
        assert art in self.aliases
        self.aliases[art][alias_name] = canonical

    def _canon(self, art, name):
        seen = set()
        while name in self.aliases[art] and name not in seen:
            seen.add(name)
            name = self.aliases[art][name]
        return name

    def _canon_assertion(self, a: Assertion) -> tuple[Assertion, set[str]]:
        """Kanonisiere Relation und Entitaeten; gib die rohen Formen zurueck, die
        dabei verschluckt wurden."""
        raw = set()
        rel = self._canon("relation", a.relation)
        if rel != a.relation:
            raw.add(a.relation)
        binding = []
        for role, ent in a.binding:
            c = self._canon("entity", ent)
            if c != ent:
                raw.add(ent)
            binding.append((role, c))
        return Assertion(rel, tuple(sorted(binding))), raw

    def typed(self, entity, *concepts):
        entity = self._canon("entity", entity)
        self.entity_types.setdefault(entity, set()).update(
            self._canon("concept", c) for c in concepts)

    def _concept_closure(self, entity) -> set[str]:
        out, stack = set(), list(self.entity_types.get(entity, ()))
        while stack:
            c = stack.pop()
            if c in out:
                continue
            out.add(c)
            stack.extend(self.isa.get(c, ()))
        return out

    # ---- Schema-Eigenkonsistenz: Widerspruch ZWISCHEN Relationen ---------
    def check_schema(self) -> list[Conflict]:
        """Prueft das Regelwerk gegen sich selbst. Braucht KEINE einzige Instanz."""
        out = []
        pairs = {(r.kind, r.left, r.right) for r in self.rules}
        for kind, l, r in pairs:
            if kind == "implies" and (("incompatible", l, r) in pairs
                                      or ("incompatible", r, l) in pairs):
                out.append(self._conflict(
                    "schema", f"{l} implies {r}, aber {l} ist zugleich incompatible mit {r} "
                              f"— {l} ist damit unerfuellbar", [l, r], []))
        for rd in self.relations.values():
            if rd.symmetric and rd.antisymmetric:
                out.append(self._conflict(
                    "schema", f"Relation {rd.name} ist zugleich symmetrisch und antisymmetrisch",
                    [rd.name], []))
            if rd.symmetric and rd.irreflexive and rd.antisymmetric:
                pass
            for role in rd.functional_on:
                if role not in rd.roles:
                    out.append(self._conflict(
                        "schema", f"Relation {rd.name}: functional_on nennt Rolle {role!r}, "
                                  f"die es nicht gibt", [rd.name], []))
        return out

    # ---- Expansion: Relationsregeln -> AtMostOneOf ueber Instanzen -------
    def _expand(self, literals: set[str], pending: list[Assertion]) -> list[AtMostOneOf]:
        """Die Kernoperation. Deklarierte Relationseigenschaften werden gegen die
        VORHANDENEN Instanzen zu Kollisionsmengen ausgerollt — statt sie wie
        world_base.py pro Entitaetenpaar von Hand zu listen."""
        cons: list[AtMostOneOf] = []
        by_rel: dict[str, list[Assertion]] = {}
        for a in list(self.assertions.values()) + pending:
            by_rel.setdefault(a.relation, []).append(a)

        for name, rd in self.relations.items():
            insts = by_rel.get(name, [])

            for role in rd.functional_on:
                groups: dict[tuple, set[str]] = {}
                for a in insts:
                    key = tuple((r, e) for r, e in a.binding if r != role)
                    groups.setdefault(key, set()).add(a.literal())
                for key, lits in groups.items():
                    if len(lits) > 1:
                        cons.append(AtMostOneOf(
                            f"{name}.functional[{role}]@{dict(key)}",
                            frozenset(lits), Origin.PARTITION))

            if rd.antisymmetric and len(rd.roles) == 2:
                ra, rb = rd.roles
                seen = set()
                for a in insts:
                    b = dict(a.binding)
                    if ra not in b or rb not in b:
                        continue
                    x, y = b[ra], b[rb]
                    if x == y:
                        continue      # Antisymmetrie erlaubt Selbstschleifen (aRb & bRa => a=b);
                                      # nur irreflexive verbietet sie. Ohne diese Zeile kollabiert
                                      # das Literalpaar zur Einermenge und antisymmetrisch wirkt
                                      # still wie irreflexiv.
                    if (y, x) in seen or (x, y) in seen:
                        continue
                    seen.add((x, y))
                    cons.append(AtMostOneOf(
                        f"{name}.antisymmetry[{x},{y}]",
                        frozenset({Assertion.of(name, **{ra: x, rb: y}).literal(),
                                   Assertion.of(name, **{ra: y, rb: x}).literal()}),
                        Origin.ENUMERATED_PAIR))

            if rd.irreflexive and len(rd.roles) == 2:
                ra, rb = rd.roles
                for e in {e for a in insts for e in a.entities()}:
                    cons.append(AtMostOneOf(
                        f"{name}.irreflexivity[{e}]",
                        frozenset({Assertion.of(name, **{ra: e, rb: e}).literal()}),
                        Origin.ENUMERATED_PAIR))

        for rule in self.rules:
            if rule.kind != "incompatible":
                continue
            for a in by_rel.get(rule.left, []):
                twin = Assertion(rule.right, a.binding).literal()
                cons.append(AtMostOneOf(
                    f"incompatible[{rule.left}|{rule.right}]{a.binding}",
                    frozenset({a.literal(), twin}), Origin.ENUMERATED_PAIR))

        for dname, members in self.disjoint:
            for ent in set(self.entity_types) | {e for a in pending for e in a.entities()}:
                lits = {f"isa({ent},{m})" for m in members}
                cons.append(AtMostOneOf(f"{dname}@{ent}", frozenset(lits), Origin.PARTITION))
        return cons

    # ---- Abschluss: Logikketten werden zu Ende verfolgt ------------------
    def _close(self, base: set[str], assertions: dict, guard: bool = True) -> dict:
        """Fixpunkt ueber implies / inverse / transitive. KEIN Tiefenlimit: eine
        deklarierte Regel behauptet, dass ihre Folge gilt — fuehrt der Bestand sie
        nicht, haelt er weniger als seine eigenen Regeln sagen, und das entstehende
        Schweigen ist nicht regelgedeckt, sondern eine Abkuerzung im Code.
        Terminiert, weil die Literalmenge endlich ist und nur Neues aufgenommen wird;
        Regelzyklen (R=>S, S=>R) laufen daher nicht.
        Gibt literal -> {rule, parents, depth, path} zurueck."""
        known = dict(assertions)
        out: dict[str, dict] = {}
        by_rel: dict[str, list] = {}
        for a in assertions.values():
            by_rel.setdefault(a.relation, []).append(a)
        frontier = list(assertions.values())
        depth = 0
        while frontier:
            depth += 1
            nxt = []
            for a in frontier:
                for made, rule, path in self._one_step(a, known):
                    lit = made.literal()
                    if lit in known or lit in out:
                        continue
                    entry = {"rule": rule, "parents": [a.literal()],
                             "depth": depth, "path": path}
                    if guard and self._blocks(made, known, out, by_rel):
                        entry["blocked"] = True
                        out[lit] = entry
                        continue          # steht selbst im Konflikt -> lizenziert nichts weiter
                    out[lit] = entry
                    known[lit] = made
                    by_rel.setdefault(made.relation, []).append(made)
                    nxt.append(made)
            frontier = nxt
        return out

    def _constraints_touching(self, a: Assertion, by_rel: dict, ent_types: dict):
        """Nur die Constraints, an denen DIESER Fakt beteiligt sein kann.

        Der Bestand vor der Einfuegung ist per Konstruktion schon geprueft (jeder
        Commit laeuft atomar durch). Ein neuer Fakt kann daher nur Constraints
        verletzen, in denen er selbst vorkommt — alle uebrigen sind unveraendert
        erfuellt und koennen per Definition nichts finden. Das ist KEINE Naeherung,
        sondern derselbe Pruefumfang ohne den Teil, der nichts finden kann.

        Die Constraints werden hier VOM FAKT AUS konstruiert, nicht aus dem
        Gesamtbestand herausgefiltert."""
        lit = a.literal()
        b = dict(a.binding)
        rd = self.relations.get(a.relation)
        cons = []

        if rd:
            for role in rd.functional_on:
                if role not in b:
                    continue
                key = tuple((r, e) for r, e in a.binding if r != role)
                lits = {lit}
                for other in by_rel.get(a.relation, ()):
                    if tuple((r, e) for r, e in other.binding if r != role) == key:
                        lits.add(other.literal())
                if len(lits) > 1:
                    cons.append(AtMostOneOf(f"{a.relation}.functional[{role}]@{dict(key)}",
                                            frozenset(lits), Origin.PARTITION))

            if len(rd.roles) == 2:
                ra, rb = rd.roles
                if ra in b and rb in b:
                    x, y = b[ra], b[rb]
                    if rd.antisymmetric and x != y:
                        cons.append(AtMostOneOf(
                            f"{a.relation}.antisymmetry[{x},{y}]",
                            frozenset({Assertion.of(a.relation, **{ra: x, rb: y}).literal(),
                                       Assertion.of(a.relation, **{ra: y, rb: x}).literal()}),
                            Origin.ENUMERATED_PAIR))
                    if rd.irreflexive and x == y:
                        cons.append(AtMostOneOf(
                            f"{a.relation}.irreflexivity[{x}]",
                            frozenset({lit}), Origin.ENUMERATED_PAIR))

        for rule in self.rules:
            if rule.kind != "incompatible":
                continue
            if rule.left == a.relation:
                twin = Assertion(rule.right, a.binding).literal()
            elif rule.right == a.relation:
                twin = Assertion(rule.left, a.binding).literal()
            else:
                continue
            cons.append(AtMostOneOf(f"incompatible[{rule.left}|{rule.right}]{a.binding}",
                                    frozenset({lit, twin}), Origin.ENUMERATED_PAIR))

        if a.relation == "isa" and "obj" in b:
            for dname, members in self.disjoint:
                if b["obj"] in members:
                    cons.append(AtMostOneOf(
                        f"{dname}@{b.get('subj')}",
                        frozenset({f"isa({b.get('subj')},{m})" for m in members}),
                        Origin.PARTITION))
        return cons

    def _blocks(self, made: Assertion, known: dict, out: dict,
                by_rel: dict) -> bool:
        """Kollidiert das eben abgeleitete Literal mit dem bisher Bekannten?

        Wenn ja, wird NICHT weiter daraus abgeleitet. Sonst beansprucht eine einzige
        realitaetswidrige Aussage ueber ihre Folgen den halben Bestand: die Meldungen
        vervielfachen sich entlang der Kette, obwohl es ein einziger Bruch ist. Die
        Ableitung wird gesperrt, die MELDUNG nicht — unabhaengig erreichbare Konflikte
        bleiben sichtbar, weil sonst die (willkuerliche) Ableitungsreihenfolge
        entscheiden wuerde, welcher Fund ueberlebt."""
        lit = made.literal()
        universe = set(known) | {l for l in out if not out[l].get("blocked")} | {lit}
        universe |= {f"isa({e},{c})" for e, cs in self.entity_types.items() for c in cs}
        for con in self._constraints_touching(made, by_rel, self.entity_types):
            hit = con.violated_by(universe)
            if hit and lit in hit:
                return True
        return False

    def _one_step(self, a: Assertion, known: dict):
        """Alle Folgerungen aus EINER Assertion, gegeben der bisher bekannte Bestand."""
        made = []
        rd = self.relations.get(a.relation)
        for rule in self.rules:
            if rule.kind == "implies" and rule.left == a.relation:
                made.append((Assertion(rule.right, a.binding),
                             f"{rule.left} => {rule.right}", [a.literal()]))
            elif rule.kind == "inverse" and rule.left == a.relation and rd and len(rd.roles) == 2:
                ra, rb = rd.roles
                b = dict(a.binding)
                if ra in b and rb in b:
                    made.append((Assertion.of(rule.right, **{ra: b[rb], rb: b[ra]}),
                                 f"{rule.left} inverse_of {rule.right}", [a.literal()]))
        if rd and rd.transitive and len(rd.roles) == 2:
            ra, rb = rd.roles
            b = dict(a.binding)
            if ra in b and rb in b:
                for other in list(known.values()):
                    if other.relation != a.relation:
                        continue
                    ob = dict(other.binding)
                    if ob.get(ra) == b[rb] and ob.get(rb) != b[ra]:
                        made.append((Assertion.of(a.relation, **{ra: b[ra], rb: ob[rb]}),
                                     f"{a.relation} transitiv",
                                     [a.literal(), other.literal()]))
                    if ob.get(rb) == b[ra] and ob.get(ra) != b[rb]:
                        made.append((Assertion.of(a.relation, **{ra: ob[ra], rb: b[rb]}),
                                     f"{a.relation} transitiv",
                                     [other.literal(), a.literal()]))
        return made

    def explain(self, literal, _path=()):
        """Ableitungsspur eines abgeleiteten Literals bis auf behauptete Fakten.

        Die Besuchsliste laeuft PRO PFAD (_path), nicht global: ein Literal, das in
        zwei Geschwisterzweigen legitim vorkommt, ist kein Zyklus. Eine globale Liste
        meldete den zweiten Zweig faelschlich als solchen."""
        if literal in _path:
            return [f"{literal}  [Zyklus]"]
        _path = _path + (literal,)
        d = self.derived.get(literal)
        if d is None:
            sids = sorted(self.support.get(literal, ()))
            texts = [self.statements[s].text for s in sids if s in self.statements]
            return [f"{literal}  <behauptet: {'; '.join(texts) or '?'}>"]
        lines = [f"{literal}  <{d['rule']}, Tiefe {d['depth']}>"]
        for p in d["path"]:
            lines += ["    " + x for x in self.explain(p, _path)]
        return lines

    # ---- Commit ----------------------------------------------------------
    def commit(self, text, assertions, session="", isa_facts=()):
        """Eine Aussage committen. Gibt (ok, conflicts) zurueck.

        HAELT an statt zu verweigern: bei Kollision geht NICHTS ins Wissen, die
        Aussage bleibt mit beiden Ursprungstexten im Konfliktregister stehen und
        wartet auf eine Disposition (fixed|filed|carried, I7-Form).
        """
        offen = [c for c in self.conflicts if not c.disposition]
        if offen:
            return False, [self._conflict(
                "collision", f"{len(offen)} unerledigte(r) Konflikt(e) — erst disponieren "
                             f"(fixed|filed|carried), sonst wird der Block zur Halde",
                [c.id for c in offen], [])]

        schema = self.check_schema()
        if schema:
            self.conflicts.extend(schema)
            return False, schema

        self._n += 1
        st = Statement(f"s{self._n}", text, session or "unbekannt")

        pending, raw_forms = [], {}
        for a in assertions:
            ca, raw = self._canon_assertion(a)
            pending.append(ca)
            if raw:
                raw_forms.setdefault(ca.literal(), set()).update(raw)
        isa_facts = [(self._canon("entity", e), self._canon("concept", c))
                     for e, c in isa_facts]
        for ent, con in isa_facts:
            pending.append(Assertion.of("isa", subj=ent, obj=con))

        typ = self._type_conflicts(pending, st)
        if typ:
            self.conflicts.extend(typ)
            return False, typ

        base = dict(self.assertions)
        for a in pending:
            base[a.literal()] = a
        derived = self._close(set(base), base)

        asserted = set(base) | set(derived)
        asserted |= {f"isa({e},{c})" for e, cs in self.entity_types.items() for c in cs}
        asserted |= {f"isa({e},{c})" for e, c in isa_facts}
        new_lits = {a.literal() for a in pending} | (set(derived) - set(self.derived))

        inst = list(pending) + [self._mk(l) for l in derived]
        found = []
        for con in self._expand(asserted, inst):
            hit = con.violated_by(asserted)
            if hit:
                new_side = new_lits & hit
                if not new_side:
                    continue    # Altbestand kollidiert nicht mit sich selbst
                c = self._conflict(
                    "collision", f"{con.name} [{con.origin.value}]", sorted(hit),
                    self._texts(sorted(hit), st))
                for lit in hit:
                    forms = set(raw_forms.get(lit, ())) | set(self.surface.get(lit, ()))
                    if forms:
                        c.surfaces[lit] = sorted(forms)
                found.append(c)
        if found:
            self.conflicts.extend(found)
            return False, found

        self.statements[st.id] = st
        for ent, con in isa_facts:
            self.typed(ent, con)
        for a in pending:
            self.assertions[a.literal()] = a
            self.support.setdefault(a.literal(), set()).add(st.id)
            if a.literal() in raw_forms:
                self.surface.setdefault(a.literal(), set()).update(raw_forms[a.literal()])
        self._recompute()
        return True, []

    def _type_conflicts(self, pending, st):
        out = []
        for a in pending:
            rd = self.relations.get(a.relation)
            if not rd:
                continue
            for role, ent in a.binding:
                need = rd.role_types.get(role)
                if need and need not in self._concept_closure(ent):
                    out.append(self._conflict(
                        "type", f"{a.literal()}: Rolle {role!r} verlangt Konzept {need!r}, "
                                f"{ent!r} ist {sorted(self._concept_closure(ent)) or 'untypisiert'}",
                        [a.literal()], [(st.id, st.text, st.session, st.at)]))
        return out

    def _texts(self, literals, new_st):
        out = [(new_st.id, new_st.text, new_st.session, new_st.at)]
        for lit in literals:
            for sid in sorted(self.support.get(lit, ())):
                s = self.statements[sid]
                out.append((s.id, s.text, s.session, s.at))
        return out

    def _conflict(self, kind, detail, literals, texts):
        self._cn = getattr(self, "_cn", 0) + 1
        return Conflict(f"c{self._cn}", kind, detail, literals, texts)

    # ---- Disposition (I7) ------------------------------------------------
    def dispose(self, conflict_id, disposition, note=""):
        assert disposition in ("fixed", "filed", "carried")
        for c in self.conflicts:
            if c.id == conflict_id:
                c.disposition, c.note = disposition, note
                return True
        return False

    @staticmethod
    def _mk(literal: str) -> Assertion:
        rel, _, rest = literal.partition("(")
        binding = []
        for part in rest.rstrip(")").split(","):
            if "=" in part:
                r, _, e = part.partition("=")
                binding.append((r, e))
        return Assertion(rel, tuple(binding))

    def _recompute(self):
        """Abgeleitetes wird IMMER neu aus den behaupteten Fakten berechnet, nie
        inkrementell fortgeschrieben. Damit ist die Ruecknahme korrekt ohne eigene
        Verfolgungslogik: was seine Grundlage verliert, entsteht schlicht nicht mehr."""
        self.derived = self._close(set(self.assertions), dict(self.assertions))

    # ---- Ruecknahme: Mehrfachstuetzung ----------------------------------
    def withdraw(self, statement_id):
        """Stuetze entfernen. Was auf null Stuetzen faellt, wird entfernt UND gemeldet.
        Abgeleitetes faellt ueber _recompute() weg, nicht ueber Mitloeschen."""
        dropped = []
        for lit, sup in list(self.support.items()):
            sup.discard(statement_id)
            if not sup:
                dropped.append(lit)
                self.support.pop(lit, None)
                self.assertions.pop(lit, None)
        self.statements.pop(statement_id, None)
        before = set(self.derived)
        self._recompute()
        gone = sorted(before - set(self.derived))
        return {"behauptet_entfallen": sorted(dropped), "abgeleitet_entfallen": gone}

    # ---- Persistenz ------------------------------------------------------
    def save(self, path):
        """Der Bestand muss Sessions ueberleben, sonst ist Designdrift — der Leitfall —
        gar nicht sichtbar: Drift lebt per Definition ZWISCHEN Sitzungen."""
        data = {
            "relations": {n: {"name": r.name, "roles": list(r.roles),
                              "role_types": r.role_types,
                              "functional_on": list(r.functional_on),
                              "antisymmetric": r.antisymmetric,
                              "irreflexive": r.irreflexive,
                              "symmetric": r.symmetric}
                          for n, r in self.relations.items()},
            "rules": [{"kind": r.kind, "left": r.left, "right": r.right} for r in self.rules],
            "isa": {k: sorted(v) for k, v in self.isa.items()},
            "disjoint": [[n, sorted(m)] for n, m in self.disjoint],
            "entity_types": {k: sorted(v) for k, v in self.entity_types.items()},
            "statements": {s.id: {"id": s.id, "text": s.text, "session": s.session, "at": s.at}
                           for s in self.statements.values()},
            "assertions": {lit: {"relation": a.relation,
                                 "binding": [list(b) for b in a.binding]}
                           for lit, a in self.assertions.items()},
            "support": {k: sorted(v) for k, v in self.support.items()},
            "derived": self.derived,
            "aliases": self.aliases,
            "surface": {k: sorted(v) for k, v in self.surface.items()},
            "conflicts": [{"id": c.id, "kind": c.kind, "detail": c.detail,
                           "literals": c.literals, "texts": [list(t) for t in c.texts],
                           "disposition": c.disposition, "note": c.note,
                           "surfaces": c.surfaces} for c in self.conflicts],
            "n": self._n,
        }
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=1)

    @classmethod
    def load(cls, path):
        np = cls()
        with open(path, encoding="utf-8") as fh:
            d = json.load(fh)
        for n, r in d["relations"].items():
            np.relations[n] = RelationDef(
                name=r["name"], roles=tuple(r["roles"]), role_types=r["role_types"],
                functional_on=tuple(r["functional_on"]), antisymmetric=r["antisymmetric"],
                irreflexive=r["irreflexive"], symmetric=r["symmetric"])
        np.rules = [RelationRule(**r) for r in d["rules"]]
        np.isa = {k: set(v) for k, v in d["isa"].items()}
        np.disjoint = [(n, frozenset(m)) for n, m in d["disjoint"]]
        np.entity_types = {k: set(v) for k, v in d["entity_types"].items()}
        np.statements = {k: Statement(**v) for k, v in d["statements"].items()}
        np.assertions = {lit: Assertion(a["relation"], tuple(tuple(b) for b in a["binding"]))
                         for lit, a in d["assertions"].items()}
        np.support = {k: set(v) for k, v in d["support"].items()}
        np.derived = d["derived"]
        np.aliases = d["aliases"]
        np.surface = {k: set(v) for k, v in d["surface"].items()}
        np.conflicts = [Conflict(id=c["id"], kind=c["kind"], detail=c["detail"],
                                 literals=c["literals"], texts=[tuple(t) for t in c["texts"]],
                                 disposition=c["disposition"], note=c["note"],
                                 surfaces=c["surfaces"]) for c in d["conflicts"]]
        np._n = d["n"]
        np._cn = len(np.conflicts)
        return np

    def recheck(self):
        """Den GESAMTEN Bestand gegen die AKTUELLEN Regeln pruefen, ohne etwas zu
        aendern. Gebraucht, weil das Schema den Bestand ueberlebt: wird eine Relation
        spaeter geschaerft (functional_on nachgetragen, incompatible erklaert), koennen
        Aussagen kollidieren, die beim Commit noch zulaessig waren. Das IST Designdrift,
        nur von der Regelseite her. Meldet, veraendert nichts."""
        found = self.check_schema()
        self._recompute()
        asserted = set(self.assertions) | set(self.derived)
        asserted |= {f"isa({e},{c})" for e, cs in self.entity_types.items() for c in cs}
        for con in self._expand(asserted, [self._mk(l) for l in self.derived]):
            hit = con.violated_by(asserted)
            if hit:
                c = self._conflict("collision", f"{con.name} [{con.origin.value}] (recheck)",
                                   sorted(hit), self._texts_for(sorted(hit)))
                for lit in hit:
                    if lit in self.surface:
                        c.surfaces[lit] = sorted(self.surface[lit])
                found.append(c)
        return found

    def _texts_for(self, literals):
        out = []
        for lit in literals:
            for sid in sorted(self.support.get(lit, ())):
                s = self.statements.get(sid)
                if s:
                    out.append((s.id, s.text, s.session, s.at))
        return out

    # ---- Uebersicht ------------------------------------------------------
    def overview(self):
        used = {a.relation for a in self.assertions.values()} | {self._mk(l).relation for l in self.derived}
        ents = {e for a in self.assertions.values() for e in a.entities()}
        degree = {e: 0 for e in ents}
        for a in self.assertions.values():
            for e in a.entities():
                degree[e] += 1
        return {
            "aussagen": len(self.statements),
            "behauptet": len(self.assertions),
            "abgeleitet": len(self.derived),
            "tote_relationen": sorted(set(self.relations) - used),
            "isolierte_entitaeten": sorted(e for e, d in degree.items() if d <= 1),
            "mehrfach_gestuetzt": sorted(l for l, s in self.support.items() if len(s) > 1),
            "offene_konflikte": [c.id for c in self.conflicts if not c.disposition],
            "namensnah": self._near_names(ents),
            "verschmolzen": {l: sorted(f) for l, f in self.surface.items()},
        }

    @staticmethod
    def _norm(name):
        base = name.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
        return base.lower().replace("_", "").replace("-", "").replace(".", "")

    def _near_names(self, ents):
        """HEURISTIK, kein Konflikt: Namen, die sich nur in Pfadpraefix, Schreibweise
        oder Trennzeichen unterscheiden. Findet FEHLENDE Aliase — die stille
        Fehlerrichtung, die die Maschinerie sonst gar nicht bemerkt. Unvollstaendig
        per Konstruktion: echte Synonyme ohne Oberflaechenaehnlichkeit
        (verdrahtet/wired) faengt das NICHT."""
        groups: dict[str, set[str]] = {}
        for e in ents:
            groups.setdefault(self._norm(e), set()).add(e)
        return {k: sorted(v) for k, v in groups.items() if len(v) > 1}

    def report(self, conflicts):
        lines = []
        for c in conflicts:
            lines.append(f"[{c.id}] {c.kind.upper()}: {c.detail}")
            for lit in c.literals:
                d = self.derived.get(lit)
                if d and d.get("blocked"):
                    lines.append(f"    ! {lit} steht selbst im Konflikt — "
                                 f"seine Folgen wurden NICHT weiter abgeleitet")
            for lit in c.literals:
                lines.append(f"    literal: {lit}")
                if lit in c.surfaces:
                    lines.append(f"      zusammengelegt aus: {c.surfaces[lit]} "
                                 f"— falsches Alias? Ursprungstexte vergleichen")
            for sid, text, sess, at in c.texts:
                lines.append(f"    <{sid} | {sess} | {at}> {text}")
            lines.append("    -> pruefe ZUERST die Uebersetzung, dann den Widerspruch")
        return "\n".join(lines)


# --------------------------------------------------------------------------
# DEMO — der Leitfall aus dem Paket-README (mining.py built+wired -> NOT WIRED)
# --------------------------------------------------------------------------
if __name__ == "__main__":
    np = Notepad()
    np.declare_concept("Modul")
    np.declare_concept("Verdrahtungsstatus")
    np.declare_relation(RelationDef(
        name="hat_status", roles=("modul", "status"),
        role_types={"modul": "Modul"}, functional_on=("status",)))
    np.declare_relation(RelationDef(
        name="ersetzt", roles=("neu", "alt"), antisymmetric=True, irreflexive=True))
    np.declare_relation(RelationDef(name="auf_solve_pfad", roles=("modul",)))
    np.declare_rule(RelationRule("implies", "auf_solve_pfad", "verdrahtet"))
    np.declare_relation(RelationDef(name="verdrahtet", roles=("modul",)))
    np.typed("mining.py", "Modul")

    print("=== Aussage 1 (Sitzung 8) ===")
    ok, cf = np.commit(
        "mining.py ist gebaut und verdrahtet, laeuft auf dem Solve-Pfad.",
        [Assertion.of("hat_status", modul="mining.py", status="built+wired")],
        session="Sitzung 8")
    print("committed:", ok)

    print("\n=== Aussage 2 (Sitzung 11) — widerspricht ===")
    ok, cf = np.commit(
        "Korrektur: mining.py ist gebaut, aber NICHT verdrahtet.",
        [Assertion.of("hat_status", modul="mining.py", status="built,NOT_WIRED")],
        session="Sitzung 11")
    print("committed:", ok)
    print(np.report(cf))

    print("\n=== Disposition, dann Neuversuch ===")
    np.dispose(cf[0].id, "filed", "echter Konflikt: Sitzung 11 korrigiert Sitzung 8")
    np.withdraw("s1")
    ok, cf = np.commit(
        "Korrektur: mining.py ist gebaut, aber NICHT verdrahtet.",
        [Assertion.of("hat_status", modul="mining.py", status="built,NOT_WIRED")],
        session="Sitzung 11")
    print("committed:", ok)

    print("\n=== Schema-Widerspruch, ganz ohne Instanzen ===")
    np2 = Notepad()
    np2.declare_relation(RelationDef(name="ersetzt", roles=("neu", "alt")))
    np2.declare_relation(RelationDef(name="haengt_ab_von", roles=("neu", "alt")))
    np2.declare_rule(RelationRule("implies", "ersetzt", "haengt_ab_von"))
    np2.declare_rule(RelationRule("incompatible", "ersetzt", "haengt_ab_von"))
    for c in np2.check_schema():
        print(f"[{c.id}] {c.kind.upper()}: {c.detail}")

    print("\n=== Uebersicht ===")
    for k, v in np.overview().items():
        print(f"  {k}: {v}")
