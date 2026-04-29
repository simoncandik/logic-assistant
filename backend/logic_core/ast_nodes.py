from __future__ import annotations

from dataclasses import dataclass
from typing import List


# Základná abstraktná trieda pre všetky uzly syntaktického stromu formule.
# Každý konkrétny typ uzla z nej dedí a podľa potreby prepisuje metódu
# children(), ktorá vracia jeho priamych potomkov v strome.
@dataclass(frozen=True)
class Node:
    def children(self) -> List['Node']:
        return []


# Uzol reprezentujúci výrokovú premennú, napríklad p, q alebo r.
# Uchováva iba názov premennej.
@dataclass(frozen=True)
class Var(Node):
    name: str

    # Reťazcová reprezentácia premennej je priamo jej názov.
    def __str__(self) -> str:
        return self.name


# Uzol reprezentujúci negáciu formule.
# Obsahuje jediného potomka, ktorým je negovaná podformula.
@dataclass(frozen=True)
class Not(Node):
    child: Node

    # Negácia má práve jedného potomka.
    def children(self) -> List['Node']:
        return [self.child]

    # Pri prevode na text sa zátvorky pridávajú len vtedy, keď je to potrebné
    # na zachovanie jednoznačnosti zápisu.
    def __str__(self) -> str:
        c = self.child
        if isinstance(c, (Var, Not)):
            return f"¬{c}"
        return f"¬({c})"


# Uzol reprezentujúci konjunkciu dvoch podformúl.
@dataclass(frozen=True)
class And(Node):
    left: Node
    right: Node

    # Konjunkcia má dvoch potomkov: ľavú a pravú podformulu.
    def children(self) -> List['Node']:
        return [self.left, self.right]

    # Pri výpise sa zátvorky pridávajú iba okolo zložitejších podformúl,
    # aby bol výsledný zápis čitateľný a zároveň jednoznačný.
    def __str__(self) -> str:
        l = f"{self.left}" if isinstance(self.left, (Var, Not)) else f"({self.left})"
        r = f"{self.right}" if isinstance(self.right, (Var, Not)) else f"({self.right})"
        return f"{l} ∧ {r}"


# Uzol reprezentujúci disjunkciu dvoch podformúl.
@dataclass(frozen=True)
class Or(Node):
    left: Node
    right: Node

    # Disjunkcia má dvoch potomkov: ľavú a pravú podformulu.
    def children(self) -> List['Node']:
        return [self.left, self.right]

    # Formátovanie rešpektuje potrebu zátvoriek pri zložitejších podformulách.
    def __str__(self) -> str:
        l = f"{self.left}" if isinstance(self.left, (Var, Not)) else f"({self.left})"
        r = f"{self.right}" if isinstance(self.right, (Var, Not)) else f"({self.right})"
        return f"{l} ∨ {r}"


# Uzol reprezentujúci implikáciu dvoch podformúl.
@dataclass(frozen=True)
class Imp(Node):
    left: Node
    right: Node

    # Implikácia má dvoch potomkov: antecedent a konsekvent.
    def children(self) -> List['Node']:
        return [self.left, self.right]

    # Pri textovej reprezentácii sa v prípade potreby dopĺňajú zátvorky.
    def __str__(self) -> str:
        l = f"{self.left}" if isinstance(self.left, (Var, Not)) else f"({self.left})"
        r = f"{self.right}" if isinstance(self.right, (Var, Not)) else f"({self.right})"
        return f"{l} → {r}"


# Uzol reprezentujúci ekvivalenciu dvoch podformúl.
@dataclass(frozen=True)
class Iff(Node):
    left: Node
    right: Node

    # Ekvivalencia má dvoch potomkov: ľavú a pravú stranu ekvivalencie.
    def children(self) -> List['Node']:
        return [self.left, self.right]

    # Pri výpise sa používajú zátvorky len tam, kde sú potrebné.
    def __str__(self) -> str:
        l = f"{self.left}" if isinstance(self.left, (Var, Not)) else f"({self.left})"
        r = f"{self.right}" if isinstance(self.right, (Var, Not)) else f"({self.right})"
        return f"{l} ↔ {r}"


# Uzol reprezentujúci logickú konštantu.
# Hodnota True zodpovedá konštante T a hodnota False konštante F.
@dataclass(frozen=True)
class Const(Node):
    value: bool

    # Textová reprezentácia konštanty používa symboly T a F.
    def __str__(self) -> str:
        return "T" if self.value else "F"
