from __future__ import annotations

# Import triedy FastAPI a middleware pre povolenie komunikácie medzi frontendom a backendom.
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import triedy BaseModel pre definovanie dátových modelov API požiadaviek a odpovedí.
from pydantic import BaseModel

# Import typov používaných v anotáciách.
from typing import List, Literal

# Import parsera formúl a výnimky signalizujúcej chybu pri parsovaní formule.
from logic_core.parser import parse, ParseError

# Import parsera úsudkov a výnimky signalizujúcej chybu pri parsovaní úsudku.
from logic_core.argument_parser import parse_argument, ArgumentParseError

# Import slovníkov s metadátami pravidiel a mapovania textového označenia pravidla na jeho kód.
from logic_core.rules import RULES_BY_CODE, RULE_CODE_BY_LABEL

# Import triedy konštanty, aby bolo možné rozpoznať koncové tvary T a F.
from logic_core.ast_nodes import Const

# Import funkcií na vyhľadávanie aplikovateľných pravidiel,
# funkcií na aplikovanie pravidiel na zvolenej pozícii v strome
# a pomocnej funkcie na normalizovaný výpis formule.
from logic_core.rules import (
    find_imp_to_or_suggestions,
    find_double_neg_suggestions,
    find_de_morgan_suggestions,
    find_distributive_suggestions,
    find_and_true_suggestions,
    find_and_false_suggestions,
    find_or_false_suggestions,
    find_or_true_suggestions,
    find_idempotent_suggestions,
    find_or_complement_suggestions,
    find_and_complement_suggestions,
    find_commutative_suggestions,
    find_iff_definition_suggestions,
    find_associative_suggestions,

    apply_imp_to_or_at_path,
    apply_double_neg_at_path,
    apply_de_morgan_at_path,
    apply_distributive_at_path,
    apply_and_true_at_path,
    apply_and_false_at_path,
    apply_or_false_at_path,
    apply_or_true_at_path,
    apply_idempotent_at_path,
    apply_or_complement_at_path,
    apply_and_complement_at_path,
    apply_commutative_at_path,
    apply_iff_definition_at_path,
    apply_associative_at_path,

    pretty
)

# Vytvorenie objektu webovej aplikácie FastAPI.
app = FastAPI(title="Interactive Logic Assistant (MVP)")

# Povolenie CORS komunikácie, aby frontend otvorený v prehliadači
# mohol odosielať požiadavky na backend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Dátový model požiadavky pre endpoint /suggest.
# Používateľ zadáva text vstupu a určuje, či ide o formulu alebo úsudok.
class SuggestRequest(BaseModel):
    formula: str
    input_mode: Literal["formula", "argument"] = "formula"


# Dátový model jednej navrhovanej úpravy formule.
# Obsahuje informácie o pravidle, pôvodnom a novom tvare podformuly
# aj informáciu o tom, či by daný krok ukončil dokazovanie.
class SuggestionDTO(BaseModel):
    path: str
    rule_code: str
    rule_name: str
    rule_form: str
    rule: str
    before: str
    after: str
    finishes_proof: bool = False
    final_value: str | None = None
    final_kind: str | None = None
    final_message: str | None = None


# Dátový model odpovede endpointu /suggest.
# Okrem zoznamu návrhov obsahuje aj normalizovaný tvar formule,
# informáciu o ukončení dokazovania a prípadný prevod úsudku na formulu.
class SuggestResponse(BaseModel):
    ok: bool
    ast: str | None = None
    suggestions: List[SuggestionDTO] = []
    is_finished: bool = False
    final_value: str | None = None
    final_kind: str | None = None
    final_message: str | None = None
    converted_from_argument: bool = False
    conversion_message: str | None = None
    error: str | None = None


# Dátový model požiadavky pre endpoint /apply.
# Obsahuje aktuálnu formulu, pozíciu podformuly a identifikáciu pravidla.
class ApplyRequest(BaseModel):
    formula: str
    path: str
    rule: str | None = None
    rule_code: str | None = None


