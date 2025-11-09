# AI Game Master — Consolidated PRD + Technical Design (MVP v1.3)

## 1. Overview
Single-page hobby app that runs a rules-faithful B/X-compatible session with an AI GM. Inputs are user-supplied PDFs for rules and module, plus optional Markdown journal. PDFs are converted to text locally and never sent to the LLM. The GM uses only the uploaded rules and module, performs all dice via a function tool, and writes a human-readable journal that doubles as the save file.

---

## 2. Product Requirements

### 2.1 Goals
- Enable solo or small-table play for B/X, OSE, and B/X-compatible systems.
- Maintain simplicity. No server, no persistent storage, no multiplayer.

### 2.2 In Scope (MVP)
- **Inputs:** rules PDF(s), one module PDF, optional Markdown journal. Convert PDFs to text locally on upload; never send raw PDFs to the LLM.
- **Start session:** resume from existing journal or run guided character creation per the uploaded rules.
- **Core loop:** GM adheres strictly to rules + module only. If an action is unsupported, the GM refuses and includes a rules excerpt trimmed to ≤256 characters. Dice rolls must be performed via the dice tool and integrated into one cohesive response. No simulated rolls.
- **Interaction:** chat UI with free-form input; journal pane for viewing and download.
- **Journal:** sole save mechanism; Markdown with YAML front-matter; downloadable at any time.
- **UI:** one page, sentence case labels, dark mode default; include a Settings drawer.
- **Homebrew toggles (Settings):** `ability_scores_4d6L`, `level1_max_hp`. Both default off.
- **BYOK:** user supplies OpenAI API key at runtime; store in volatile memory only; cleared on tab close.
- **Model API:** OpenAI Responses API. Treat `output` as heterogeneous. Use `output_text` only as a convenience to aggregate text. Pin model snapshots for stability; reasoning models allowed.

### 2.3 Out of Scope
- Multiplayer, live web rules lookup, vector DB/RAG, persistent storage of keys or PII, additional tools beyond dice.

### 2.4 Acceptance Criteria
1) **Upload materials**
   - Local PDF→text completed; no raw PDFs sent to LLM.
   - Optional journal loads and renders.

2) **Provide API key (BYOK)**
   - Key lives only in page memory; cleared when the tab closes.

3) **Start session**
   - Journal present → resume. No journal → guided character creation per rule PDF.

4) **Play loop**
   - GM uses only rules + module; refuses unsupported actions with ≤256-char rule excerpt.
   - All rolls performed via dice tool, never simulated; GM returns one cohesive narrative.
   - GM message ends with a **Dice audit** section as an unordered list. Each bullet:
     `SOURCE ACTION TARGET: TOTAL (NdM+-KL)`
     Omit `TARGET` when none.

5) **Journal**
   - YAML front-matter carries machine state; session log appends one-line summary per GM turn; file downloadable as Markdown.

6) **Settings**
   - Homebrew toggles exist as specified and default off.

7) **Testing and DoD**
   - Unit tests for each core area; all pass before done.

### 2.5 Risks and Mitigations
- **PDF fidelity:** stat blocks and tables may degrade. Mitigate with deterministic parsing heuristics and on-upload preview.
- **Tool schema drift:** enforce strict JSON Schema, `additionalProperties: false`, required fields, enums.
- **Output heterogeneity:** do not assume a fixed location for text; iterate items; use `output_text` for aggregation.

---

## 3. Technical Design

### 3.1 Architecture
- **Client-only SPA**
  - Modules: file intake + local PDF→text; BYOK key entry (volatile); chat panel; journal drawer; settings drawer; download; LLM orchestrator using the OpenAI Responses API.
  - Treat `response.output` as heterogeneous; reasoning models supported; pin a model snapshot for repeatability.

### 3.2 Data Flow
1) **Upload:** PDFs → local parse → normalized text blocks with headings; never transmit raw PDFs to LLM.
2) **Compose request:**
   - Developer instructions encode rule primacy, refusal behavior with ≤256-char excerpt, dice via tool only, journal policy.
   - Messages contain prior turns, minimal rule/module snippets, and journal context. Use roles and `instructions` as appropriate.
