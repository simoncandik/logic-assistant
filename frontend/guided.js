// Adresa backendového API, s ktorým frontend komunikuje.
const API = "http://127.0.0.1:8000";

// Pole uchovávajúce kompletnú históriu krokov riešenia.
let historySteps = [];

// Index aktuálne zobrazeného kroku v histórii.
let currentStepIndex = -1;

// Index kroku, ktorý je práve vybraný v detaile histórie.
let selectedHistoryIndex = -1;

// Aktuálny normalizovaný tvar formule zobrazený v aplikácii.
let currentFormulaValue = "";

// Textová informácia o prevode úsudku na formulu.
let currentConversionMessage = "";

// Pôvodný vstup používateľa pred spracovaním backendom.
let originalInputValue = "";

// Typ pôvodného vstupu: formula alebo argument.
let originalInputMode = "formula";

/*
 * Funkcia vloží zvolený symbol na aktuálnu pozíciu kurzora do vstupného poľa.
 * Používa sa pri tlačidlách s logickými spojkami a pomocnými symbolmi.
 */
function insert(text) {
    const input = document.getElementById("formula");

    const start = input.selectionStart ?? input.value.length;
    const end = input.selectionEnd ?? input.value.length;

    input.value =
        input.value.substring(0, start) +
        text +
        input.value.substring(end);

    input.selectionStart = input.selectionEnd = start + text.length;
    input.focus();
}

/*
 * Pomocná funkcia na escapovanie špeciálnych znakov pred vložením textu do HTML.
 * Zabraňuje nechcenej interpretácii textu ako HTML kódu.
 */
function escapeHtml(text) {
    return String(text)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;");
}

/*
 * Funkcia vytvorí skrátené označenie zákona pre zobrazenie v histórii krokov.
 */
function getShortRuleLabel(step) {
    if (!step || !step.rule_code) return "Počiatočná formula";
    return `(${step.rule_code}) ${step.rule_name}`;
}

/*
 * Funkcia vytvorí úplné označenie zákona vrátane jeho formálneho tvaru.
 * Používa sa najmä v detaile konkrétneho kroku.
 */
function getFullRuleLabel(step) {
    if (!step || !step.rule_code) return "Počiatočná formula";
    return `(${step.rule_code}) ${step.rule_name}: ${step.rule_form}`;
}

/*
 * Funkcia prevedie text formule na orezaný reťazec bez nadbytočných medzier.
 * Slúži na jednotné porovnávanie tvarov formúl.
 */
function normalizeFormulaText(text) {
    return String(text ?? "").trim();
}

/*
 * Funkcia vráti aktívnu časť histórie riešenia.
 * Ak sa používateľ vrátil späť na starší krok, berú sa iba kroky po aktuálny index.
 */
function getActiveHistorySteps() {
    if (currentStepIndex < 0) {
        return historySteps;
    }
    return historySteps.slice(0, currentStepIndex + 1);
}

/*
 * Funkcia odstráni upozornenie na možné zacyklenie.
 */
function clearLoopWarning() {
    const container = document.getElementById("loopWarning");
    if (container) {
        container.innerHTML = "";
    }
}

/*
 * Funkcia zobrazí upozornenie na možné zacyklenie pri riešení.
 */
function renderLoopWarning(message) {
    const container = document.getElementById("loopWarning");
    if (!container) return;

    container.innerHTML = `
        <div class="loop-warning">
            <b>Upozornenie na možné zacyklenie</b><br>
            ${escapeHtml(message)}
        </div>
    `;
}

/*
 * Funkcia zistí, či bola rovnaká transformácia už v minulosti použitá
 * na rovnaký tvar formule s rovnakým výsledkom.
 */
function wasSameTransformationUsed(beforeFormula, ruleCode, afterFormula) {
    const before = normalizeFormulaText(beforeFormula);
    const after = normalizeFormulaText(afterFormula);

    return historySteps.some(step =>
        step.rule_code === ruleCode &&
        normalizeFormulaText(step.before) === before &&
        normalizeFormulaText(step.after || step.formula) === after
    );
}

/*
 * Funkcia zistí, či by navrhovaný krok nevrátil používateľa
 * na už navštívený tvar formule.
 */
function wouldReturnToVisitedFormula(nextFormula) {
    const next = normalizeFormulaText(nextFormula);
    const activeSteps = getActiveHistorySteps();

    return activeSteps.slice(0, -1).some(step =>
        normalizeFormulaText(step.formula) === next
    );
}

/*
 * Funkcia zobrazí stav riešenia v prípade, že backend oznámi ukončenie dokazovania.
 * Typicky ide o výsledok T alebo F.
 */
