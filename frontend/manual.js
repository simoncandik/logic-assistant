// Adresa backendového API, s ktorým frontend komunikuje.
const API = "http://127.0.0.1:8000";

// Pole uchovávajúce kompletnú históriu krokov riešenia.
let historySteps = [];

// Index aktuálneho kroku v histórii.
let currentStepIndex = -1;

// Index kroku, ktorý je práve vybraný v detaile histórie.
let selectedHistoryIndex = -1;

// Aktuálny normalizovaný tvar formule zobrazený v aplikácii.
let currentFormulaValue = "";

// Identifikátor vstupného poľa, do ktorého sa majú vkladať symboly z panela tlačidiel.
let activeInputId = "formula";

// Textová informácia o prevode úsudku na formulu.
let currentConversionMessage = "";

// Pôvodný vstup používateľa pred spracovaním backendom.
let originalInputValue = "";

// Typ pôvodného vstupu: formula alebo argument.
let originalInputMode = "formula";

/*
 * Funkcia nastaví, ktoré vstupné pole je aktuálne aktívne.
 * Používa sa na správne vkladanie symbolov buď do počiatočnej formule,
 * alebo do poľa pre nasledujúci krok.
 */
function setActiveInput(id) {
    activeInputId = id;
}

/*
 * Funkcia vloží zvolený symbol na aktuálnu pozíciu kurzora
 * do práve aktívneho vstupného poľa.
 */
function insert(text) {
    const input = document.getElementById(activeInputId);
    if (!input) return;

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
 * Funkcia zobrazí stav riešenia iba na základe textového tvaru formule.
 * Používa sa pri návrate na starší krok z histórie.
 */
function renderSolutionStatusFromFormula(formula) {
    const container = document.getElementById("solutionStatus");
    if (!container) return;

    if (formula === "T") {
        container.innerHTML = `
            <div class="feedback success">
                <b>✓ Dokazovanie je ukončené</b><br>
                Gratulujem, formula sa upravila na T. Dokazovanie je ukončené a výsledok je tautológia.
            </div>
        `;
        return;
    }

    if (formula === "F") {
        container.innerHTML = `
            <div class="feedback success">
                <b>✓ Dokazovanie je ukončené</b><br>
                Gratulujem, formula sa upravila na F. Dokazovanie je ukončené a výsledok je kontradikcia.
            </div>
        `;
        return;
    }

    container.innerHTML = "";
}

/*
 * Funkcia vykreslí aktuálnu formulu do hlavnej zobrazovacej oblasti.
 */
function renderCurrentFormula() {
    const current = document.getElementById("current");

    if (!currentFormulaValue) {
        current.innerHTML = "";
        return;
    }

    current.innerHTML = escapeHtml(currentFormulaValue);
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
 * Súčasne obnoví stav formulí, spätnú väzbu a kurzor do poľa pre ďalší krok.
 */
function returnToStep(index) {
    if (index < 0 || index >= historySteps.length) return;

    currentStepIndex = index;
    currentFormulaValue = historySteps[index].formula;

    document.getElementById("formula").value = currentFormulaValue;
    document.getElementById("nextFormula").value = "";
    document.getElementById("feedback").innerHTML = "";
    renderCurrentFormula();
    renderConversionInfo();
    renderSolutionStatusFromFormula(currentFormulaValue);
    renderHistory();
    closeStepDetail();

    document.getElementById("nextFormula").focus();
    activeInputId = "nextFormula";
}

/*
 * Funkcia vynuluje celý stav režimu kontroly kroku.
 * Odstráni históriu, aktuálnu formulu, spätnú väzbu aj informáciu o prevode úsudku.
 */
function resetManual() {
    historySteps = [];
    currentStepIndex = -1;
    selectedHistoryIndex = -1;
    currentFormulaValue = "";
    activeInputId = "formula";
    originalInputValue = "";
    originalInputMode = "formula";

    currentConversionMessage = "";
    document.getElementById("conversionInfo").innerHTML = "";

    document.getElementById("formula").value = "";
    document.getElementById("nextFormula").value = "";
    document.getElementById("feedback").innerHTML = "";
    document.getElementById("history").innerHTML = "";
    document.getElementById("solutionStatus").innerHTML = "";
    renderCurrentFormula();
    closeStepDetail();
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
        helper.textContent = "Po spustení zapisuj ďalší krok do poľa nižšie.";
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
 * Funkcia spustí režim kontroly kroku nad aktuálne zadaným vstupom.
 * Uloží pôvodný vstup, pošle ho na backend a inicializuje históriu riešenia.
 */
async function startManual() {
    const formula = document.getElementById("formula").value.trim();
    if (!formula) return;

    const inputMode = getSelectedInputMode();

    originalInputValue = formula;
    originalInputMode = inputMode;

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
        return;
    }

    currentFormulaValue = data.ast;
    currentConversionMessage = data.converted_from_argument ? (data.conversion_message || "") : "";

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

    document.getElementById("formula").value = data.ast;
    document.getElementById("nextFormula").value = "";
    document.getElementById("feedback").innerHTML = "";
    renderCurrentFormula();
    renderConversionInfo();
    renderSolutionStatusFromData(data);
    renderHistory();

    document.getElementById("nextFormula").focus();
    activeInputId = "nextFormula";
}

/*
 * Funkcia odošle používateľom zadaný ďalší krok na endpoint /check-step.
 * Backend overí, či ide o korektnú jednokrokovú ekvivalentnú úpravu.
 */
async function checkManualStep() {
    const nextFormula = document.getElementById("nextFormula").value.trim();
    if (!currentFormulaValue || !nextFormula) return;

    const res = await fetch(API + "/check-step", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            current_formula: currentFormulaValue,
            next_formula: nextFormula
        })
    });

    const data = await res.json();

    if (!data.ok) {
        alert(data.error);
        return;
    }

    const feedback = document.getElementById("feedback");

    if (!data.valid_step) {
        feedback.innerHTML = `
            <div class="feedback error">
                <b>✗ Krok nie je korektný</b><br>
                ${escapeHtml(data.message)}
            </div>
        `;
        return;
    }

    const rulesHtml = renderMatchedRules(data.matched_rules);

    feedback.innerHTML = `
        <div class="feedback success">
            <b>✓ Krok je korektný</b><br>
            ${escapeHtml(data.message)}
            <div style="margin-top:10px">
                <b>Rozpoznané zákony ekvivalencie:</b>
                ${rulesHtml}
            </div>
        </div>
    `;

    const primaryRule = data.matched_rules[0];

    const repeatedTransformation = data.matched_rules.some(r =>
        wasSameTransformationUsed(data.normalized_current, r.rule_code, data.normalized_next)
    );

    if (repeatedTransformation) {
        feedback.innerHTML = `
            <div class="feedback error">
                <b>↺ Opakovaná úprava</b><br>
                Tú istú úpravu ste už na tejto formule použili.
            </div>
        `;
        return;
    }

    if (wouldReturnToVisitedFormula(data.normalized_next)) {
        feedback.innerHTML = `
            <div class="feedback error">
                <b>↺ Možné zacyklenie</b><br>
                Týmto krokom by ste sa vrátili na už navštívený tvar formule.
            </div>
        `;
        return;
    }

    currentFormulaValue = data.normalized_next;
    document.getElementById("formula").value = data.normalized_next;
    document.getElementById("nextFormula").value = "";
    renderCurrentFormula();
    renderSolutionStatusFromData(data);

    if (currentStepIndex >= 0 && currentStepIndex < historySteps.length - 1) {
        historySteps = historySteps.slice(0, currentStepIndex + 1);
    }

    historySteps.push({
        formula: data.normalized_next,
        rule_code: primaryRule.rule_code,
        rule_name: primaryRule.rule_name,
        rule_form: primaryRule.rule_form,
        before: data.normalized_current,
        after: data.normalized_next
    });

    currentStepIndex = historySteps.length - 1;
    renderHistory();

    document.getElementById("nextFormula").focus();
    activeInputId = "nextFormula";
}

