# AI Game Master — Coding Agent Kickoff Prompt (MVP v1.3)

Paste this prompt verbatim into your coding agent.

---

## Mission
Build, test, and open a PR with a feature-complete MVP of **AI Game Master** per the consolidated PRD+TD (MVP v1.3). Operate autonomously end-to-end: bootstrap repo, implement app, write tests, set up CI, and create the PR.

## Operate autonomously
- Assume full write access with `--dangerously-skip-permissions` enabled.
- Ask no humans for confirmation. Make choices that satisfy the spec with minimal complexity.
- Fetch any needed public docs for dependencies (OpenAI Responses API, pdf.js, Vite, React, etc.).
- If a decision is ambiguous, pick the simplest option that still meets requirements and document the choice in the PR description.

## Project location
- Initialize the project in: `REPO_ROOT/ai-gm/`

## Target platform and constraints
- **Client-only SPA**. No server. All PDF→text parsing is local. No raw PDFs sent to the LLM.
- **BYOK**: user pastes OpenAI API key at runtime. Never persist. Clear on tab close.
- **No multiplayer. No live web rules lookup. No RAG/vector DB.** Only one function tool: `roll_dice`.
- The GM must follow uploaded rules/module. Refuse unsupported actions with a ≤256-char rule excerpt from local text.
- Dice grammar: `NdM[+/-K]` with optional `L` (drop lowest).
- Dice audit footer: unordered list; each bullet `SOURCE ACTION TARGET: TOTAL (NdM+-KL)`; omit `TARGET` when none.
- Journal is the only save file: Markdown with YAML front-matter. Downloadable.

## Tech stack
- **Frontend**: React + TypeScript + Vite.
- **State**: minimal local state (Zustand or React Context). Keep it simple.
- **Styling**: Tailwind CSS. Dark mode default. Sentence case labels.
- **PDF parsing**: Mozilla pdf.js. Deterministic, on-device parsing.
- **OpenAI**: Responses API with a pinned snapshot. Handle heterogeneous `response.output`. Prefer `output_text` for aggregation when available. Set `parallel_tool_calls: false`.
- **Package manager**: pnpm.
- **Testing**: Vitest + Testing Library for UI; Playwright for a thin E2E smoke.
  - For core logic modules (PDF extractor, rule-excerpt trimmer, dice parser, journal serializer, output aggregator), write unit tests.
- **Lint/format**: ESLint + Prettier with strict settings.
- **CI**: GitHub Actions workflow running install, build, lint, unit tests, and E2E headless.

## Deliverables (must be in the PR)
1. Working SPA in `REPO_ROOT/ai-gm/` implementing all MVP features.
2. Automated tests with ≥ 90% branch coverage for non-UI core modules.
3. GitHub Actions CI passing on PR.
4. PR includes screenshots, a short demo GIF, and a concise arch/readme.
5. Minimal sample assets for manual verification: a tiny mock rules PDF and a tiny mock module PDF.
6. A sample journal Markdown file demonstrating YAML front-matter and session log.

## Repository layout (create all files)
```
ai-gm/
  README.md
  LICENSE
  .editorconfig
  .gitignore
  .npmrc
  package.json
  pnpm-lock.yaml
  tsconfig.json
  vite.config.ts
  postcss.config.js
  tailwind.config.js
  public/
    favicon.svg
  src/
    main.tsx
    index.css
    app/
      App.tsx
      routes.ts
      hooks/
      components/
        ChatPanel.tsx
        JournalDrawer.tsx
        SettingsDrawer.tsx
        TopBar.tsx
        DiceAudit.tsx
        KeyInputModal.tsx
        PdfUpload.tsx
      state/
        store.ts
        schema.ts           # Zod schemas for journal front-matter and tool I/O
      lib/
        openai/
          client.ts         # Responses API wrapper, snapshot pinning, output aggregation
          orchestration.ts  # tool-call loop, parallel_tool_calls=false, final response assembly
          tools.ts          # function tool metadata: roll_dice
        pdf/
          extract.ts        # pdf.js wrapper, OSE/BX stat-block heuristics, text slicing
          excerpt.ts        # 256-char rule excerpt selector
        dice/
          parse.ts          # NdM[+/-K], optional L; simplify unknowns
          roll.ts           # pure local roller used by the tool handler
        journal/
          serialize.ts      # YAML front-matter + sections
          parse.ts
        ui/
          formatting.ts     # sentence case helpers, dark mode defaults
    pages/
      Home.tsx
  e2e/
    example.spec.ts
    fixtures/
      rules-mock.pdf
      module-mock.pdf
  tests/
    dice.parse.spec.ts
    dice.roll.spec.ts
    pdf.extract.spec.ts
    pdf.excerpt.spec.ts
    journal.serialize.spec.ts
    openai.output-aggregate.spec.ts
  .github/
    pull_request_template.md
    workflows/ci.yml
```