function renderSolutionStatusFromData(data) {
    const container = document.getElementById("solutionStatus");
    if (!container) return;

    if (!data || !data.is_finished) {
        container.innerHTML = "";
        return;
    }

    container.innerHTML = `
        <div class="feedback success">
            <b>✓ Dokazovanie je ukončené</b><br>
            ${escapeHtml(data.final_message)}
        </div>
    `;
}

/*
 * Funkcia vykreslí aktuálnu formulu do hlavnej zobrazovacej oblasti.
 * Ak je zadaný parameter highlightText, zvýrazní v texte zodpovedajúcu podformulu.
 */
function renderCurrentFormula(highlightText = null) {
    const current = document.getElementById("current");

    if (!currentFormulaValue) {
        current.innerHTML = "";
        return;
    }

    if (!highlightText) {
        current.innerHTML = escapeHtml(currentFormulaValue);
        return;
    }

    const index = currentFormulaValue.indexOf(highlightText);

    if (index === -1) {
        current.innerHTML = escapeHtml(currentFormulaValue);
        return;
    }

    const before = escapeHtml(currentFormulaValue.slice(0, index));
    const match = escapeHtml(currentFormulaValue.slice(index, index + highlightText.length));
    const after = escapeHtml(currentFormulaValue.slice(index + highlightText.length));

    current.innerHTML = `${before}<span class="subexpr-highlight">${match}</span>${after}`;
}

/*
 * Funkcia vykreslí históriu krokov riešenia.
 * Každý krok je možné kliknutím otvoriť v detaile.
 */
function renderHistory() {
    const container = document.getElementById("history");
    container.innerHTML = "";

    historySteps.forEach((step, i) => {
        const div = document.createElement("div");
        div.className = "history-item";

        if (i === currentStepIndex) {
            div.classList.add("active");
        }

        let ruleHtml = "";
        if (step.rule_code) {
            ruleHtml = `<div class="history-rule"><b>Zákon:</b> ${escapeHtml(getShortRuleLabel(step))}</div>`;
        }

        div.innerHTML = `
            <b>Krok ${i + 1}</b><br>
            ${ruleHtml}
            <div class="history-formula">${escapeHtml(step.formula)}</div>
        `;

        div.onclick = () => openStepDetail(i);
        container.appendChild(div);
    });
}

/*
 * Funkcia otvorí modálne okno s detailom vybraného kroku.
 * Zobrazí použitý zákon, jeho tvar a formulu pred aj po úprave.
 */
function openStepDetail(index) {
    if (index < 0 || index >= historySteps.length) return;

    selectedHistoryIndex = index;
    const step = historySteps[index];
    const body = document.getElementById("stepDetailBody");
    const returnBtn = document.getElementById("returnToStepBtn");

    let html = `<p><b>Krok:</b> ${index + 1}</p>`;

    if (step.rule_code) {
        html += `<p><b>Kód zákona:</b> ${escapeHtml(step.rule_code)}</p>`;
        html += `<p><b>Názov zákona:</b> ${escapeHtml(step.rule_name)}</p>`;
        html += `<p><b>Tvar zákona:</b><br>${escapeHtml(step.rule_form)}</p>`;
        html += `<p><b>Úplné označenie:</b><br>${escapeHtml(getFullRuleLabel(step))}</p>`;
    } else {
        html += `<p><b>Zákon:</b> Počiatočná formula</p>`;
    }

    if (step.before) {
        html += `<p><b>Pred úpravou:</b><br>${escapeHtml(step.before)}</p>`;
    }

    html += `<p><b>Po úprave:</b><br>${escapeHtml(step.after || step.formula)}</p>`;

    body.innerHTML = html;

    returnBtn.onclick = () => returnToStep(index);

    document.getElementById("stepDetailModal").classList.remove("hidden");
}

/*
 * Funkcia zatvorí modálne okno s detailom kroku.
 */
function closeStepDetail() {
    document.getElementById("stepDetailModal").classList.add("hidden");
    selectedHistoryIndex = -1;
}

/*
 * Funkcia vráti používateľa na vybraný krok histórie.
 * Následne sa pre tento stav znovu načítajú návrhy ďalších úprav.
 */
async function returnToStep(index) {
    if (index < 0 || index >= historySteps.length) return;

    currentStepIndex = index;
    currentFormulaValue = historySteps[index].formula;

    document.getElementById("formula").value = currentFormulaValue;
    renderCurrentFormula();
    renderConversionInfo();

    closeStepDetail();
    renderHistory();
    clearLoopWarning();
    await suggest();
}

