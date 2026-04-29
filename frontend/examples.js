// Adresa backendového API, s ktorým frontend komunikuje pri načítaní tabuľky zákonov.
const API = "http://127.0.0.1:8000";

/*
 * Pomocná funkcia na escapovanie špeciálnych znakov pred vložením textu do HTML.
 * Zabraňuje tomu, aby sa používateľský alebo dátový text interpretoval ako HTML kód.
 */
function escapeHtml(text) {
    return String(text ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;");
}

/*
 * Pole vzorových príkladov zobrazovaných na stránke examples.html.
 * Každý objekt obsahuje názov príkladu, počiatočnú formulu, očakávaný výsledok
 * a postup riešenia rozdelený na jednotlivé kroky.
 */
const EXAMPLES = [
    {
        id: "ex1",
        title: "Modus ponens ako tautológia",
        input_mode: "formula",
        input_label: "Počiatočná formula",
        formula: "((p → q) ∧ p) → q",
        final_formula: "T",
        final_note: "Formula sa upraví na T, preto ide o tautológiu.",
        steps: [
            {after: "((¬p ∨ q) ∧ p) → q", rule_code: "Z1", rule_name: "Definícia implikácie"},
            {after: "((p ∧ ¬p) ∨ (p ∧ q)) → q", rule_code: "Z2", rule_name: "Distributívny zákon"},
            {after: "(F ∨ (p ∧ q)) → q", rule_code: "Z5", rule_name: "Komplementárny zákon"},
            {after: "(p ∧ q) → q", rule_code: "Z8", rule_name: "Zákon s konštantou"},
            {after: "¬(p ∧ q) ∨ q", rule_code: "Z1", rule_name: "Definícia implikácie"},
            {after: "(¬p ∨ ¬q) ∨ q", rule_code: "Z13", rule_name: "De Morganov zákon"},
            {after: "¬p ∨ (¬q ∨ q)", rule_code: "Z16b", rule_name: "Asociatívny zákon"},
            {after: "¬p ∨ T", rule_code: "Z4", rule_name: "Komplementárny zákon"},
            {after: "T ∨ ¬p", rule_code: "Z11b", rule_name: "Komutatívny zákon"},
            {after: "T", rule_code: "Z9", rule_name: "Zákon s konštantou"}
        ]
    },
    {
        id: "ex2",
        title: "Kontrapozícia ako tautológia",
        input_mode: "formula",
        input_label: "Počiatočná formula",
        formula: "((p → q) ∧ ¬q) → ¬p",
        final_formula: "T",
        final_note: "Formula sa upraví na T, preto ide o tautológiu.",
        steps: [
            {after: "((¬p ∨ q) ∧ ¬q) → ¬p", rule_code: "Z1", rule_name: "Definícia implikácie"},
            {after: "((¬q ∧ ¬p) ∨ (¬q ∧ q)) → ¬p", rule_code: "Z2", rule_name: "Distributívny zákon"},
            {after: "((¬q ∧ ¬p) ∨ F) → ¬p", rule_code: "Z5", rule_name: "Komplementárny zákon"},
            {after: "(¬q ∧ ¬p) → ¬p", rule_code: "Z8", rule_name: "Zákon s konštantou"},
            {after: "¬(¬q ∧ ¬p) ∨ ¬p", rule_code: "Z1", rule_name: "Definícia implikácie"},
            {after: "(¬¬q ∨ ¬¬p) ∨ ¬p", rule_code: "Z13", rule_name: "De Morganov zákon"},
            {after: "(q ∨ ¬¬p) ∨ ¬p", rule_code: "Z12", rule_name: "Dvojitá negácia"},
            {after: "(q ∨ p) ∨ ¬p", rule_code: "Z12", rule_name: "Dvojitá negácia"},
            {after: "q ∨ (p ∨ ¬p)", rule_code: "Z16b", rule_name: "Asociatívny zákon"},
            {after: "q ∨ T", rule_code: "Z4", rule_name: "Komplementárny zákon"},
            {after: "T ∨ q", rule_code: "Z11b", rule_name: "Komutatívny zákon"},
            {after: "T", rule_code: "Z9", rule_name: "Zákon s konštantou"}
        ]
    },
    {
        id: "ex3",
        title: "Zloženejšia tautológia s implikáciou",
        input_mode: "formula",
        input_label: "Počiatočná formula",
        formula: "(q ∧ p) → ((p → q) ∧ (¬p ∨ q))",
        final_formula: "T",
        final_note: "Formula sa upraví na T, preto ide o tautológiu.",
        steps: [
            {after: "(q ∧ p) → ((¬p ∨ q) ∧ (¬p ∨ q))", rule_code: "Z1", rule_name: "Definícia implikácie"},
            {after: "(q ∧ p) → (¬p ∨ q)", rule_code: "Z10a", rule_name: "Idempotencia"},
            {after: "¬(q ∧ p) ∨ (¬p ∨ q)", rule_code: "Z1", rule_name: "Definícia implikácie"},
            {after: "(¬q ∨ ¬p) ∨ (¬p ∨ q)", rule_code: "Z13", rule_name: "De Morganov zákon"},
            {after: "¬q ∨ (¬p ∨ (¬p ∨ q))", rule_code: "Z16b", rule_name: "Asociatívny zákon"},
            {after: "¬q ∨ ((¬p ∨ ¬p) ∨ q)", rule_code: "Z16b", rule_name: "Asociatívny zákon"},
            {after: "¬q ∨ (¬p ∨ q)", rule_code: "Z10b", rule_name: "Idempotencia"},
            {after: "¬q ∨ (q ∨ ¬p)", rule_code: "Z11b", rule_name: "Komutatívny zákon"},
            {after: "(¬q ∨ q) ∨ ¬p", rule_code: "Z16b", rule_name: "Asociatívny zákon"},
            {after: "T ∨ ¬p", rule_code: "Z4", rule_name: "Komplementárny zákon"},
            {after: "T", rule_code: "Z9", rule_name: "Zákon s konštantou"}
        ]
    },
    {
        id: "ex4",
        title: "Tautológia s negáciou antecedentu",
        input_mode: "formula",
        input_label: "Počiatočná formula",
        formula: "((p → q) ∧ (q ∨ p)) → (¬p ∨ q)",
        final_formula: "T",
        final_note: "Formula sa upraví na T, preto ide o tautológiu.",
        steps: [
            {after: "((¬p ∨ q) ∧ (q ∨ p)) → (¬p ∨ q)", rule_code: "Z1", rule_name: "Definícia implikácie"},
            {after: "¬((¬p ∨ q) ∧ (q ∨ p)) ∨ (¬p ∨ q)", rule_code: "Z1", rule_name: "Definícia implikácie"},
            {after: "(¬(¬p ∨ q) ∨ ¬(q ∨ p)) ∨ (¬p ∨ q)", rule_code: "Z13", rule_name: "De Morganov zákon"},
            {after: "¬(¬p ∨ q) ∨ (¬(q ∨ p) ∨ (¬p ∨ q))", rule_code: "Z16b", rule_name: "Asociatívny zákon"},
            {after: "¬(¬p ∨ q) ∨ ((¬p ∨ q) ∨ ¬(q ∨ p))", rule_code: "Z11b", rule_name: "Komutatívny zákon"},
            {after: "(¬(¬p ∨ q) ∨ (¬p ∨ q)) ∨ ¬(q ∨ p)", rule_code: "Z16b", rule_name: "Asociatívny zákon"},
            {after: "T ∨ ¬(q ∨ p)", rule_code: "Z4", rule_name: "Komplementárny zákon"},
            {after: "T", rule_code: "Z9", rule_name: "Zákon s konštantou"}
        ]
    },
    {
        id: "ex5",
        title: "Kontradikcia s ekvivalenciou",
        input_mode: "formula",
        input_label: "Počiatočná formula",
        formula: "(p → q) ↔ (p ∧ ¬q)",
        final_formula: "F",
        final_note: "Formula sa upraví na F, preto ide o kontradikciu.",
        steps: [
            {
                after: "((p → q) → (p ∧ ¬q)) ∧ ((p ∧ ¬q) → (p → q))",
                rule_code: "Z15",
                rule_name: "Definícia ekvivalencie"
            },
            {after: "((¬p ∨ q) → (p ∧ ¬q)) ∧ ((p ∧ ¬q) → (p → q))", rule_code: "Z1", rule_name: "Definícia implikácie"},
            {
                after: "((¬p ∨ q) → (p ∧ ¬q)) ∧ ((p ∧ ¬q) → (¬p ∨ q))",
                rule_code: "Z1",
                rule_name: "Definícia implikácie"
            },
            {
                after: "(¬(¬p ∨ q) ∨ (p ∧ ¬q)) ∧ ((p ∧ ¬q) → (¬p ∨ q))",
                rule_code: "Z1",
                rule_name: "Definícia implikácie"
            },
            {
                after: "(¬(¬p ∨ q) ∨ (p ∧ ¬q)) ∧ (¬(p ∧ ¬q) ∨ (¬p ∨ q))",
                rule_code: "Z1",
                rule_name: "Definícia implikácie"
            },
            {
                after: "((¬¬p ∧ ¬q) ∨ (p ∧ ¬q)) ∧ (¬(p ∧ ¬q) ∨ (¬p ∨ q))",
                rule_code: "Z14",
                rule_name: "De Morganov zákon"
            },
            {after: "((p ∧ ¬q) ∨ (p ∧ ¬q)) ∧ (¬(p ∧ ¬q) ∨ (¬p ∨ q))", rule_code: "Z12", rule_name: "Dvojitá negácia"},
            {after: "(p ∧ ¬q) ∧ (¬(p ∧ ¬q) ∨ (¬p ∨ q))", rule_code: "Z10b", rule_name: "Idempotencia"},
            {after: "(p ∧ ¬q) ∧ ((¬p ∨ ¬¬q) ∨ (¬p ∨ q))", rule_code: "Z13", rule_name: "De Morganov zákon"},
            {after: "(p ∧ ¬q) ∧ ((¬p ∨ q) ∨ (¬p ∨ q))", rule_code: "Z12", rule_name: "Dvojitá negácia"},
            {after: "(p ∧ ¬q) ∧ (¬p ∨ q)", rule_code: "Z10b", rule_name: "Idempotencia"},
            {after: "((p ∧ ¬q) ∧ ¬p) ∨ ((p ∧ ¬q) ∧ q)", rule_code: "Z2", rule_name: "Distributívny zákon"},
            {after: "(p ∧ (¬q ∧ ¬p)) ∨ ((p ∧ ¬q) ∧ q)", rule_code: "Z16a", rule_name: "Asociatívny zákon"},
            {after: "(p ∧ (¬p ∧ ¬q)) ∨ ((p ∧ ¬q) ∧ q)", rule_code: "Z11a", rule_name: "Komutatívny zákon"},
            {after: "((p ∧ ¬p) ∧ ¬q) ∨ ((p ∧ ¬q) ∧ q)", rule_code: "Z16a", rule_name: "Asociatívny zákon"},
            {after: "(F ∧ ¬q) ∨ ((p ∧ ¬q) ∧ q)", rule_code: "Z5", rule_name: "Komplementárny zákon"},
            {after: "F ∨ ((p ∧ ¬q) ∧ q)", rule_code: "Z7", rule_name: "Zákon s konštantou"},
            {after: "F ∨ (p ∧ (¬q ∧ q))", rule_code: "Z16a", rule_name: "Asociatívny zákon"},
            {after: "F ∨ (p ∧ F)", rule_code: "Z5", rule_name: "Komplementárny zákon"},
            {after: "F ∨ (F ∧ p)", rule_code: "Z11a", rule_name: "Komutatívny zákon"},
            {after: "F ∨ F", rule_code: "Z7", rule_name: "Zákon s konštantou"},
            {after: "F", rule_code: "Z8", rule_name: "Zákon s konštantou"}
        ]
    }
];

/*
 * Funkcia načíta z backendu metadáta všetkých podporovaných zákonov ekvivalencie
 * a následne ich zobrazí v tabuľke na stránke vzorových príkladov.
 */
async function loadRulesMeta() {
    const container = document.getElementById("rulesTableContainer");

    try {
        const res = await fetch(API + "/rules-meta");
        const data = await res.json();

        if (!Array.isArray(data)) {
            container.innerHTML = `<div class="feedback error">Nepodarilo sa načítať tabuľku zákonov.</div>`;
            return;
        }

        container.innerHTML = `
            <table class="rules-table">
                <thead>
                    <tr>
                        <th>Index</th>
                        <th>Názov zákona</th>
                        <th>Tvar zákona</th>
                    </tr>
                </thead>
                <tbody>
                    ${data.map(rule => `
                        <tr>
                            <td>${escapeHtml(rule.code)}</td>
                            <td>${escapeHtml(rule.name)}</td>
                            <td>${escapeHtml(rule.form)}</td>
                        </tr>
                    `).join("")}
                </tbody>
            </table>
        `;
    } catch (err) {
        container.innerHTML = `<div class="feedback error">Chyba pri načítaní tabuľky zákonov.</div>`;
    }
}

/*
 * Funkcia vytvorí URL adresu, pomocou ktorej je možné otvoriť konkrétny vzorový príklad
 * priamo v asistovanom režime aplikácie aj s automatickým spustením riešenia.
 */
function buildOpenInAppUrl(example) {
    const params = new URLSearchParams({
        formula: example.formula,
        input_mode: example.input_mode || "formula",
        autostart: "1"
    });

    return `guided.html?${params.toString()}`;
}

/*
 * Funkcia vykreslí všetky vzorové príklady uložené v poli EXAMPLES.
 * Pri každom príklade zobrazí počiatočnú formulu, jednotlivé kroky riešenia
 * a výsledný tvar formule spolu so stručným slovným zhrnutím.
 */
function renderExamples() {
    const container = document.getElementById("examplesContainer");

    container.innerHTML = EXAMPLES.map(example => {
        let current = example.formula;

        const stepsHtml = example.steps.map((step, index) => {
            const row = `
                <div class="example-step">
                    <div class="example-step-header">
                        <span class="example-step-number">Krok ${index + 1}</span>
                        <span class="example-rule-badge">(${escapeHtml(step.rule_code)}) ${escapeHtml(step.rule_name)}</span>
                    </div>
                    <div class="example-step-formulas">
                        <div><b>Pred:</b> ${escapeHtml(current)}</div>
                        <div><b>Po:</b> ${escapeHtml(step.after)}</div>
                    </div>
                </div>
            `;
            current = step.after;
            return row;
        }).join("");

        return `
            <div class="example-card">
                <div class="example-card-header">
                    <div>
                        <h3>${escapeHtml(example.title)}</h3>
                    </div>
                    <a class="nav-button" href="${buildOpenInAppUrl(example)}">Otvoriť v aplikácii</a>
                </div>

                <div class="example-block">
                    <b>${escapeHtml(example.input_label || "Počiatočná formula")}:</b><br>
                    <span class="example-formula">${escapeHtml(example.formula)}</span>
                </div>

                <div class="example-steps">
                    ${stepsHtml}
                </div>

                <div class="example-block example-final">
                    <b>Výsledok:</b><br>
                    <span class="example-formula">${escapeHtml(example.final_formula)}</span>
                    <div class="helper-text" style="margin-top: 8px;">
                        ${escapeHtml(example.final_note)}
                    </div>
                </div>
            </div>
        `;
    }).join("");
}

/*
 * Po načítaní dokumentu sa inicializuje obsah stránky:
 * najprv sa načíta tabuľka zákonov z backendu a následne sa vykreslia vzorové príklady.
 */
document.addEventListener("DOMContentLoaded", async () => {
    await loadRulesMeta();
    renderExamples();
});