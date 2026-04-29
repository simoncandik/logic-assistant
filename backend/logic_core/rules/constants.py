from __future__ import annotations

from ..ast_nodes import *
from .common import Suggestion, make_suggestion, apply_by_path, get_node_at_path
from .rule_metadata import Z6, Z7, Z8, Z9


# Tento modul implementuje zákony s logickými konštantami:
#   Z6: T ∧ α ↔ α
#   Z7: F ∧ α ↔ F
#   Z8: F ∨ α ↔ α
#   Z9: T ∨ α ↔ T
#
# Pre každé pravidlo sú definované dve funkcie:
#   - funkcia na vyhľadanie všetkých aplikovateľných miest v strome,
#   - funkcia na aplikovanie pravidla na konkrétnom mieste určenom cestou path.


# Funkcia overí, či je daný uzol tvaru T ∧ α alebo α ∧ T.
# Ak áno, vráti podformulu α.
# Inak vráti None.
def _match_and_true(node: Node):
    if isinstance(node, And):
        if isinstance(node.left, Const) and node.left.value is True:
            return node.right
        if isinstance(node.right, Const) and node.right.value is True:
            return node.left
    return None


# Funkcia prejde celý strom formule a nájde všetky miesta,
# na ktorých možno použiť zákon Z6: T ∧ α ↔ α.
# Výsledkom je zoznam návrhov typu Suggestion.
def find_and_true_suggestions(root: Node) -> List[Suggestion]:
    suggestions = []

    # Rekurzívna funkcia walk prechádza strom a na každom uzle skúša,
    # či zodpovedá tvaru pravidla T ∧ α ↔ α.
    def walk(node: Node, path: str):
        inner = _match_and_true(node)
        if inner is not None:
            suggestions.append(make_suggestion(
                path=path,
                meta=Z6,
                before=str(node),
                after=str(inner)
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


# Funkcia aplikuje zákon Z6 na uzol stromu určený cestou path.
# Ak sa na danej pozícii nachádza tvar T ∧ α alebo α ∧ T,
# uzol sa nahradí podformulou α.
# Inak sa vyvolá chyba.
def apply_and_true_at_path(root: Node, path: str) -> Node:
    current = get_node_at_path(root, path)
    inner = _match_and_true(current)
    if inner is None:
        raise ValueError("Selected path is not applicable for T ∧ p")
    return apply_by_path(root, path, inner)


# Funkcia overí, či je daný uzol tvaru F ∧ α alebo α ∧ F.
# Ak áno, vráti konštantu F.
# Inak vráti None.
def _match_and_false(node: Node):
    if isinstance(node, And):
        if isinstance(node.left, Const) and node.left.value is False:
            return Const(False)
        if isinstance(node.right, Const) and node.right.value is False:
            return Const(False)
    return None


# Funkcia prejde celý strom formule a nájde všetky miesta,
# na ktorých možno použiť zákon Z7: F ∧ α ↔ F.
# Výsledkom je zoznam návrhov typu Suggestion.
def find_and_false_suggestions(root: Node) -> List[Suggestion]:
    suggestions = []

    # Rekurzívna funkcia walk prechádza strom a na každom uzle skúša,
    # či zodpovedá tvaru pravidla F ∧ α ↔ F.
    def walk(node: Node, path: str):
        if _match_and_false(node):
            suggestions.append(make_suggestion(
                path=path,
                meta=Z7,
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


# Funkcia aplikuje zákon Z7 na uzol stromu určený cestou path.
# Ak sa na danej pozícii nachádza tvar F ∧ α alebo α ∧ F,
# uzol sa nahradí konštantou F.
# Inak sa vyvolá chyba.
def apply_and_false_at_path(root: Node, path: str) -> Node:
    current = get_node_at_path(root, path)
    matched = _match_and_false(current)
    if matched is None:
        raise ValueError("Selected path is not applicable for F ∧ p ⇔ F")
    return apply_by_path(root, path, matched)


# Funkcia overí, či je daný uzol tvaru F ∨ α alebo α ∨ F.
# Ak áno, vráti podformulu α.
# Inak vráti None.
def _match_or_false(node: Node):
    if isinstance(node, Or):
        if isinstance(node.left, Const) and node.left.value is False:
            return node.right
        if isinstance(node.right, Const) and node.right.value is False:
            return node.left
    return None


# Funkcia prejde celý strom formule a nájde všetky miesta,
# na ktorých možno použiť zákon Z8: F ∨ α ↔ α.
# Výsledkom je zoznam návrhov typu Suggestion.
def find_or_false_suggestions(root: Node) -> List[Suggestion]:
    suggestions = []

    # Rekurzívna funkcia walk prechádza strom a na každom uzle skúša,
    # či zodpovedá tvaru pravidla F ∨ α ↔ α.
    def walk(node: Node, path: str):
        inner = _match_or_false(node)
        if inner is not None:
            suggestions.append(make_suggestion(
                path=path,
                meta=Z8,
                before=str(node),
                after=str(inner)
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


# Funkcia aplikuje zákon Z8 na uzol stromu určený cestou path.
# Ak sa na danej pozícii nachádza tvar F ∨ α alebo α ∨ F,
# uzol sa nahradí podformulou α.
# Inak sa vyvolá chyba.
def apply_or_false_at_path(root: Node, path: str) -> Node:
    current = get_node_at_path(root, path)
    inner = _match_or_false(current)
    if inner is None:
        raise ValueError("Selected path is not applicable for F ∨ p ⇔ p")
    return apply_by_path(root, path, inner)


# Funkcia overí, či je daný uzol tvaru T ∨ α alebo α ∨ T.
# Ak áno, vráti konštantu T.
# Inak vráti None.
def _match_or_true(node: Node):
    if isinstance(node, Or):
        if isinstance(node.left, Const) and node.left.value is True:
            return Const(True)
        if isinstance(node.right, Const) and node.right.value is True:
            return Const(True)
    return None


# Funkcia prejde celý strom formule a nájde všetky miesta,
# na ktorých možno použiť zákon Z9: T ∨ α ↔ T.
# Výsledkom je zoznam návrhov typu Suggestion.
def find_or_true_suggestions(root: Node) -> List[Suggestion]:
    suggestions = []

    # Rekurzívna funkcia walk prechádza strom a na každom uzle skúša,
    # či zodpovedá tvaru pravidla T ∨ α ↔ T.
    def walk(node: Node, path: str):
        if _match_or_true(node):
            suggestions.append(make_suggestion(
                path=path,
                meta=Z9,
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


# Funkcia aplikuje zákon Z9 na uzol stromu určený cestou path.
# Ak sa na danej pozícii nachádza tvar T ∨ α alebo α ∨ T,
# uzol sa nahradí konštantou T.
# Inak sa vyvolá chyba.
def apply_or_true_at_path(root: Node, path: str) -> Node:
    current = get_node_at_path(root, path)
    matched = _match_or_true(current)
    if matched is None:
        raise ValueError("Selected path is not applicable for T ∨ p ⇔ T")
    return apply_by_path(root, path, matched)