/*
 * Funkcia vynuluje celý stav asistovaného režimu.
 * Odstráni históriu, aktuálnu formulu aj informácie o prevode úsudku.
 */
function resetHistory() {
    historySteps = [];
    currentStepIndex = -1;
    selectedHistoryIndex = -1;
    currentFormulaValue = "";
    currentConversionMessage = "";
    originalInputValue = "";
    originalInputMode = "formula";

    document.getElementById("formula").value = "";
    document.getElementById("history").innerHTML = "";
    document.getElementById("suggestions").innerHTML = "";
    document.getElementById("solutionStatus").innerHTML = "";
    document.getElementById("conversionInfo").innerHTML = "";
    clearLoopWarning();
    renderCurrentFormula();
    closeStepDetail();
    updateInputModeUI();
}

/*
 * Funkcia spustí asistovaný režim nad aktuálne zadaným vstupom.
 * Uloží pôvodný vstup, pošle ho na backend a inicializuje históriu riešenia.
 */
async function startSuggest() {
    const formula = document.getElementById("formula").value.trim();
    if (!formula) return;

    const inputMode = getSelectedInputMode();

    originalInputValue = formula;
    originalInputMode = inputMode;

    const data = await suggest(inputMode);
    if (!data) return;

    currentConversionMessage = data.converted_from_argument ? (data.conversion_message || "") : "";
    renderConversionInfo();

    historySteps = [
        {
            formula: data.ast,
            rule_code: null,
            rule_name: null,
            rule_form: null,
            before: null,
            after: data.ast
        }
    ];

    currentStepIndex = 0;
    renderHistory();
}

/*
 * Funkcia vykreslí všetky návrhy ekvivalentných úprav vrátené backendom.
 * Pri každom návrhu zohľadní aj anti-loop kontrolu a prípadné ukončenie dokazovania.
 */
function renderSuggestions(data) {
    const container = document.getElementById("suggestions");
    container.innerHTML = "";

    if (data.is_finished) {
        container.innerHTML = `
            <div class="helper-text">
                Formula je už v koncovom tvare. Ďalšie úpravy nie sú potrebné.
            </div>
        `;
        return;
    }

    data.suggestions.forEach(s => {
        const div = document.createElement("div");
        div.className = "rule";

        const repeatedTransformation = wasSameTransformationUsed(data.ast, s.rule_code, s.after);
        const returnsToVisitedFormula = wouldReturnToVisitedFormula(s.after);

        let finishHtml = "";
        if (s.finishes_proof) {
            finishHtml = `
                <div class="completion-hint">
                    <b>Upozornenie:</b> ${escapeHtml(s.final_message)}
                </div>
            `;
        }

        let loopHintHtml = "";
        if (repeatedTransformation) {
            loopHintHtml = `
                <div class="loop-hint">
                    <b>Anti-loop:</b> Túto úpravu ste už na tejto formule použili.
                </div>
            `;
        } else if (returnsToVisitedFormula) {
            loopHintHtml = `
                <div class="loop-hint">
                    <b>Anti-loop:</b> Touto úpravou by ste sa vrátili na už navštívený tvar formule.
                </div>
            `;
        }

        div.innerHTML = `
            <b>${escapeHtml(`(${s.rule_code}) ${s.rule_name}`)}</b><br>
            <div class="rule-form-line">${escapeHtml(s.rule_form)}</div>
            <div class="rule-example-line">${escapeHtml(s.before)} ↔ ${escapeHtml(s.after)}</div>
            ${finishHtml}
            ${loopHintHtml}
            <br>
        `;

        div.addEventListener("mouseenter", () => renderCurrentFormula(s.before));
        div.addEventListener("mouseleave", () => renderCurrentFormula());
        div.addEventListener("focusin", () => renderCurrentFormula(s.before));
        div.addEventListener("focusout", () => renderCurrentFormula());

        const button = document.createElement("button");
        button.textContent = "Použiť";

        const shouldBlock = repeatedTransformation || returnsToVisitedFormula;
        if (shouldBlock) {
            button.disabled = true;
        }

        button.onclick = () => applyRule(data.ast, s);

        div.appendChild(button);
        container.appendChild(div);
    });
}

/*
 * Funkcia zistí aktuálne zvolený typ vstupu z prepínača.
 */
function getSelectedInputMode() {
    const checked = document.querySelector('input[name="inputMode"]:checked');
    return checked ? checked.value : "formula";
}

/*
 * Funkcia prispôsobí placeholder a pomocný text podľa zvoleného typu vstupu.
 */
