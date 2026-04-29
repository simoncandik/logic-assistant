from __future__ import annotations
from dataclasses import dataclass
from ..ast_nodes import *
from .rule_metadata import RuleMeta


# Trieda Suggestion reprezentuje jeden konkrétny návrh ekvivalentnej úpravy.
# Obsahuje cestu k podformule v strome, identifikáciu použitého zákona
# a textový tvar formule pred aj po úprave.
@dataclass(frozen=True)
class Suggestion:
    path: str
    rule_code: str
    rule_name: str
    rule_form: str
    rule: str
    before: str
    after: str


# Pomocná funkcia vytvorí objekt Suggestion z metadát pravidla a textových tvarov
# formuly pred a po úprave.
def make_suggestion(path: str, meta: RuleMeta, before: str, after: str) -> Suggestion:
    return Suggestion(
        path=path,
        rule_code=meta.code,
        rule_name=meta.name,
        rule_form=meta.form,
        rule=meta.label,
        before=before,
        after=after,
    )


# Funkcia apply_by_path nahradí podstrom na zadanej ceste novým podstromom.
# Cesta je zapísaná reťazcom, napríklad "left.right" alebo "child".
# Výsledkom je nový strom formule, pretože uzly sú nemenné.
def apply_by_path(root: Node, path: str, new_subtree: Node) -> Node:
    # Prázdna cesta znamená, že sa má nahradiť celý koreň stromu.
    if path == "":
        return new_subtree

    parts = path.split(".")

    # Vnútorná rekurzívna funkcia zostaví nový strom od koreňa po miesto zmeny.
    def rebuild(node: Node, i: int) -> Node:
        # Ak sme sa dostali na koniec cesty, vrátime nový podstrom.
        if i == len(parts):
            return new_subtree

        part = parts[i]

        # Spracovanie negácie, ktorá má jediného potomka child.
        if isinstance(node, Not) and part == "child":
            return Not(rebuild(node.child, i + 1))

        # Spracovanie binárnych uzlov so zložkami left a right.
        if isinstance(node, (And, Or, Imp, Iff)):
            if part == "left":
                return type(node)(rebuild(node.left, i + 1), node.right)  # type: ignore
            if part == "right":
                return type(node)(node.left, rebuild(node.right, i + 1))  # type: ignore

        # Ak cesta nezodpovedá štruktúre uzla, ide o chybnú cestu.
        raise ValueError(f"Invalid path '{path}' for node {node}")

    return rebuild(root, 0)


# Funkcia get_node_at_path vráti poduzol stromu, ktorý sa nachádza na zadanej ceste.
# Používa sa najmä pri zisťovaní, či je možné na dané miesto aplikovať konkrétne pravidlo.
def get_node_at_path(root: Node, path: str) -> Node:
    parts = path.split(".") if path else []
    current = root

    for part in parts:
        # Pohyb do vnútorného uzla negácie.
        if isinstance(current, Not) and part == "child":
            current = current.child

        # Pohyb do ľavého alebo pravého podstromu binárneho uzla.
        elif isinstance(current, (And, Or, Imp, Iff)) and part in ("left", "right"):
            current = getattr(current, part)

        # Ak cesta nezodpovedá štruktúre stromu, ide o chybný vstup.
        else:
            raise ValueError(f"Invalid path '{path}'")

    return current


# Funkcia pretty zabezpečuje jednotný textový výpis uzla.
# V aktuálnej implementácii iba využíva metódu __str__ definovanú v triedach AST.
def pretty(node: Node) -> str:
    return str(node)


# Pomocná funkcia overí, či uzol a je negáciou uzla b.
# Používa sa napríklad pri komplementárnych zákonoch p ∨ ¬p a p ∧ ¬p.
def _is_negation_of(a: Node, b: Node) -> bool:
    return isinstance(a, Not) and a.child == b
