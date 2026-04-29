from __future__ import annotations

from ..ast_nodes import *
from .common import Suggestion, make_suggestion, apply_by_path, get_node_at_path
from .rule_metadata import Z15


# Tento modul implementuje definíciu ekvivalencie:
#   Z15: (α ↔ β) ↔ ((α → β) ∧ (β → α))
#
# Pravidlo umožňuje:
#   - rozvinúť ekvivalenciu na dvojicu implikácií,
#   - alebo naopak z dvojice opačných implikácií vytvoriť ekvivalenciu.


# Funkcia overí, či má daný uzol tvar vhodný na použitie definície ekvivalencie.
# Rozlišujú sa dva smery:
#   - forward:  α ↔ β  ->  (α → β) ∧ (β → α)
#   - backward: (α → β) ∧ (β → α)  ->  α ↔ β
#
# Ak uzol zodpovedá niektorému z týchto tvarov, funkcia vráti typ transformácie
# a dvojicu podformúl p, q. Inak vráti None.
def _match_iff_definition(node: Node):
    # Priamy smer: uzol je ekvivalencia p ↔ q.
    if isinstance(node, Iff):
        return ("forward", node.left, node.right)

    # Opačný smer: uzol je konjunkcia dvoch implikácií.
    # Overuje sa, či ide presne o dvojicu (p → q) a (q → p).
    if isinstance(node, And) and isinstance(node.left, Imp) and isinstance(node.right, Imp):
        a1, b1 = node.left.left, node.left.right
        a2, b2 = node.right.left, node.right.right

        if a1 == b2 and b1 == a2:
            return ("backward", a1, b1)

    return None


# Funkcia prejde celý strom formule a nájde všetky miesta,
# na ktorých možno použiť definíciu ekvivalencie.
# Výsledkom je zoznam návrhov typu Suggestion.
def find_iff_definition_suggestions(root: Node) -> List[Suggestion]:
    suggestions = []

    # Rekurzívna funkcia walk prechádza strom a na každom uzle skúša,
    # či sa na ňom dá aplikovať pravidlo Z15.
    def walk(node: Node, path: str):
        match = _match_iff_definition(node)
        if match is not None:
            kind, p, q = match

            if kind == "forward":
                rewritten = And(Imp(p, q), Imp(q, p))
            else:
                rewritten = Iff(p, q)

            suggestions.append(make_suggestion(
                path=path,
                meta=Z15,
                before=str(node),
                after=str(rewritten),
            ))

        # Rekurzívne pokračovanie do ľavého a pravého podstromu
        # pri binárnych logických spojkách.
        if isinstance(node, (And, Or, Imp, Iff)):
            walk(node.left, path + (".left" if path else "left"))
            walk(node.right, path + (".right" if path else "right"))

        # Rekurzívne pokračovanie do vnútorného uzla negácie.
        elif isinstance(node, Not):
            walk(node.child, path + (".child" if path else "child"))

    walk(root, "")
    return suggestions


# Funkcia aplikuje definíciu ekvivalencie na uzol stromu určený cestou path.
# Podľa rozpoznaného tvaru buď:
#   - rozvinie ekvivalenciu na konjunkciu dvoch implikácií,
#   - alebo zodpovedajúcu konjunkciu implikácií zbalí späť na ekvivalenciu.
#
# Ak sa na danej pozícii pravidlo Z15 nedá použiť, vyvolá sa chyba.
def apply_iff_definition_at_path(root: Node, path: str) -> Node:
    current = get_node_at_path(root, path)
    match = _match_iff_definition(current)

    if match is None:
        raise ValueError("Selected path is not applicable for equivalence definition")

    kind, p, q = match

    if kind == "forward":
        new_subtree = And(Imp(p, q), Imp(q, p))
    else:
        new_subtree = Iff(p, q)

    return apply_by_path(root, path, new_subtree)
