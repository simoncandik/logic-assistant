from __future__ import annotations

from ..ast_nodes import *
from .common import Suggestion, make_suggestion, apply_by_path, get_node_at_path
from .rule_metadata import Z12, Z13, Z14


# Tento modul implementuje pravidlá pracujúce s negáciou:
#   Z12: dvojitá negácia
#   Z13: De Morganov zákon pre negovanú konjunkciu
#   Z14: De Morganov zákon pre negovanú disjunkciu


# Funkcia overí, či má uzol tvar dvojitej negácie ¬¬α.
# Ak áno, vráti vnútorný uzol α.
# V opačnom prípade vráti None.
def _match_double_neg(node: Node):
    if isinstance(node, Not) and isinstance(node.child, Not):
        return node.child.child
    return None


# Funkcia prejde celý strom formule a nájde všetky miesta,
# na ktorých je možné použiť pravidlo dvojitej negácie Z12.
# Výsledkom je zoznam návrhov typu Suggestion.
def find_double_neg_suggestions(root: Node) -> List[Suggestion]:
    suggestions = []

    # Rekurzívna funkcia walk prechádza strom a pri každom uzle
    # skúša, či ide o tvar ¬¬α.
    def walk(node: Node, path: str):
        inner = _match_double_neg(node)
        if inner is not None:
            suggestions.append(make_suggestion(
                path=path,
                meta=Z12,
                before=str(node),
                after=str(inner),
            ))

        # Rekurzívne pokračovanie do podstromov binárnych operátorov.
        if isinstance(node, (And, Or, Imp, Iff)):
            walk(node.left, path + (".left" if path else "left"))
            walk(node.right, path + (".right" if path else "right"))

        # Rekurzívne pokračovanie do vnútorného uzla negácie.
        elif isinstance(node, Not):
            walk(node.child, path + (".child" if path else "child"))

    walk(root, "")
    return suggestions


# Funkcia aplikuje pravidlo dvojitej negácie Z12
# na konkrétne miesto v strome určené cestou path.
# Ak sa na danej pozícii nenachádza tvar ¬¬α, vyvolá chybu.
def apply_double_neg_at_path(root: Node, path: str) -> Node:
    current = get_node_at_path(root, path)
    inner = _match_double_neg(current)
    if inner is None:
        raise ValueError("Selected path is not a double negation")
    return apply_by_path(root, path, inner)


# Funkcia overí, či má uzol niektorý z tvarov patriacich
# pod De Morganove zákony.
# Podporované sú oba smery:
#   ¬(α ∧ β)  ↔  (¬α ∨ ¬β)
#   ¬(α ∨ β)  ↔  (¬α ∧ ¬β)
# Ak je tvar rozpoznaný, funkcia vráti identifikátor smeru a dvojicu podformúl.
# V opačnom prípade vráti None.
def _match_de_morgan(node: Node):
    # Priamy smer:
    #   ¬(α ∧ β)  ->  ¬α ∨ ¬β
    #   ¬(α ∨ β)  ->  ¬α ∧ ¬β
    if isinstance(node, Not):
        inner = node.child
        if isinstance(inner, And):
            return ("forward_and", inner.left, inner.right)
        if isinstance(inner, Or):
            return ("forward_or", inner.left, inner.right)

    # Spätný smer:
    #   ¬α ∨ ¬β  ->  ¬(α ∧ β)
    if isinstance(node, Or) and isinstance(node.left, Not) and isinstance(node.right, Not):
        return ("backward_and", node.left.child, node.right.child)

    # Spätný smer:
    #   ¬α ∧ ¬β  ->  ¬(α ∨ β)
    if isinstance(node, And) and isinstance(node.left, Not) and isinstance(node.right, Not):
        return ("backward_or", node.left.child, node.right.child)

    return None


# Funkcia prejde celý strom formule a nájde všetky miesta,
# na ktorých je možné použiť De Morganove zákony Z13 alebo Z14.
# Výsledkom je zoznam návrhov typu Suggestion.
def find_de_morgan_suggestions(root: Node) -> List[Suggestion]:
    suggestions = []

    # Rekurzívna funkcia walk prechádza strom a pri každom uzle
    # skúša, či zodpovedá niektorému tvaru De Morganových zákonov.
    def walk(node: Node, path: str):
        match = _match_de_morgan(node)
        if match is not None:
            kind, p, q = match

            # Výber správneho výsledného tvaru a metadát pravidla
            # podľa rozpoznaného smeru transformácie.
            if kind == "forward_and":
                rewritten = Or(Not(p), Not(q))
                meta = Z13
            elif kind == "forward_or":
                rewritten = And(Not(p), Not(q))
                meta = Z14
            elif kind == "backward_and":
                rewritten = Not(And(p, q))
                meta = Z13
            else:
                rewritten = Not(Or(p, q))
                meta = Z14

            suggestions.append(make_suggestion(
                path=path,
                meta=meta,
                before=str(node),
                after=str(rewritten),
            ))

        # Rekurzívne pokračovanie do podstromov binárnych operátorov.
        if isinstance(node, (And, Or, Imp, Iff)):
            walk(node.left, path + (".left" if path else "left"))
            walk(node.right, path + (".right" if path else "right"))

        # Rekurzívne pokračovanie do vnútorného uzla negácie.
        elif isinstance(node, Not):
            walk(node.child, path + (".child" if path else "child"))

    walk(root, "")
    return suggestions


# Funkcia aplikuje príslušný De Morganov zákon na miesto v strome
# určené cestou path.
# Najprv rozpozná konkrétny tvar, následne vytvorí nový podstrom
# a nahradí ním pôvodný uzol.
# Ak uzol nezodpovedá žiadnemu podporovanému tvaru, vyvolá chybu.
def apply_de_morgan_at_path(root: Node, path: str) -> Node:
    current = get_node_at_path(root, path)
    match = _match_de_morgan(current)

    if match is None:
        raise ValueError("Selected path is not applicable for De Morgan")

    kind, p, q = match

    if kind == "forward_and":
        new_subtree = Or(Not(p), Not(q))
    elif kind == "forward_or":
        new_subtree = And(Not(p), Not(q))
    elif kind == "backward_and":
        new_subtree = Not(And(p, q))
    else:
        new_subtree = Not(Or(p, q))

    return apply_by_path(root, path, new_subtree)
