from __future__ import annotations

from ..ast_nodes import *
from .common import Suggestion, make_suggestion, apply_by_path, get_node_at_path
from .rule_metadata import Z10A, Z10B


# Tento modul implementuje idempotentné zákony:
#   Z10a: α ∧ α ↔ α
#   Z10b: α ∨ α ↔ α
#
# Ak sa na oboch stranách konjunkcie alebo disjunkcie nachádza rovnaká
# podformula, celý výraz je možné zjednodušiť na túto podformulu.


# Funkcia overí, či je daný uzol tvaru α ∧ α alebo α ∨ α.
# Ak áno, vráti vnútornú podformulu α.
# Inak vráti None.
def _match_idempotent(node: Node):
    if isinstance(node, (And, Or)):
        if node.left == node.right:
            return node.left
    return None


# Funkcia prejde celý strom formule a nájde všetky miesta,
# na ktorých možno použiť idempotentný zákon.
# Výsledkom je zoznam návrhov typu Suggestion.
def find_idempotent_suggestions(root: Node) -> List[Suggestion]:
    suggestions = []

    # Rekurzívna funkcia walk prechádza strom a na každom uzle skúša,
    # či zodpovedá tvaru α ∧ α alebo α ∨ α.
    def walk(node: Node, path: str):
        inner = _match_idempotent(node)
        if inner is not None:
            meta = Z10A if isinstance(node, And) else Z10B
            suggestions.append(make_suggestion(
                path=path,
                meta=meta,
                before=str(node),
                after=str(inner),
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


# Funkcia aplikuje idempotentný zákon na uzol stromu určený cestou path.
# Ak sa na danej pozícii nachádza tvar α ∧ α alebo α ∨ α,
# uzol sa nahradí podformulou α.
# Inak sa vyvolá chyba.
def apply_idempotent_at_path(root: Node, path: str) -> Node:
    current = get_node_at_path(root, path)
    inner = _match_idempotent(current)
    if inner is None:
        raise ValueError("Selected path is not applicable for idempotence")
    return apply_by_path(root, path, inner)
