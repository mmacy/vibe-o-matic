# AI Game Master

A client-only single-page application for running rules-faithful B/X D&D-compatible tabletop RPG sessions with an AI Game Master.

## Features

- **Client-only**: No server required, runs entirely in your browser
- **BYOK (Bring Your Own Key)**: Supply your own OpenAI API key at runtime
- **Rules-faithful**: GM strictly adheres to uploaded rules and module PDFs
- **Tool-driven dice**: All dice rolls use function tools, never simulated
- **Journal system**: Markdown-based save files with YAML front-matter
- **Local PDF parsing**: PDFs converted to text locally, never sent to LLM
- **Dark mode**: Easy on the eyes for long sessions
- **Homebrew support**: Optional toggles for common house rules

## Tech Stack

- **Framework**: React 18 + TypeScript
- **Build**: Vite
- **Styling**: Tailwind CSS
- **State**: Zustand
- **Validation**: Zod
- **PDF**: pdf.js
- **AI**: OpenAI Responses API
- **Testing**: Vitest + Playwright

## Prerequisites

- Node.js 20+
- pnpm
- OpenAI API key

## Installation

```bash
# Clone the repository
git clone <repo-url>
cd ai-gm

# Install dependencies
pnpm install

# Run development server
pnpm dev
```

## Usage

1. **Enter API key**: Click "Enter API key" and provide your OpenAI API key
2. **Upload materials**:
   - Rules PDF: Your B/X or OSE rules document
   - Module PDF: The adventure module you want to run
   - Journal (optional): Resume a previous session
3. **Configure settings**: Open Settings drawer to enable homebrew rules
4. **Start session**: Click "Start session" to begin
5. **Play**: Interact with the GM through the chat interface
6. **Save**: Download your journal anytime from the Journal drawer

## Scripts

```bash
pnpm dev          # Start development server
pnpm build        # Build for production
pnpm preview      # Preview production build
pnpm lint         # Run ESLint
pnpm format       # Format code with Prettier
pnpm test         # Run unit tests
pnpm test:watch   # Run tests in watch mode
pnpm coverage     # Generate test coverage report
pnpm e2e          # Run E2E tests with Playwright
```

## Architecture

### Directory Structure

```
src/
├── app/
│   ├── components/      # React components
│   │   ├── ChatPanel.tsx
│   │   ├── JournalDrawer.tsx
│   │   ├── SettingsDrawer.tsx
│   │   └── ...
│   ├── state/          # State management
│   │   ├── store.ts    # Zustand store
│   │   └── schema.ts   # Zod schemas
│   └── App.tsx
├── lib/
│   ├── openai/         # OpenAI client & orchestration
│   ├── pdf/            # PDF extraction & rule excerpts
│   ├── dice/           # Dice parser & roller
│   ├── journal/        # Journal parsing & serialization
│   └── ui/             # UI utilities
└── pages/
    └── Home.tsx
```

### Key Concepts

**Journal as Save File**
- Markdown file with YAML front-matter
- Contains party info, session log, and metadata
- Downloadable and reloadable

**Tool-Driven Dice**
- All dice rolls use the `roll_dice` function tool
- GM never simulates or makes up results
- Each response includes a "Dice audit" section

**Rules Primacy**
- GM only uses uploaded rules and module
- Refuses unsupported actions with rule excerpts (≤256 chars)
- No assumptions from other game systems

**Privacy & Security**
- API key stored only in volatile memory
- Cleared on tab close
- No telemetry or external tracking
- PDFs parsed locally, never sent to LLM

## Testing

### Unit Tests
Core modules have comprehensive test coverage:
- Dice parser and roller
- PDF extraction and excerpt selector
- Journal parsing and serialization
- OpenAI output aggregation

```bash
pnpm test
pnpm coverage  # View coverage report
```

### E2E Tests
Playwright tests cover:
- UI navigation
- Settings and Journal drawers
- Setup workflow

```bash
pnpm e2e
```

## CI/CD

GitHub Actions workflow runs on every push/PR:
- Linting
- Build verification
- Unit tests with coverage
- E2E tests (headless)

## License

MIT

## Contributing

This is an MVP implementation. For bugs or feature requests, please open an issue.

## Acknowledgments

Built according to the AI Game Master PRD + Technical Design (MVP v1.3)
