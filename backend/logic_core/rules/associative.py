from __future__ import annotations

from ..ast_nodes import *
from .common import Suggestion, make_suggestion, apply_by_path, get_node_at_path
from .rule_metadata import Z16A, Z16B


# Tento modul implementuje asociatívne zákony:
#   Z16a: (α ∧ β) ∧ γ ↔ α ∧ (β ∧ γ)
#   Z16b: (α ∨ β) ∨ γ ↔ α ∨ (β ∨ γ)
#
# Asociativita umožňuje meniť zátvorkovanie pri opakovaní tej istej logickej spojky
# bez zmeny významu formule.


# Funkcia overí, či má daný uzol tvar vhodný na použitie asociatívneho zákona.
# Rozlišujú sa dva smery:
#   - forward:  z ľavého zátvorkovania na pravé
#   - backward: z pravého zátvorkovania na ľavé
#
# Ak je zhoda úspešná, funkcia vráti typ transformácie a tri podformuly p, q, r.
# Ak zhoda neexistuje, vráti None.
def _match_associative(node: Node):
    # Pri konjunkcii tvaru (p ∧ q) ∧ r sa môže použiť prechod na p ∧ (q ∧ r).
    if isinstance(node, And) and isinstance(node.left, And):
        return ("forward_and", node.left.left, node.left.right, node.right)

    # Pri disjunkcii tvaru (p ∨ q) ∨ r sa môže použiť prechod na p ∨ (q ∨ r).
    if isinstance(node, Or) and isinstance(node.left, Or):
        return ("forward_or", node.left.left, node.left.right, node.right)

    # Pri konjunkcii tvaru p ∧ (q ∧ r) sa môže použiť opačný smer na (p ∧ q) ∧ r.
    if isinstance(node, And) and isinstance(node.right, And):
        return ("backward_and", node.left, node.right.left, node.right.right)

    # Pri disjunkcii tvaru p ∨ (q ∨ r) sa môže použiť opačný smer na (p ∨ q) ∨ r.
    if isinstance(node, Or) and isinstance(node.right, Or):
        return ("backward_or", node.left, node.right.left, node.right.right)

    return None


# Funkcia prejde celý strom formule a nájde všetky miesta,
# na ktorých možno použiť asociatívny zákon.
# Výsledkom je zoznam návrhov typu Suggestion.
def find_associative_suggestions(root: Node) -> List[Suggestion]:
    suggestions = []

    # Rekurzívna funkcia walk prechádza strom a na každom uzle skúša,
    # či spĺňa niektorý z podporovaných asociatívnych tvarov.
    def walk(node: Node, path: str):
        match = _match_associative(node)
        if match is not None:
            kind, p, q, r = match

            if kind == "forward_and":
                rewritten = And(p, And(q, r))
                meta = Z16A
            elif kind == "forward_or":
                rewritten = Or(p, Or(q, r))
                meta = Z16B
            elif kind == "backward_and":
                rewritten = And(And(p, q), r)
                meta = Z16A
            else:
                rewritten = Or(Or(p, q), r)
                meta = Z16B

            suggestions.append(make_suggestion(
                path=path,
                meta=meta,
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


# Funkcia aplikuje asociatívny zákon na uzol stromu určený cestou path.
# Podľa rozpoznaného tvaru vykoná prechod medzi ľavým a pravým zátvorkovaním.
# Ak sa na danej pozícii asociatívny zákon nedá použiť, vyvolá sa chyba.
def apply_associative_at_path(root: Node, path: str) -> Node:
    current = get_node_at_path(root, path)
    match = _match_associative(current)

    if match is None:
        raise ValueError("Selected path is not applicable for associativity")

    kind, p, q, r = match

    if kind == "forward_and":
        new_subtree = And(p, And(q, r))
    elif kind == "forward_or":
        new_subtree = Or(p, Or(q, r))
    elif kind == "backward_and":
        new_subtree = And(And(p, q), r)
    else:
        new_subtree = Or(Or(p, q), r)

    return apply_by_path(root, path, new_subtree)
