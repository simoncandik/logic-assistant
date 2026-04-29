from __future__ import annotations
from .ast_nodes import *


# Výnimka signalizujúca chybu pri syntaktickej analýze vstupnej formule.
# Používa sa v prípadoch, keď vstup nespĺňa očakávanú gramatiku.
class ParseError(Exception):
    pass


# Pomocná trieda pre postupné čítanie vstupného reťazca.
# Lexer zabezpečuje pohyb po texte, preskakovanie medzier
# a rozpoznávanie konkrétnych symbolov alebo reťazcov.
class Lexer:
    def __init__(self, s: str):
        # Pôvodný vstupný reťazec.
        self.s = s
        # Aktuálna pozícia čítania vo vstupnom reťazci.
        self.i = 0

    # Vráti nasledujúcich n znakov od aktuálnej pozície bez posunu ukazovateľa.
    def peek(self, n=1):
        return self.s[self.i:self.i + n]

    # Preskočí všetky medzery a biele znaky od aktuálnej pozície.
    def skip_ws(self):
        while self.i < len(self.s) and self.s[self.i].isspace():
            self.i += 1

    # Pokúsi sa načítať konkrétny text od aktuálnej pozície.
    # Ak sa text zhoduje, posunie ukazovateľ a vráti True.
    # V opačnom prípade ponechá pozíciu bez zmeny a vráti False.
    def eat(self, text: str) -> bool:
        self.skip_ws()
        if self.s.startswith(text, self.i):
            self.i += len(text)
            return True
        return False

    # Overí, či sa parser nachádza na konci vstupu.
    def eof(self) -> bool:
        self.skip_ws()
        return self.i >= len(self.s)


# Hlavná funkcia parsera.
# Zo vstupného textového reťazca vytvorí syntaktický strom formule
# podľa definovanej precedencie logických operátorov.
def parse(s: str) -> Node:
    # Vytvorenie lexer objektu pre spracovanie vstupu.
    lx = Lexer(s)

    # Najvyššia úroveň gramatiky.
    # Parser začína spracovanie na úrovni ekvivalencie.
    def parse_formula() -> Node:
        return parse_iff()

    # Spracovanie ekvivalencie.
    # Ekvivalencia má v tejto implementácii najnižšiu prioritu,
    # preto sa spracováva ako posledná vrstva skladania operátorov.
    def parse_iff() -> Node:
        left = parse_imp()
        while True:
            if lx.eat("<->") or lx.eat("↔") or lx.eat("≡"):
                right = parse_imp()
                left = Iff(left, right)
            else:
                break
        return left

    # Spracovanie implikácie.
    # Implikácia je definovaná ako pravostranné asociatívna,
    # preto sa pravá strana parsuje rekurzívnym volaním parse_imp().
    def parse_imp() -> Node:
        left = parse_or()

        if lx.eat("->") or lx.eat("→") or lx.eat("⊃") or lx.eat("=>"):
            right = parse_imp()
            return Imp(left, right)

        return left

    # Spracovanie disjunkcie.
    # Disjunkcia sa skladá z operandov vyššej priority, teda konjunkcií.
    def parse_or() -> Node:
        left = parse_and()
        while True:
            if lx.eat("|") or lx.eat("v") or lx.eat("∨") or lx.eat("OR") or lx.eat("or"):
                right = parse_and()
                left = Or(left, right)
            else:
                break
        return left

    # Spracovanie konjunkcie.
    # Konjunkcia sa skladá z operandov vyššej priority, teda negácií.
    def parse_and() -> Node:
        left = parse_not()
        while True:
            if lx.eat("&") or lx.eat("^") or lx.eat("∧") or lx.eat("AND") or lx.eat("and"):
                right = parse_not()
                left = And(left, right)
            else:
                break
        return left

    # Spracovanie negácie, zátvoriek a základných atómov.
    # Negácia má najvyššiu prioritu spomedzi logických spojok.
    def parse_not() -> Node:
        # Negácia môže byť zadaná viacerými symbolmi.
        if lx.eat("~") or lx.eat("!") or lx.eat("¬"):
            return Not(parse_not())

        # Podpora okrúhlych zátvoriek.
        if lx.eat("("):
            inside = parse_formula()
            if not lx.eat(")"):
                raise ParseError("expected ')'")
            return inside

        # Podpora hranatých zátvoriek.
        if lx.eat("["):
            inside = parse_formula()
            if not lx.eat("]"):
                raise ParseError("expected ']'")
            return inside

        # Podpora zložených zátvoriek.
        if lx.eat("{"):
            inside = parse_formula()
            if not lx.eat("}"):
                raise ParseError("expected '}'")
            return inside

        # Ak nejde o negáciu ani zátvorkovanú formulu, očakáva sa premenná
        # alebo logická konštanta.
        return parse_var()

    # Spracovanie premennej alebo logickej konštanty.
    # Premenná môže obsahovať písmená, číslice a znak podčiarknutia.
    def parse_var() -> Node:
        lx.skip_ws()
        start = lx.i

        while lx.i < len(lx.s) and (lx.s[lx.i].isalnum() or lx.s[lx.i] == "_"):
            lx.i += 1

        # Ak sa nenačítal žiadny znak, vstup na tejto pozícii nie je platný.
        if lx.i == start:
            raise ParseError(f"unexpected token at position {lx.i + 1}")

        name = lx.s[start:lx.i]

        # Osobitné spracovanie logických konštánt T a F.
        if name == "T":
            return Const(True)
        if name == "F":
            return Const(False)

        # V ostatných prípadoch ide o výrokovú premennú.
        return Var(name=name)

    # Spustenie samotného parsovania od najvyššej úrovne gramatiky.
    node = parse_formula()

    # Po úspešnom spracovaní musí nasledovať koniec vstupu.
    # Ak ostali nespracované znaky, vstup nie je syntakticky korektný.
    if not lx.eof():
        raise ParseError(f"unexpected trailing input at position {lx.i + 1}")

    return node