function updateInputModeUI() {
    const inputMode = getSelectedInputMode();
    const input = document.getElementById("formula");
    const helper = document.getElementById("inputHelper");

    if (inputMode === "argument") {
        input.placeholder = "A, B, C ⊨ D";
        helper.textContent = "Príklad vstupu úsudku: A, B, C ⊨ D";
    } else {
        input.placeholder = "((p → q) ∧ p) → q";
        helper.textContent = "Príklad vstupu: ((p → q) ∧ p) → q";
    }
}

/*
 * Funkcia zobrazí informáciu o tom, že zadaný úsudok bol prevedený na formulu.
 */
function renderConversionInfo() {
    const container = document.getElementById("conversionInfo");
    if (!container) return;

    if (!currentConversionMessage) {
        container.innerHTML = "";
        return;
    }

    container.innerHTML = `
        <div class="conversion-info">
            <b>Prevod úsudku na formulu</b><br>
            ${escapeHtml(currentConversionMessage)}
        </div>
    `;
}

/*
 * Funkcia nastaví prepínač typu vstupu podľa zadanej hodnoty.
 * Používa sa napríklad pri otvorení vzorového príkladu cez URL parametre.
 */
function applyInputModeFromValue(inputMode) {
    const radio = document.querySelector(`input[name="inputMode"][value="${inputMode}"]`);
    if (radio) {
        radio.checked = true;
        updateInputModeUI();
    }
}

/*
 * Funkcia prevedie internú hodnotu typu vstupu na text vhodný do exportu riešenia.
 */
function getInputModeLabel(mode) {
    return mode === "argument" ? "Úsudok" : "Formula";
}

/*
 * Funkcia vytvorí stručné slovné zhrnutie výsledku riešenia.
 */
function getResultSummaryText() {
    if (currentFormulaValue === "T") {
        return "Formula je tautológia.";
    }

    if (currentFormulaValue === "F") {
        return "Formula je kontradikcia.";
    }

    return "Dokazovanie nie je ukončené na T ani F.";
}

/*
 * Funkcia zostaví textový záznam riešenia na základe histórie krokov.
 * Výstup obsahuje typ vstupu, pôvodný vstup, prípadný prevod úsudku,
 * históriu krokov a výsledné zhrnutie.
 */
function buildSolutionText() {
    if (!historySteps.length) {
        return "";
    }

    const lines = [];

    lines.push("INTERAKTÍVNY NÁSTROJ PRE DOKAZOVANIE VO VÝROKOVEJ LOGIKE");
    lines.push("ZÁZNAM RIEŠENIA");
    lines.push("");
    lines.push(`Typ vstupu: ${getInputModeLabel(originalInputMode)}`);
    lines.push("");

    if (originalInputMode === "argument") {
        lines.push("Zadaný úsudok:");
        lines.push(originalInputValue || "-");
        lines.push("");

        lines.push("Prevod úsudku na formulu:");
        lines.push(currentConversionMessage || "Úsudok bol prevedený na formulu.");
        lines.push("");
    } else {
        lines.push("Zadaná formula:");
        lines.push(originalInputValue || "-");
        lines.push("");
    }

    lines.push("Počiatočná formula:");
    lines.push(historySteps[0].formula || "-");
    lines.push("");
    lines.push("HISTÓRIA KROKOV");
    lines.push("");

    for (let i = 1; i < historySteps.length; i++) {
        const step = historySteps[i];

        lines.push(`Krok ${i}:`);

        if (step.rule_code) {
            lines.push(`Použitý zákon: (${step.rule_code}) ${step.rule_name}`);
        }

        if (step.rule_form) {
            lines.push(`Tvar zákona: ${step.rule_form}`);
        }

        if (step.before) {
            lines.push(`Pred úpravou: ${step.before}`);
        }

        lines.push(`Po úprave: ${step.after || step.formula}`);
        lines.push("");
    }

    lines.push("VÝSLEDOK");
    lines.push("");
    lines.push(`Aktuálny tvar formule: ${currentFormulaValue || "-"}`);
    lines.push(getResultSummaryText());

    return lines.join("\n");
}

/*
 * Funkcia vytvorí a stiahne textový súbor s obsahom riešenia.
 */
function downloadTextFile(filename, content) {
    const blob = new Blob([content], {type: "text/plain;charset=utf-8"});
    const url = URL.createObjectURL(blob);

    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);

    URL.revokeObjectURL(url);
}

/*
 * Funkcia vygeneruje názov exportovaného súboru podľa typu vstupu a aktuálneho dátumu.
 */