# Dátový model odpovede endpointu /apply.
# Vracia nový tvar formule a informáciu o prípadnom ukončení dokazovania.
class ApplyResponse(BaseModel):
    ok: bool
    result: str | None = None
    is_finished: bool = False
    final_value: str | None = None
    final_kind: str | None = None
    final_message: str | None = None
    error: str | None = None


# Dátový model požiadavky pre endpoint /check-step.
# Používateľ zadáva aktuálny a nasledujúci tvar formule.
class CheckStepRequest(BaseModel):
    current_formula: str
    next_formula: str


# Dátový model odpovede endpointu /check-step.
# Obsahuje výsledok kontroly kroku, rozpoznané pravidlá,
# normalizované tvary formúl a informáciu o stave dokazovania.
class CheckStepResponse(BaseModel):
    ok: bool
    valid_step: bool = False
    matched_rules: List[SuggestionDTO] = []
    normalized_current: str | None = None
    normalized_next: str | None = None
    is_finished: bool = False
    final_value: str | None = None
    final_kind: str | None = None
    final_message: str | None = None
    message: str | None = None
    error: str | None = None


# Pomocná funkcia prevedie interný objekt návrhu úpravy na dátový model API odpovede.
def suggestion_to_dto(s):
    status = get_formula_status_from_text(s.after)

    return SuggestionDTO(
        path=s.path,
        rule_code=s.rule_code,
        rule_name=s.rule_name,
        rule_form=s.rule_form,
        rule=s.rule,
        before=s.before,
        after=s.after,
        finishes_proof=status["finishes_proof"],
        final_value=status["final_value"],
        final_kind=status["final_kind"],
        final_message=status["final_message"],
    )


# Dátový model metadát jedného zákona ekvivalencie.
# Používa sa pri generovaní tabuľky zákonov na stránke vzorových príkladov.
class RuleInfoDTO(BaseModel):
    code: str
    name: str
    form: str
    label: str


# Funkcia zisťuje, či sa formula nachádza v koncovom tvare.
# Ak je výsledkom T alebo F, vráti aj typ výsledku a správu pre používateľa.
def get_formula_status(ast):
    if isinstance(ast, Const):
        if ast.value is True:
            return {
                "is_finished": True,
                "final_value": "T",
                "final_kind": "tautológia",
                "final_message": "Gratulujem, formula sa upravila na T. Dokazovanie je ukončené a výsledok je tautológia."
            }
        return {
            "is_finished": True,
            "final_value": "F",
            "final_kind": "kontradikcia",
            "final_message": "Gratulujem, formula sa upravila na F. Dokazovanie je ukončené a výsledok je kontradikcia."
        }

    return {
        "is_finished": False,
        "final_value": None,
        "final_kind": None,
        "final_message": None
    }


# Funkcia zisťuje stav formule podľa jej textového tvaru.
# Používa sa najmä pri návrhoch krokov, kde ešte nie je potrebné pracovať s AST objektom.
def get_formula_status_from_text(formula_text: str):
    if formula_text == "T":
        return {
            "finishes_proof": True,
            "final_value": "T",
            "final_kind": "tautológia",
            "final_message": "Použitím tejto úpravy sa dostanete na koniec dokazovania. Výsledkom bude tautológia."
        }

    if formula_text == "F":
        return {
            "finishes_proof": True,
            "final_value": "F",
            "final_kind": "kontradikcia",
            "final_message": "Použitím tejto úpravy sa dostanete na koniec dokazovania. Výsledkom bude kontradikcia."
        }

    return {
        "finishes_proof": False,
        "final_value": None,
        "final_kind": None,
        "final_message": None
    }


# Funkcia spracuje používateľský vstup podľa zvoleného režimu.
# Pri formule sa vykoná priame parsovanie.
# Pri úsudku sa vykoná parsovanie úsudku a jeho prevod na implikačnú formulu.
def parse_entry_input(text: str, input_mode: str):
    if input_mode == "formula":
        ast = parse(text)
        return ast, False, None

    if input_mode == "argument":
        ast = parse_argument(text)
        conversion_message = f"Zadaný úsudok bol prevedený na formulu {pretty(ast)}."
        return ast, True, conversion_message

    raise ValueError("Neznámy typ vstupu.")


