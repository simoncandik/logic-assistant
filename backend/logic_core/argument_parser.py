from __future__ import annotations

from .ast_nodes import Node, Imp
from .parser import parse, ParseError


# Výnimka signalizujúca chybu pri syntaktickej analýze úsudku.
# Používa sa v prípadoch, keď vstupný úsudok nemá očakávaný tvar,
# chýba v ňom symbol úsudku alebo obsahuje neplatné premisy či záver.
class ArgumentParseError(Exception):
    pass


# Zoznam podporovaných symbolov úsudku.
# Parser akceptuje viacero variantov zápisu, aby bol vstup používateľsky flexibilnejší.
TURNSTILE_TOKENS = ("⊨", "|=", "I=", "⊢")


# Pomocná funkcia rozdelí ľavú stranu úsudku na jednotlivé premisy podľa čiarok.
# Rozdelenie sa vykonáva iba na najvyššej úrovni zátvoriek, aby sa neporušili
# vnorené formuly obsahujúce čiarky alebo zložitejšie štruktúry.
def _split_top_level_commas(text: str) -> list[str]:
    # Výsledný zoznam textových reprezentácií premís.
    parts: list[str] = []
    # Priebežne budovaná aktuálna časť.
    current: list[str] = []
    # Počítadlo úrovne vnorenia do zátvoriek.
    depth = 0

    for ch in text:
        # Pri otvorení zátvorky sa zvýši úroveň vnorenia.
        if ch in "([{":
            depth += 1
        # Pri uzavretí zátvorky sa úroveň zníži.
        elif ch in ")]}":
            depth -= 1
            # Ak depth klesne pod nulu, zátvorky sú nesprávne spárované.
            if depth < 0:
                raise ArgumentParseError("Nezodpovedajúce zátvorky v úsudku.")

        # Čiarka rozdeľuje premisy iba na najvyššej úrovni.
        if ch == "," and depth == 0:
            part = "".join(current).strip()
            parts.append(part)
            current = []
            continue

        # Iné znaky sa pridávajú do aktuálne budovanej časti.
        current.append(ch)

    # Ak na konci nie je depth nulové, niektorá zátvorka ostala neuzavretá.
    if depth != 0:
        raise ArgumentParseError("Neuzavreté zátvorky v úsudku.")

    # Po skončení cyklu sa pridá aj posledná časť.
    parts.append("".join(current).strip())
    return parts


# Pomocná funkcia nájde vo vstupnom texte symbol úsudku.
# Vyhľadávanie prebieha iba na najvyššej úrovni zátvoriek,
# aby sa ignorovali prípadné znaky vo vnorených formulách.
def _find_top_level_turnstile(text: str) -> tuple[int, str | None]:
    # Úroveň vnorenia do zátvoriek.
    depth = 0
    # Index aktuálneho znaku.
    i = 0

    while i < len(text):
        ch = text[i]

        # Otváracia zátvorka zvyšuje hĺbku vnorenia.
        if ch in "([{":
            depth += 1
            i += 1
            continue

        # Uzatváracia zátvorka znižuje hĺbku vnorenia.
        if ch in ")]}":
            depth -= 1
            if depth < 0:
                raise ArgumentParseError("Nezodpovedajúce zátvorky v úsudku.")
            i += 1
            continue

        # Symbol úsudku hľadáme iba mimo vnorených zátvoriek.
        if depth == 0:
            for token in TURNSTILE_TOKENS:
                if text.startswith(token, i):
                    return i, token

        i += 1

    # Ak po prejdení textu nie je depth nulové, zátvorky nie sú uzavreté správne.
    if depth != 0:
        raise ArgumentParseError("Neuzavreté zátvorky v úsudku.")

    # Ak sa symbol úsudku nenašiel, vracia sa hodnota signalizujúca neúspech.
    return -1, None


# Funkcia vytvorí výslednú formulu reprezentujúcu úsudok.
# Zoznam premís sa prevedie na zreťazenú implikáciu smerujúcu k záveru.
# Napríklad z premís A, B a záveru C vznikne formula A → (B → C).
def build_argument_formula(premises: list[Node], conclusion: Node) -> Node:
    result = conclusion
    for premise in reversed(premises):
        result = Imp(premise, result)
    return result


# Hlavná funkcia parsera úsudkov.
# Spracuje vstupný text úsudku, rozdelí ho na premisy a záver,
# jednotlivé časti prevedie na AST uzly a následne z nich vytvorí
# výslednú implikačnú formulu.
def parse_argument(text: str) -> Node:
    # Odstránenie nadbytočných medzier na začiatku a konci vstupu.
    raw = text.strip()
    if not raw:
        raise ArgumentParseError("Úsudok je prázdny.")

    # Vyhľadanie symbolu úsudku na najvyššej úrovni.
    idx, token = _find_top_level_turnstile(raw)
    if idx == -1 or token is None:
        raise ArgumentParseError("V úsudku chýba symbol ⊨, |=, I= alebo ⊢.")

    # Rozdelenie vstupu na ľavú stranu s premisami a pravú stranu so záverom.
    left = raw[:idx].strip()
    right = raw[idx + len(token):].strip()

    # Pravá strana úsudku musí obsahovať záver.
    if not right:
        raise ArgumentParseError("Chýba záver úsudku.")

    # Pokus o parsovanie záveru ako formule výrokovej logiky.
    try:
        conclusion_ast = parse(right)
    except ParseError as e:
        raise ArgumentParseError(f"Neplatný záver úsudku: {e}") from e

    # Ak ľavá strana neobsahuje premisy, úsudok sa redukuje iba na záver.
    if not left:
        return conclusion_ast

    # Rozdelenie ľavej strany na jednotlivé premisy.
    premise_texts = _split_top_level_commas(left)

    # Kontrola, či medzi premisami nevznikla prázdna položka.
    if any(not item for item in premise_texts):
        raise ArgumentParseError("Medzi premisami je prázdna položka.")

    # Parsovanie všetkých premís na AST uzly.
    premises: list[Node] = []
    for item in premise_texts:
        try:
            premises.append(parse(item))
        except ParseError as e:
            raise ArgumentParseError(f"Neplatná premisa '{item}': {e}") from e

    # Z parsed premís a záveru sa zostaví výsledná formula reprezentujúca úsudok.
    return build_argument_formula(premises, conclusion_ast)
