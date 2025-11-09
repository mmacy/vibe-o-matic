# AI Game Master MVP

## Summary
<!-- Brief description of changes -->

## Checklist

### Functionality
- [ ] Upload rules PDF(s) and module PDF with local parsing
- [ ] Upload optional journal and parse YAML front-matter
- [ ] BYOK modal for OpenAI API key (volatile, cleared on tab close)
- [ ] Start session: resume from journal or run character creation
- [ ] Chat loop with OpenAI Responses API
- [ ] Tool-driven dice rolls (never simulated)
- [ ] Dice audit footer on all GM responses
- [ ] Settings drawer with homebrew toggles
- [ ] Journal drawer with download functionality

### Technical Requirements
- [ ] All PDFs parsed locally, never sent to LLM
- [ ] Responses API with pinned model snapshot
- [ ] `parallel_tool_calls: false` for determinism
- [ ] Tool execution and round-trip pattern implemented
- [ ] Refusal policy with ≤256 char excerpts
- [ ] Journal as sole save file (Markdown + YAML)

### Testing
- [ ] Unit tests for core modules (≥90% coverage)
- [ ] E2E smoke test with Playwright
- [ ] All tests passing in CI

### Documentation
- [ ] README with setup instructions
- [ ] Sample assets included
- [ ] Architecture overview

## Screenshots
<!-- Add screenshots here -->

## Demo
<!-- Add demo GIF or video here -->

## Notes
<!-- Any additional context -->