# Funkcia zhromaždí všetky aplikovateľné návrhy úprav nad zadanou formulou.
# Jednotlivé pravidlá sa vyhodnocujú postupne a ich návrhy sa spoja do jedného zoznamu.
def collect_suggestions(ast):
    suggestions = []
    suggestions += find_imp_to_or_suggestions(ast)
    suggestions += find_double_neg_suggestions(ast)
    suggestions += find_de_morgan_suggestions(ast)
    suggestions += find_distributive_suggestions(ast)
    suggestions += find_and_true_suggestions(ast)
    suggestions += find_and_false_suggestions(ast)
    suggestions += find_or_false_suggestions(ast)
    suggestions += find_or_true_suggestions(ast)
    suggestions += find_idempotent_suggestions(ast)
    suggestions += find_or_complement_suggestions(ast)
    suggestions += find_and_complement_suggestions(ast)
    suggestions += find_commutative_suggestions(ast)
    suggestions += find_iff_definition_suggestions(ast)
    suggestions += find_associative_suggestions(ast)
    return suggestions


# Funkcia vytvorí mapovanie medzi kódom pravidla a funkciou,
# ktorá vie dané pravidlo aplikovať na vybranej pozícii v strome formule.
def get_rule_dispatch():
    return {
        "Z1": apply_imp_to_or_at_path,
        "Z12": apply_double_neg_at_path,
        "Z13": apply_de_morgan_at_path,
        "Z14": apply_de_morgan_at_path,
        "Z2": apply_distributive_at_path,
        "Z3": apply_distributive_at_path,
        "Z6": apply_and_true_at_path,
        "Z7": apply_and_false_at_path,
        "Z8": apply_or_false_at_path,
        "Z9": apply_or_true_at_path,
        "Z10a": apply_idempotent_at_path,
        "Z10b": apply_idempotent_at_path,
        "Z4": apply_or_complement_at_path,
        "Z5": apply_and_complement_at_path,
        "Z11a": apply_commutative_at_path,
        "Z11b": apply_commutative_at_path,
        "Z15": apply_iff_definition_at_path,
        "Z16a": apply_associative_at_path,
        "Z16b": apply_associative_at_path,
    }


# Endpoint /suggest prijme formulu alebo úsudok,
# prevedie vstup na internú stromovú reprezentáciu,
# vyhodnotí stav formule a vráti všetky aplikovateľné návrhy ďalších krokov.
@app.post("/suggest", response_model=SuggestResponse)
def suggest(req: SuggestRequest):
    try:
        ast, converted_from_argument, conversion_message = parse_entry_input(req.formula, req.input_mode)
    except ParseError as e:
        return SuggestResponse(ok=False, error=f"Parse error: {e}")
    except ArgumentParseError as e:
        return SuggestResponse(ok=False, error=f"Chyba v úsudku: {e}")
    except Exception as e:
        return SuggestResponse(ok=False, error=str(e))

    status = get_formula_status(ast)

    suggestions = []
    if not status["is_finished"]:
        suggestions = collect_suggestions(ast)

    return SuggestResponse(
        ok=True,
        ast=pretty(ast),
        suggestions=[suggestion_to_dto(s) for s in suggestions],
        is_finished=status["is_finished"],
        final_value=status["final_value"],
        final_kind=status["final_kind"],
        final_message=status["final_message"],
        converted_from_argument=converted_from_argument,
        conversion_message=conversion_message,
    )