/*
 * Funkcia vráti riešenie o jeden krok späť.
 * Obnoví predchádzajúci stav formule a pripraví pole pre ďalší krok.
 */
function undoStep() {
    if (currentStepIndex <= 0) return;

    currentStepIndex -= 1;
    currentFormulaValue = historySteps[currentStepIndex].formula;

    document.getElementById("formula").value = currentFormulaValue;
    document.getElementById("nextFormula").value = "";
    document.getElementById("feedback").innerHTML = "";
    renderCurrentFormula();
    renderConversionInfo();
    renderSolutionStatusFromFormula(currentFormulaValue);
    renderHistory();

    document.getElementById("nextFormula").focus();
    activeInputId = "nextFormula";
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
 * Funkcia vykreslí všetky zákony, ktoré backend rozpoznal
 * pri kontrole používateľom zadaného kroku.
 */
function renderMatchedRules(matchedRules) {
    return matchedRules.map(r => {
        const shortLabel = `(${r.rule_code}) ${r.rule_name}`;

        let finishHtml = "";
        if (r.finishes_proof) {
            finishHtml = `
                <div class="completion-hint">
                    <b>Upozornenie:</b> ${escapeHtml(r.final_message)}
                </div>
            `;
        }

        return `
            <div class="matched-rule">
                <b>${escapeHtml(shortLabel)}</b><br>
                <div class="rule-form-line">${escapeHtml(r.rule_form)}</div>
                <div class="rule-example-line">${escapeHtml(r.before)} ↔ ${escapeHtml(r.after)}</div>
                ${finishHtml}
            </div>
        `;
    }).join("");
}

/*
 * Po načítaní súboru sa inicializuje používateľské rozhranie
 * podľa predvoleného typu vstupu.
 */
updateInputModeUI();