3) **Tool calls:** Include the dice function tool. Set `parallel_tool_calls: false` to force ≤1 call per turn for determinism.
4) **Round-trip:** If model emits tool call(s), execute the dice tool, append results back to the model input, then request the final response.
5) **Render:** Iterate all `output` items and aggregate final text; append **Dice audit** bullets; update journal with one-line summary.

### 3.3 Tooling

**Function tool: `roll_dice`**
- **Purpose:** resolve dice expressions for B/X play.
- **Grammar:** `NdM[+/-K]` with optional `L` for drop-lowest.
- **Behavior on unknown formats:** simplify to nearest supported form for MVP; fidelity loss accepted.
- **Schema:** strict JSON Schema with `additionalProperties: false`; all fields required; use enums where applicable. Enable strict mode.
- **Concurrency:** `parallel_tool_calls: false` by default.
- **Loop contract:** execute tool, capture output as string, re-submit to model, then render final narrative.

### 3.4 Response Handling
- Do not assume a single text output. The `output` array can contain multiple items, including tool calls and reasoning items. Use `output_text` as a convenience aggregator, but be prepared to iterate items.
- If using reasoning models with tool calls, include any required reasoning items when round-tripping tool outputs.

### 3.5 Journal Format
- **File:** Markdown with YAML front-matter.
- **Front-matter fields:**
  `schema_version`, `system` (`BX` or `OSE`), `party` (name, abilities, HP, inventory), `flags` (homebrew toggles), `module_id`, `timestamps`.
- **Sections:** `# Session log`, `# Characters`, `# Inventory`, `# House rules`.
- **Turn write-through:** append a one-line summary per GM turn to `# Session log`. Journal is the only save file.

### 3.6 Output Formatting Rules
- **Narrative:** free-form assistant text.
- **Dice audit:** unordered list. Bullet grammar:
  `SOURCE ACTION TARGET: TOTAL (NdM+-KL)`
  Omit `TARGET` when none. Examples:
  - `Fighter attack Goblin: 17 (1d20+4)`
  - `Cleric roll ability Wisdom: 14 (4d6L)`
- **Refusals:** brief denial plus ≤256-char rule excerpt from local extraction.

### 3.7 PDF→Text Extraction
- Deterministic, local parsing tuned for OSE-style B/X stat blocks: detect headers and canonical stat lines (AC, HD, HP, MV, Att, Dmg, Save, Morale, XP). Provide short text excerpts to the model; never raw PDFs.

### 3.8 Security and Privacy
- BYOK only. Key is held in volatile page memory and cleared on tab close. No persistence. No third-party telemetry.

### 3.9 Testing Strategy
- **Unit tests:** PDF extractor, rule excerpt selector (enforces 256-char cap), OSE stat-block parser, dice tool adapter, prompt assembler, output aggregator, journal parser/serializer, turn reducer.
- **Behavioral tests:** character creation walkthrough per uploaded rules; at least one combat including tool-driven rolls and audit block.
- All tests must pass before delivery.

---

## 4. Implementation Notes for the Builder LLM
- Use the OpenAI Responses API. Do not assume text at a fixed index in `response.output`; iterate items. `output_text` is optional convenience.
- Pin a model snapshot for deterministic behavior in “release” mode; reasoning models are supported.
- Define exactly one function tool now. Keep the tool schema strict and minimal; invalid states should be unrepresentable.
- Set `parallel_tool_calls: false` for MVP.
- After executing tool(s), append outputs and re-submit to obtain the final narrative.
- Never upload or stream raw PDF bytes to the LLM. Only pass short extracted snippets as needed.
- Render a **Dice audit** footer per the fixed grammar on every GM message.
- Journal is the save file. YAML front-matter must remain valid and round-trippable.

---

## 5. Open Questions for Handoff Q&A
- Confirm exact label text for Settings toggles in UI.
- Confirm any hard limits for rule excerpt length in UI rendering beyond the enforced 256-char cap.
