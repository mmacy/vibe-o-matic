# Test Fixtures

This directory contains sample files for testing the AI Game Master application.

## Files

### sample-journal.md
A complete example of a journal file with YAML front-matter showing:
- Party of two characters (Fighter and Magic-User)
- Session log with multiple entries
- Character details and inventory
- Proper YAML structure for parsing

## Creating Mock PDFs

For E2E testing, you would need actual PDF files. You can create minimal PDFs using:

1. **Rules PDF**: A simple document containing basic B/X rules like:
   - Character creation
   - Combat rules
   - Saving throws
   - Spell descriptions

2. **Module PDF**: A simple adventure module with:
   - Room descriptions
   - Monster stat blocks (AC, HD, HP, etc.)
   - Treasure tables

These PDFs can be generated using tools like LaTeX, LibreOffice, or online PDF creators.

For unit testing, the PDF parsing is mocked, so actual PDFs are not required.
