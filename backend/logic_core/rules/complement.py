from __future__ import annotations

from ..ast_nodes import *
from .common import Suggestion, make_suggestion, apply_by_path, get_node_at_path, _is_negation_of
from .rule_metadata import Z4, Z5


# Tento modul implementuje komplementárne zákony:
#   Z4: α ∨ ¬α ↔ T
#   Z5: α ∧ ¬α ↔ F
#
# Pre každé pravidlo sú definované dve funkcie:
#   - funkcia na vyhľadanie všetkých aplikovateľných miest v strome,
#   - funkcia na aplikovanie pravidla na konkrétnom mieste určenom cestou path.


# Funkcia overí, či je daný uzol tvaru α ∨ ¬α alebo ¬α ∨ α.
# Ak áno, vráti konštantu T.
# Inak vráti None.
def _match_or_complement(node: Node):
    if isinstance(node, Or):
        if _is_negation_of(node.left, node.right) or _is_negation_of(node.right, node.left):
            return Const(True)
    return None


# Funkcia prejde celý strom formule a nájde všetky miesta,
# na ktorých možno použiť zákon Z4: α ∨ ¬α ↔ T.
# Výsledkom je zoznam návrhov typu Suggestion.
def find_or_complement_suggestions(root: Node) -> List[Suggestion]:
    suggestions = []

    # Rekurzívna funkcia walk prechádza strom a na každom uzle skúša,
    # či zodpovedá tvaru pravidla α ∨ ¬α ↔ T.
    def walk(node: Node, path: str):
        if _match_or_complement(node):
            suggestions.append(make_suggestion(
                path=path,
                meta=Z4,
                before=str(node),
                after="T"
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


# Funkcia aplikuje zákon Z4 na uzol stromu určený cestou path.
# Ak sa na danej pozícii nachádza tvar α ∨ ¬α alebo ¬α ∨ α,
# uzol sa nahradí konštantou T.
# Inak sa vyvolá chyba.
def apply_or_complement_at_path(root: Node, path: str) -> Node:
    current = get_node_at_path(root, path)
    matched = _match_or_complement(current)
    if matched is None:
        raise ValueError("Selected path is not applicable for p ∨ ¬p ⇔ T")
    return apply_by_path(root, path, matched)


# Funkcia overí, či je daný uzol tvaru α ∧ ¬α alebo ¬α ∧ α.
# Ak áno, vráti konštantu F.
# Inak vráti None.
def _match_and_complement(node: Node):
    if isinstance(node, And):
        if _is_negation_of(node.left, node.right) or _is_negation_of(node.right, node.left):
            return Const(False)
    return None


# Funkcia prejde celý strom formule a nájde všetky miesta,
# na ktorých možno použiť zákon Z5: α ∧ ¬α ↔ F.
# Výsledkom je zoznam návrhov typu Suggestion.
def find_and_complement_suggestions(root: Node) -> List[Suggestion]:
    suggestions = []

    # Rekurzívna funkcia walk prechádza strom a na každom uzle skúša,
    # či zodpovedá tvaru pravidla α ∧ ¬α ↔ F.
    def walk(node: Node, path: str):
        if _match_and_complement(node):
            suggestions.append(make_suggestion(
                path=path,
                meta=Z5,
                before=str(node),
                after="F"
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


# Funkcia aplikuje zákon Z5 na uzol stromu určený cestou path.
# Ak sa na danej pozícii nachádza tvar α ∧ ¬α alebo ¬α ∧ α,
# uzol sa nahradí konštantou F.
# Inak sa vyvolá chyba.
def apply_and_complement_at_path(root: Node, path: str) -> Node:
    current = get_node_at_path(root, path)
    matched = _match_and_complement(current)
    if matched is None:
        raise ValueError("Selected path is not applicable for p ∧ ¬p ⇔ F")
    return apply_by_path(root, path, matched)
