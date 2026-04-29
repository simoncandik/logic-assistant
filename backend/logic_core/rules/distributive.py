from __future__ import annotations

from ..ast_nodes import *
from .common import Suggestion, make_suggestion, apply_by_path, get_node_at_path
from .rule_metadata import Z2, Z3


# Tento modul implementuje distributívne zákony:
#   Z2: α ∧ (β ∨ γ) ↔ (α ∧ β) ∨ (α ∧ γ)
#   Z3: α ∨ (β ∧ γ) ↔ (α ∨ β) ∧ (α ∨ γ)
#
# Podporované sú oba smery transformácie:
#   - priamy smer, keď sa spoločná časť rozdistribuuje do dvoch vetiev,
#   - spätný smer, keď sa spoločná časť z dvoch vetiev vytkne.


# Funkcia overí, či daný uzol zodpovedá niektorému z podporovaných
# tvarov distributívneho zákona.
# Ak áno, vráti identifikátor smeru transformácie a trojicu podformúl.
# V opačnom prípade vráti None.
def _match_distributive(node: Node):
    # Priamy smer zákona Z2:
    #   α ∧ (β ∨ γ)  ->  (α ∧ β) ∨ (α ∧ γ)
    # Podporuje sa aj symetrický zápis:
    #   (β ∨ γ) ∧ α
    if isinstance(node, And):
        if isinstance(node.right, Or):
            return ("forward_and_over_or", node.left, node.right.left, node.right.right)
        if isinstance(node.left, Or):
            return ("forward_and_over_or", node.right, node.left.left, node.left.right)

    # Priamy smer zákona Z3:
    #   α ∨ (β ∧ γ)  ->  (α ∨ β) ∧ (α ∨ γ)
    # Podporuje sa aj symetrický zápis:
    #   (β ∧ γ) ∨ α
    if isinstance(node, Or):
        if isinstance(node.right, And):
            return ("forward_or_over_and", node.left, node.right.left, node.right.right)
        if isinstance(node.left, And):
            return ("forward_or_over_and", node.right, node.left.left, node.left.right)

    # Spätný smer zákona Z2:
    #   (a ∧ b) ∨ (a ∧ c)  ->  a ∧ (b ∨ c)
    # Funkcia skúša nájsť spoločnú podformulu v oboch konjunkciách.
    if isinstance(node, Or) and isinstance(node.left, And) and isinstance(node.right, And):
        l1, l2 = node.left.left, node.left.right
        r1, r2 = node.right.left, node.right.right

        if l1 == r1:
            return ("backward_and_over_or", l1, l2, r2)
        if l1 == r2:
            return ("backward_and_over_or", l1, l2, r1)
        if l2 == r1:
            return ("backward_and_over_or", l2, l1, r2)
        if l2 == r2:
            return ("backward_and_over_or", l2, l1, r1)

    # Spätný smer zákona Z3:
    #   (a ∨ b) ∧ (a ∨ c)  ->  a ∨ (b ∧ c)
    # Funkcia skúša nájsť spoločnú podformulu v oboch disjunkciách.
    if isinstance(node, And) and isinstance(node.left, Or) and isinstance(node.right, Or):
        l1, l2 = node.left.left, node.left.right
        r1, r2 = node.right.left, node.right.right

        if l1 == r1:
            return ("backward_or_over_and", l1, l2, r2)
        if l1 == r2:
            return ("backward_or_over_and", l1, l2, r1)
        if l2 == r1:
            return ("backward_or_over_and", l2, l1, r2)
        if l2 == r2:
            return ("backward_or_over_and", l2, l1, r1)

    return None


# Funkcia prejde celý strom formule a nájde všetky miesta,
# na ktorých je možné použiť niektorý z distributívnych zákonov.
# Výsledkom je zoznam návrhov typu Suggestion.
def find_distributive_suggestions(root: Node) -> List[Suggestion]:
    suggestions = []

    # Rekurzívna funkcia walk prechádza strom a pri každom uzle
    # skúša, či zodpovedá niektorému podporovanému distributívnemu tvaru.
    def walk(node: Node, path: str):
        match = _match_distributive(node)
        if match is not None:
            kind, p, q, r = match

            # Podľa typu rozpoznaného tvaru sa vytvorí nová podformula
            # a priradí sa správne metadáto pravidla.
            if kind == "forward_and_over_or":
                rewritten = Or(And(p, q), And(p, r))
                meta = Z2
            elif kind == "forward_or_over_and":
                rewritten = And(Or(p, q), Or(p, r))
                meta = Z3
            elif kind == "backward_and_over_or":
                rewritten = And(p, Or(q, r))
                meta = Z2
            else:
                rewritten = Or(p, And(q, r))
                meta = Z3

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


# Funkcia aplikuje distributívny zákon na konkrétny uzol stromu
# určený cestou path.
# Najprv rozpozná konkrétny tvar, potom vytvorí nový podstrom
# a nahradí ním pôvodný uzol.
# Ak sa na danej pozícii nenachádza podporovaný tvar, vyvolá chybu.
def apply_distributive_at_path(root: Node, path: str) -> Node:
    current = get_node_at_path(root, path)
    match = _match_distributive(current)

    if match is None:
        raise ValueError("Selected path is not applicable for distributivity")

    kind, p, q, r = match

    if kind == "forward_and_over_or":
        new_subtree = Or(And(p, q), And(p, r))
    elif kind == "forward_or_over_and":
        new_subtree = And(Or(p, q), Or(p, r))
    elif kind == "backward_and_over_or":
        new_subtree = And(p, Or(q, r))
    else:
        new_subtree = Or(p, And(q, r))

    return apply_by_path(root, path, new_subtree)