## Functional requirements checklist
- [ ] Upload rules PDF(s) and one module PDF. Local parse to text blocks. Never send PDFs to LLM.
- [ ] Optional journal upload; display parsed YAML front-matter and logs.
- [ ] BYOK modal. Keep key only in memory. Clear on tab close/unload.
- [ ] Start session button: resume from journal if present; else run guided character creation per rules.
- [ ] Chat loop with OpenAI Responses API:
      - Build `instructions` capturing rule primacy, refusal policy with ≤256-char excerpt, dice via tool only, journal policy, and response formatting.
      - Include minimal relevant rule/module snippets.
      - Provide a single function tool, `roll_dice`, strict schema, `parallel_tool_calls: false`.
      - Execute tool calls locally and round-trip outputs to obtain a final narrative.
      - Render a **Dice audit** footer per grammar.
      - Append a one-line session summary to the journal.
- [ ] Settings drawer with two toggles: `ability_scores_4d6L` and `level1_max_hp`. Both default off.
- [ ] Download journal as Markdown with valid YAML front-matter.

## Tool: `roll_dice` contract
- **Input JSON (strict):**
  - `expr`: string, grammar `NdM[+/-K]` with optional `L`. Examples: `1d20+4`, `1d8`, `4d6L`.
  - `source`: string (actor/source of the roll).
  - `action`: string (what the roll represents).
  - `target`: string | empty when none.
- **Behavior:** parse `expr`; if unknown, simplify to nearest recognized form; compute result deterministically by RNG; return:
  - `total`: number
  - `detail`: string like `d20=[13]+4`
  - `normalized_expr`: canonicalized expression string
- The orchestrator inserts results into the assistant’s final “Dice audit” list.

## OpenAI orchestration notes
- Use the **Responses API** with a pinned model snapshot.
- Treat `response.output` as heterogeneous. Do not assume text at a fixed index. Provide an `aggregateOutputText()` helper and also iterate raw items.
- Set `parallel_tool_calls: false` for determinism.
- Round-trip tool calls: on function call, execute locally, append a `function_call_output` item, then request the final response.
- Enforce refusal semantics: if a player action is outside rules/module, reply with a brief denial plus a ≤256-char rule excerpt.

## Testing requirements
- Unit tests for: dice parse/roll, PDF extract, rule excerpt trimmer, journal parse/serialize, output aggregation, and the tool-call loop (mock OpenAI).
- UI tests: Chat happy-path with mocked OpenAI responses; Settings toggles; Journal download.
- E2E smoke with Playwright: upload mock PDFs, start session, receive at least one GM message with a valid Dice audit, download journal.

## CI requirements (GitHub Actions)
- Node 20 setup; pnpm install; build; lint; unit tests; Playwright in headless mode.
- Upload coverage artifact; fail on coverage < 90% for core modules.
- On PR: run full workflow and report status.

## Developer experience
- `pnpm` scripts:
  - `dev`, `build`, `preview`
  - `lint`, `format`
  - `test`, `test:watch`, `coverage`
  - `e2e`
- PR template with checklist mirroring this prompt. Include short demo GIF and screenshots.

## Initial commands for the agent
1) Create project skeleton and initialize git:
   - `mkdir -p REPO_ROOT/ai-gm && cd REPO_ROOT/ai-gm`
   - `git init -b main`
2) Initialize project:
   - `pnpm init`
   - Add Vite + React + TS, Tailwind, pdf.js, Zustand, Zod, OpenAI SDK (browser-compatible), Testing Library, Vitest, Playwright.
3) Configure Tailwind, ESLint, Prettier, tsconfig, vite config.
4) Implement modules and pages per the layout above.
5) Add tests and fixtures; wire CI workflow.
6) Record demo GIF and screenshots in PR.
7) Open a PR titled: `feat(ai-gm): MVP client-only SPA with BYOK, rules-first GM, dice tool, and journal`.

## Definition of done
- All acceptance criteria satisfied.
- All tests and CI pass.
- PR is open with artifacts and clear instructions to run locally:
  - Prereqs: Node 20+, pnpm.
  - Commands: `pnpm i`, `pnpm dev`, `pnpm build`, `pnpm test`, `pnpm e2e`.
- No secrets committed. BYOK enforced at runtime. Keys never persisted.