# Endpoint /apply aplikuje vybrané pravidlo na zadanú podformulu
# a vráti nový normalizovaný tvar výslednej formule.
@app.post("/apply", response_model=ApplyResponse)
def apply(req: ApplyRequest):
    try:
        ast = parse(req.formula)
        rule_dispatch = get_rule_dispatch()

        # Ak klient neposlal priamo kód pravidla, pokúsi sa získať ho z textového označenia pravidla.
        rule_code = req.rule_code
        if rule_code is None and req.rule is not None:
            rule_code = RULE_CODE_BY_LABEL.get(req.rule)

        if rule_code not in rule_dispatch:
            return ApplyResponse(ok=False, error=f"Unknown rule: {req.rule or req.rule_code}")

        new_ast = rule_dispatch[rule_code](ast, req.path)
        status = get_formula_status(new_ast)

        return ApplyResponse(
            ok=True,
            result=pretty(new_ast),
            is_finished=status["is_finished"],
            final_value=status["final_value"],
            final_kind=status["final_kind"],
            final_message=status["final_message"],
        )

    except ParseError as e:
        return ApplyResponse(ok=False, error=f"Parse error: {e}")
    except Exception as e:
        return ApplyResponse(ok=False, error=str(e))


# Endpoint /check-step overí, či používateľom zadaný nasledujúci krok
# zodpovedá niektorej podporovanej jednokrokovej ekvivalentnej úprave.
@app.post("/check-step", response_model=CheckStepResponse)
def check_step(req: CheckStepRequest):
    try:
        current_ast = parse(req.current_formula)
        next_ast = parse(req.next_formula)

        normalized_current = pretty(current_ast)
        normalized_next = pretty(next_ast)

        # Ak sa aktuálna a nasledujúca formula nelíšia,
        # nejde o platný krok úpravy.
        if current_ast == next_ast:
            return CheckStepResponse(
                ok=True,
                valid_step=False,
                normalized_current=normalized_current,
                normalized_next=normalized_next,
                message="Nebola vykonaná žiadna zmena formule."
            )

        suggestions = collect_suggestions(current_ast)
        rule_dispatch = get_rule_dispatch()

        matches: List[SuggestionDTO] = []

        # Pre každý navrhnutý krok sa skúsi jeho reálna aplikácia.
        # Ak výsledok zodpovedá používateľom zadanej formule,
        # krok sa považuje za korektný.
        for s in suggestions:
            apply_fn = rule_dispatch.get(s.rule_code)
            if apply_fn is None:
                continue

            try:
                candidate_ast = apply_fn(current_ast, s.path)
            except Exception:
                continue

            if candidate_ast == next_ast:
                status = get_formula_status_from_text(pretty(candidate_ast))

                matches.append(SuggestionDTO(
                    path=s.path,
                    rule_code=s.rule_code,
                    rule_name=s.rule_name,
                    rule_form=s.rule_form,
                    rule=s.rule,
                    before=s.before,
                    after=pretty(candidate_ast),
                    finishes_proof=status["finishes_proof"],
                    final_value=status["final_value"],
                    final_kind=status["final_kind"],
                    final_message=status["final_message"],
                ))

        # Ak sa nenašla žiadna zhoda, krok nie je podporovanou jednokrokovou úpravou.
        if not matches:
            return CheckStepResponse(
                ok=True,
                valid_step=False,
                normalized_current=normalized_current,
                normalized_next=normalized_next,
                message="Zadaný krok nezodpovedá žiadnej podporovanej jednokrokovej ekvivalentnej úprave."
            )

        status = get_formula_status(next_ast)

        return CheckStepResponse(
            ok=True,
            valid_step=True,
            matched_rules=matches,
            normalized_current=normalized_current,
            normalized_next=normalized_next,
            is_finished=status["is_finished"],
            final_value=status["final_value"],
            final_kind=status["final_kind"],
            final_message=status["final_message"],
            message="Krok je správny."
        )

    except ParseError as e:
        return CheckStepResponse(ok=False, error=f"Parse error: {e}")
    except Exception as e:
        return CheckStepResponse(ok=False, error=str(e))


# Endpoint /rules-meta vracia metadáta všetkých podporovaných pravidiel.
# Tieto údaje využíva frontend napríklad pri generovaní tabuľky zákonov.
@app.get("/rules-meta", response_model=List[RuleInfoDTO])
def rules_meta():
    return [
        RuleInfoDTO(
            code=rule.code,
            name=rule.name,
            form=rule.form,
            label=rule.label,
        )
        for rule in RULES_BY_CODE.values()
    ]


# Jednoduchý testovací endpoint na overenie, že backend beží správne.
@app.get("/health")
def health():
    return {"ok": True}
