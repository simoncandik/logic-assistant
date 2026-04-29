from __future__ import annotations
from typing import List, Optional, Tuple

from ..ast_nodes import *
from .common import Suggestion, make_suggestion, apply_by_path, get_node_at_path
from .rule_metadata import Z1


# Tento modul implementuje pravidlo Z1 – definíciu implikácie.
# Umožňuje pracovať v oboch smeroch:
#   (α → β) ↔ (¬α ∨ β)


# Funkcia overí, či má uzol tvar implikácie α → β.
# Ak áno, vráti dvojicu ľavá a pravá strana implikácie.
# V opačnom prípade vráti None.
def _match_imp_forward(node: Node) -> Optional[Tuple[Node, Node]]:
    if isinstance(node, Imp):
        return node.left, node.right
    return None


# Funkcia overí, či má uzol tvar disjunkcie ¬α ∨ β.
# Ak áno, vráti dvojicu α a β, aby bolo možné tento tvar
# spätne prepísať na implikáciu α → β.
# V opačnom prípade vráti None.
def _match_imp_backward(node: Node) -> Optional[Tuple[Node, Node]]:
    if isinstance(node, Or) and isinstance(node.left, Not):
        return node.left.child, node.right
    return None


# Funkcia vytvorí nový uzol zodpovedajúci prepisu implikácie
# α → β na disjunkciu ¬α ∨ β.
def _apply_imp_to_or(left: Node, right: Node) -> Node:
    return Or(Not(left), right)


# Funkcia vytvorí nový uzol zodpovedajúci spätnému prepisu
# disjunkcie ¬α ∨ β na implikáciu α → β.
def _apply_or_to_imp(left: Node, right: Node) -> Node:
    return Imp(left, right)


# Funkcia prejde celý strom formule a nájde všetky miesta,
# na ktorých je možné použiť pravidlo Z1.
# Výsledkom je zoznam návrhov typu Suggestion.
def find_imp_to_or_suggestions(root: Node) -> List[Suggestion]:
    out: List[Suggestion] = []

    # Rekurzívna funkcia walk prechádza strom a pri každom uzle
    # skúša oba smery pravidla definície implikácie.
    def walk(node: Node, path: str):
        # Pokus o nájdenie tvaru α → β.
        m1 = _match_imp_forward(node)
        if m1 is not None:
            L, R = m1
            out.append(make_suggestion(
                path=path,
                meta=Z1,
                before=str(node),
                after=str(_apply_imp_to_or(L, R))
            ))

        # Pokus o nájdenie tvaru ¬α ∨ β.
        m2 = _match_imp_backward(node)
        if m2 is not None:
            L, R = m2
            out.append(make_suggestion(
                path=path,
                meta=Z1,
                before=str(node),
                after=str(_apply_or_to_imp(L, R))
            ))

        # Rekurzívne pokračovanie do podstromov binárnych operátorov.
        if isinstance(node, (And, Or, Imp, Iff)):
            walk(node.left, path + (".left" if path else "left"))
            walk(node.right, path + (".right" if path else "right"))

        # Rekurzívne pokračovanie do vnútorného uzla negácie.
        elif isinstance(node, Not):
            walk(node.child, path + (".child" if path else "child"))

    walk(root, "")
    return out


# Funkcia aplikuje pravidlo Z1 na konkrétne miesto v strome určené cestou path.
# Najprv získa uzol na danej pozícii, potom skúsi oba možné smery pravidla.
# Ak ani jeden tvar nezodpovedá, vyvolá chybu.
def apply_imp_to_or_at_path(root: Node, path: str) -> Node:
    current = get_node_at_path(root, path)

    # Priamy smer: α → β  na  ¬α ∨ β
    m1 = _match_imp_forward(current)
    if m1 is not None:
        left, right = m1
        return apply_by_path(root, path, _apply_imp_to_or(left, right))

    # Spätný smer: ¬α ∨ β  na  α → β
    m2 = _match_imp_backward(current)
    if m2 is not None:
        left, right = m2
        return apply_by_path(root, path, _apply_or_to_imp(left, right))

    raise ValueError("Selected path is not applicable for implication equivalence")