function buildSolutionFilename() {
    const modePart = originalInputMode === "argument" ? "usudok" : "formula";
    const date = new Date();

    const yyyy = date.getFullYear();
    const mm = String(date.getMonth() + 1).padStart(2, "0");
    const dd = String(date.getDate()).padStart(2, "0");
    const hh = String(date.getHours()).padStart(2, "0");
    const mi = String(date.getMinutes()).padStart(2, "0");

    return `riesenie_${modePart}_${yyyy}-${mm}-${dd}_${hh}-${mi}.txt`;
}

/*
 * Funkcia spustí export riešenia do textového súboru.
 * Ak riešenie ešte nebolo inicializované, používateľ je na to upozornený.
 */
function saveSolutionToFile() {
    if (!historySteps.length) {
        alert("Najprv spusti riešenie, aby bolo čo uložiť.");
        return;
    }

    const content = buildSolutionText();
    const filename = buildSolutionFilename();

    downloadTextFile(filename, content);
}

/*
 * Funkcia odošle aktuálny vstup na endpoint /suggest a načíta návrhy ďalších úprav.
 * Zároveň aktualizuje zobrazenú formulu, stav riešenia a zoznam návrhov.
 */
async function suggest(inputMode = "formula") {
    const formula = document.getElementById("formula").value.trim();

    const res = await fetch(API + "/suggest", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            formula,
            input_mode: inputMode
        })
    });

    const data = await res.json();

    if (!data.ok) {
        alert(data.error);
        return null;
    }

    currentFormulaValue = data.ast;
    document.getElementById("formula").value = data.ast;
    renderCurrentFormula();
    renderSolutionStatusFromData(data);
    clearLoopWarning();
    renderSuggestions(data);

    return data;
}

/*
 * Funkcia aplikuje používateľom vybraný zákon na aktuálnu formulu.
 * Pred samotným odoslaním kontroluje možné zacyklenie.
 */
async function applyRule(formula, suggestion) {
    clearLoopWarning();

    if (wasSameTransformationUsed(formula, suggestion.rule_code, suggestion.after)) {
        renderLoopWarning("Túto úpravu ste už na tejto formule použili.");
        return;
    }

    if (wouldReturnToVisitedFormula(suggestion.after)) {
        renderLoopWarning("Touto úpravou by ste sa vrátili na už navštívený tvar formule.");
        return;
    }

    const res = await fetch(API + "/apply", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            formula,
            path: suggestion.path,
            rule_code: suggestion.rule_code
        })
    });

    const data = await res.json();

    if (!data.ok) {
        alert(data.error);
        return;
    }

    document.getElementById("formula").value = data.result;

    if (currentStepIndex >= 0 && currentStepIndex < historySteps.length - 1) {
        historySteps = historySteps.slice(0, currentStepIndex + 1);
    }

    historySteps.push({
        formula: data.result,
        rule_code: suggestion.rule_code,
        rule_name: suggestion.rule_name,
        rule_form: suggestion.rule_form,
        before: formula,
        after: data.result
    });

    currentStepIndex = historySteps.length - 1;
    renderHistory();

    await suggest();
}

/*
 * Funkcia vráti riešenie o jeden krok späť a následne načíta návrhy úprav
 * pre novú aktuálnu formulu.
 */
async function undoStep() {
    if (currentStepIndex <= 0) return;

    currentStepIndex -= 1;
    currentFormulaValue = historySteps[currentStepIndex].formula;

    document.getElementById("formula").value = currentFormulaValue;
    renderCurrentFormula();
    renderConversionInfo();

    renderHistory();
    await suggest();
}

/*
 * Funkcia zatvorí modálne okno s detailom kroku pri kliknutí mimo jeho obsahu.
 */
window.onclick = function (event) {
    const modal = document.getElementById("stepDetailModal");
    if (event.target === modal) {
        closeStepDetail();
    }
};

/*
 * Funkcia načíta parametre z URL adresy.
 * Umožňuje predvyplniť formulu, nastaviť typ vstupu a automaticky spustiť riešenie,
 * čo sa využíva pri prechode zo stránky vzorových príkladov.
 */
async function loadFormulaFromQuery() {
    const params = new URLSearchParams(window.location.search);

    const formula = params.get("formula");
    const inputMode = params.get("input_mode");
    const autostart = params.get("autostart");

    if (inputMode === "formula" || inputMode === "argument") {
        applyInputModeFromValue(inputMode);
    }

    if (formula) {
        document.getElementById("formula").value = formula;
    }

    if (formula && autostart === "1") {
        await startSuggest();
    }
}

/*
 * Po načítaní dokumentu sa inicializuje používateľské rozhranie
 * a spracujú sa prípadné vstupy z URL adresy.
 */
document.addEventListener("DOMContentLoaded", async () => {
    updateInputModeUI();
    await loadFormulaFromQuery();
});