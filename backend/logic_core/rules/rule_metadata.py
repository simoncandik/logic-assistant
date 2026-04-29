from __future__ import annotations
from dataclasses import dataclass


# Trieda RuleMeta reprezentuje metadáta jedného zákona ekvivalencie.
# Každý zákon má svoj kód, názov a formálny tvar.
@dataclass(frozen=True)
class RuleMeta:
    code: str
    name: str
    form: str

    # Vlastnosť label vytvára jednotný textový zápis zákona.
    # Tento zápis sa používa najmä vo frontende a pri mapovaní pravidiel.
    @property
    def label(self) -> str:
        return f"({self.code}) {self.name}: {self.form}"


# Definícia implikácie.
Z1 = RuleMeta("Z1", "Definícia implikácie", "(α → β) ↔ (¬α ∨ β)")

# Distributívne zákony.
Z2 = RuleMeta("Z2", "Distributívny zákon", "(α ∧ (β ∨ γ)) ↔ ((α ∧ β) ∨ (α ∧ γ))")
Z3 = RuleMeta("Z3", "Distributívny zákon", "(α ∨ (β ∧ γ)) ↔ ((α ∨ β) ∧ (α ∨ γ))")

# Komplementárne zákony.
Z4 = RuleMeta("Z4", "Komplementárny zákon", "(α ∨ ¬α) ↔ T")
Z5 = RuleMeta("Z5", "Komplementárny zákon", "(α ∧ ¬α) ↔ F")

# Zákony s logickými konštantami.
Z6 = RuleMeta("Z6", "Zákon s konštantou", "(T ∧ α) ↔ α")
Z7 = RuleMeta("Z7", "Zákon s konštantou", "(F ∧ α) ↔ F")
Z8 = RuleMeta("Z8", "Zákon s konštantou", "(F ∨ α) ↔ α")
Z9 = RuleMeta("Z9", "Zákon s konštantou", "(T ∨ α) ↔ T")

# Zákony idempotencie.
Z10A = RuleMeta("Z10a", "Idempotencia", "(α ∧ α) ↔ α")
Z10B = RuleMeta("Z10b", "Idempotencia", "(α ∨ α) ↔ α")

# Komutatívne zákony.
Z11A = RuleMeta("Z11a", "Komutatívny zákon", "(α ∧ β) ↔ (β ∧ α)")
Z11B = RuleMeta("Z11b", "Komutatívny zákon", "(α ∨ β) ↔ (β ∨ α)")

# Dvojitá negácia.
Z12 = RuleMeta("Z12", "Dvojitá negácia", "¬¬α ↔ α")

# De Morganove zákony.
Z13 = RuleMeta("Z13", "De Morganov zákon", "¬(α ∧ β) ↔ (¬α ∨ ¬β)")
Z14 = RuleMeta("Z14", "De Morganov zákon", "¬(α ∨ β) ↔ (¬α ∧ ¬β)")

# Definícia ekvivalencie.
Z15 = RuleMeta("Z15", "Definícia ekvivalencie", "(α ↔ β) ↔ ((α → β) ∧ (β → α))")

# Asociatívne zákony.
Z16A = RuleMeta("Z16a", "Asociatívny zákon", "((α ∧ β) ∧ γ) ↔ (α ∧ (β ∧ γ))")
Z16B = RuleMeta("Z16b", "Asociatívny zákon", "((α ∨ β) ∨ γ) ↔ (α ∨ (β ∨ γ))")

# Zoznam ALL_RULES obsahuje všetky podporované zákony v poradí,
# v akom sa majú ďalej spracúvať alebo zobrazovať.
ALL_RULES = [
    Z1,
    Z2, Z3,
    Z4, Z5,
    Z6, Z7, Z8, Z9,
    Z10A, Z10B,
    Z11A, Z11B,
    Z12,
    Z13, Z14,
    Z15,
    Z16A, Z16B,
]

# Slovník RULES_BY_CODE umožňuje rýchle vyhľadanie metadát zákona podľa jeho kódu.
RULES_BY_CODE = {rule.code: rule for rule in ALL_RULES}

# Slovník RULE_CODE_BY_LABEL slúži na spätné mapovanie úplného textového označenia
# zákona na jeho interný kód.
RULE_CODE_BY_LABEL = {rule.label: rule.code for rule in ALL_RULES}
