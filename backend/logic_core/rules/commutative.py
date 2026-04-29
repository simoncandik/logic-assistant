from __future__ import annotations

from ..ast_nodes import *
from .common import Suggestion, make_suggestion, apply_by_path, get_node_at_path
from .rule_metadata import Z11A, Z11B


# Tento modul implementuje komutatívne zákony:
#   Z11a: α ∧ β ↔ β ∧ α
#   Z11b: α ∨ β ↔ β ∨ α
#
# Komutatívnosť umožňuje zmeniť poradie operandov bez zmeny významu formule.


# Funkcia overí, či je daný uzol konjunkcia alebo disjunkcia,
# pri ktorej má zmysel zameniť ľavý a pravý operand.
# Ak áno, vráti ich v prehodenom poradí.
# Ak sú obe strany rovnaké, návrh sa nevytvára, pretože by nevznikla žiadna zmena.
def _match_commutative(node: Node):
    if isinstance(node, (And, Or)):
        if node.left != node.right:
            return node.right, node.left
    return None


# Funkcia prejde celý strom formule a nájde všetky miesta,
# na ktorých možno použiť komutatívny zákon.
# Výsledkom je zoznam návrhov typu Suggestion.
def find_commutative_suggestions(root: Node) -> List[Suggestion]:
    suggestions = []

    # Rekurzívna funkcia walk prechádza strom a na každom uzle skúša,
    # či ide o konjunkciu alebo disjunkciu s rôznymi operandmi.
    def walk(node: Node, path: str):
        swapped = _match_commutative(node)
        if swapped is not None:
            right, left = swapped
            meta = Z11A if isinstance(node, And) else Z11B
            suggestions.append(make_suggestion(
                path=path,
                meta=meta,
                before=str(node),
                after=str(type(node)(right, left)),
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


# Funkcia aplikuje komutatívny zákon na uzol stromu určený cestou path.
# Ľavý a pravý operand sa na zvolenom mieste vymenia.
# Ak sa na danej pozícii komutatívny zákon nedá použiť, vyvolá sa chyba.
def apply_commutative_at_path(root: Node, path: str) -> Node:
    current = get_node_at_path(root, path)
    swapped = _match_commutative(current)
    if swapped is None:
        raise ValueError("Selected path is not commutative")

    right, left = swapped
    new_subtree = type(current)(right, left)
    return apply_by_path(root, path, new_subtree)
