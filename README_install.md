# Interaktívny nástroj pre dokazovanie vo výrokovej logike – inštalácia a spustenie

Tento dokument popisuje inštaláciu a spustenie projektu **logic-assistant** na inom zariadení.

> **Testované na:** Windows  
> **Python verzia:** 3.12.0

## 1. Požiadavky

Pred spustením projektu je potrebné mať nainštalované:

- **Python 3.12.0** alebo kompatibilnú verziu Python 3.12
- **pip**
- webový prehliadač

Projekt pozostáva z dvoch častí:

- **backend** – serverová časť aplikácie vo FastAPI
- **frontend** – klientská časť aplikácie v HTML, CSS a JavaScript

## 2. Štruktúra projektu

Predpokladaná štruktúra projektu:

```text
logic-assistant/
├── README_install.md
├── README_usage.md
├── requirements.txt
├── backend/
│   ├── main.py
│   └── logic_core/
│       ├── __init__.py
│       ├── argument_parser.py
│       ├── ast_nodes.py
│       ├── parser.py
│       └── rules/
│           ├── __init__.py
│           ├── associative.py
│           ├── common.py
│           ├── commutative.py
│           ├── complement.py
│           ├── constants.py
│           ├── distributive.py
│           ├── equivalence.py
│           ├── idempotence.py
│           ├── implication.py
│           ├── negation.py
│           └── rule_metadata.py
└── frontend/
    ├── index.html
    ├── guided.html
    ├── guided.js
    ├── manual.html
    ├── manual.js
    ├── examples.html
    ├── examples.js
    └── style.css
```

## 3. Otvorenie terminálu v koreňovom priečinku projektu

Presuňte sa do koreňového priečinka projektu:

```powershell
cd <cesta k projektu>
```

## 4. Vytvorenie virtuálneho prostredia

Ak ešte nie je vytvorené virtuálne prostredie, vytvorte ho príkazom:

```powershell
python -m venv .venv
```

alebo

```powershell
py -m venv .venv
```

## 5. Aktivácia virtuálneho prostredia

Vo Windows PowerShell:

```powershell
.\.venv\Scripts\activate
```

Po aktivácii by sa mal na začiatku riadku zobraziť text `(.venv)`.

## 6. Inštalácia závislostí

V koreňovom priečinku projektu nainštalujte všetky potrebné balíky:

```powershell
pip install -r requirements.txt
```

Ak súbor `requirements.txt` ešte nie je uložený v koreňovom priečinku projektu, skopírujte ho tam pred spustením uvedeného príkazu.

## 7. Spustenie backendu

Backend sa spúšťa z priečinka `backend`.

```powershell
cd .\backend\
uvicorn main:app --reload --port 8000
```

Po úspešnom spustení by sa mala v termináli zobraziť informácia podobná tejto:

```text
Uvicorn running on http://127.0.0.1:8000
```

Backend nechajte počas používania aplikácie spustený.

## 8. Spustenie frontendu

Otvorte druhý terminál alebo Prieskumník súborov a prejdite do priečinka `frontend`.

```powershell
cd .\frontend
```

Následne otvorte súbor `index.html` v prehliadači. Možnosti sú napríklad:

- dvojklik na `index.html`
- pravé tlačidlo myši -> **Otvoriť v programe** -> webový prehliadač
- zadanie lokálnej cesty k súboru do prehliadača

## 9. Používanie aplikácie

Po otvorení `index.html` a spustení backendu je možné aplikáciu používať v prehliadači.

K dispozícii sú tieto časti:

- **Asistovaný režim**
- **Režim kontroly kroku**
- **Vzorové príklady**

## 10. Dôležité poznámky

- Frontend komunikuje s backendom na adrese `http://127.0.0.1:8000`.
- Backend preto musí byť pred otvorením aplikácie spustený.
- Ak zmeníte port backendu, bude potrebné upraviť aj adresu API v súboroch `guided.js`, `manual.js` a `examples.js`.
- Ak PowerShell zablokuje aktiváciu virtuálneho prostredia, môže byť potrebné povoliť spúšťanie skriptov.

## 11. Ukončenie backendu

Backend ukončíte v termináli klávesovou skratkou:

```text
CTRL + C
```