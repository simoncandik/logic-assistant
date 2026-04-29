# Interaktívny nástroj pre dokazovanie vo výrokovej logike – používateľský návod

Tento dokument slúži ako stručný návod na používanie webovej aplikácie **Interaktívny nástroj pre dokazovanie vo výrokovej logike**.

## 1. Účel aplikácie

Aplikácia je didaktický nástroj určený na prácu s:

- **formulami výrokovej logiky**
- **úsudkami výrokovej logiky**

Používateľ môže krok po kroku vykonávať ekvivalentné úpravy, kontrolovať ich správnosť a sledovať priebeh riešenia.

## 2. Spustenie aplikácie

Pred použitím aplikácie je potrebné:

1. spustiť backend vo FastAPI
2. otvoriť súbor `frontend/index.html` v prehliadači

Podrobný postup je uvedený v súbore `README_install.md`.

## 3. Hlavné časti aplikácie

Po otvorení úvodnej stránky sú dostupné tri časti:

### Asistovaný režim
Systém vyhľadá možné ekvivalentné úpravy aktuálnej formuly a používateľ si z nich vyberá ďalší krok.

### Režim kontroly kroku
Používateľ zapisuje ďalší krok samostatne a systém overí, či ide o korektnú jednokrokovú ekvivalentnú úpravu.

### Vzorové príklady
Stránka obsahuje prehľad podporovaných zákonov ekvivalencie a ukážkové vyriešené príklady.

## 4. Zadanie vstupu

V oboch hlavných režimoch je možné zvoliť typ vstupu:

- **Formula**
- **Úsudok**

### Príklad vstupu typu formula

```text
((p → q) ∧ p) → q
```

### Príklad vstupu typu úsudok

```text
p → q, p ⊨ q
```

Podporované symboly úsudku sú:

- `⊨`
- `|=`
- `I=`
- `⊢`

## 5. Podporované symboly pri zápise

Aplikácia pracuje so symbolmi:

- `¬` negácia
- `∧` konjunkcia
- `∨` disjunkcia
- `→` implikácia
- `↔` ekvivalencia
- `T` pravda
- `F` nepravda

Použiť je možné aj zátvorky:

- `()`
- `[]`
- `{}`

## 6. Asistovaný režim

### Postup práce

1. Zvoľte typ vstupu.
2. Zadajte formulu alebo úsudok.
3. Kliknite na **Navrhni úpravy**.
4. Zobrazí sa aktuálna formula a zoznam možných úprav.
5. Pri vybranej úprave kliknite na **Použiť**.
6. Postup opakujte, kým sa riešenie nedostane do výsledného tvaru.

### Čo aplikácia zobrazuje

- aktuálnu formulu
- možné úpravy
- použitý zákon
- históriu krokov
- stav dokazovania
- prípadný prevod úsudku na formulu
- upozornenia na možné zacyklenie

### Tlačidlá

- **Navrhni úpravy** – vyhľadá možné ďalšie kroky
- **Krok späť** – vráti riešenie o jeden krok späť
- **Reset** – vymaže aktuálne riešenie
- **Uložiť riešenie** – uloží priebeh riešenia do textového súboru

## 7. Režim kontroly kroku

### Postup práce

1. Zvoľte typ vstupu.
2. Zadajte počiatočnú formulu alebo úsudok.
3. Kliknite na **Spustiť**.
4. Do poľa **Nasledujúci krok** zapíšte ďalší tvar formuly.
5. Kliknite na **Over krok**.

### Výsledok kontroly

Systém môže oznámiť:

- že krok je korektný
- že krok nie je korektný
- ktorý zákon alebo zákony boli rozpoznané
- či sa dokazovanie ukončilo na `T` alebo `F`

### Tlačidlá

- **Spustiť** – inicializuje riešenie
- **Over krok** – overí zadanú úpravu
- **Krok späť** – návrat k predchádzajúcemu kroku
- **Reset** – vymazanie riešenia
- **Uložiť riešenie** – uloženie priebehu riešenia do textového súboru

## 8. História krokov

V oboch režimoch sa priebežne vytvára história riešenia.

História obsahuje:

- počiatočnú formulu
- jednotlivé vykonané kroky
- použitý zákon
- výslednú formulu po každom kroku

Po kliknutí na konkrétny krok sa otvorí jeho detail. Z detailu je možné vrátiť sa na vybraný krok riešenia.

## 9. Prevod úsudku na formulu

Ak používateľ zadá vstup typu **úsudok**, systém ho najskôr prevedie na formulu vhodnú na ďalšie ekvivalentné úpravy.

Používateľ potom vidí:

- pôvodne zadaný úsudok
- informáciu o prevode úsudku na formulu
- výslednú formulu, s ktorou aplikácia ďalej pracuje

## 10. Ukončenie dokazovania

Ak sa formula upraví na:

- `T` – výsledkom je **tautológia**
- `F` – výsledkom je **kontradikcia**

Aplikácia túto skutočnosť oznámi v rozhraní.

## 11. Ochrana pred zacyklením

Aplikácia obsahuje mechanizmus proti zacykleniu.

Upozorní používateľa napríklad vtedy, keď:

- sa pokúša opakovať tú istú úpravu na tom istom tvare formule
- by sa ďalším krokom vrátil na už navštívený tvar formule

V asistovanom režime môžu byť takéto kroky automaticky zablokované.

## 12. Vzorové príklady

Stránka **Vzorové príklady** obsahuje:

- tabuľku podporovaných zákonov ekvivalencie
- ukážkové vyriešené príklady
- možnosť otvoriť vybraný príklad priamo v asistovanom režime

Táto časť je vhodná najmä na oboznámenie sa s princípom práce aplikácie.

## 13. Export riešenia

V oboch režimoch je možné uložiť priebeh riešenia do textového súboru `.txt`.

Export obsahuje:

- typ vstupu
- pôvodný vstup
- prevod úsudku na formulu, ak bol použitý
- počiatočnú formulu
- históriu krokov
- použité zákony
- výsledný stav riešenia