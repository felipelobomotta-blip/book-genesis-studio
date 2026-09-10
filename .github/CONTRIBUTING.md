# Contributing to Book Genesis

Book Genesis is an open-source project. Contributions are welcome.

## What We Need

### Skill Improvements
- Better anti-AI pattern detection
- Genre-specific calibrations (we have 8 genres — more are welcome)
- Improved emotional rendering techniques
- Voice inhabitation methods

### Knowledge Base
- Bestseller analysis data (add to `knowledge/`)
- Genre-specific benchmarks
- Anti-AI pattern examples from published books

### Translations
- Install scripts for other platforms
- Skill translations (adapting literary conventions for non-English markets)

### Testing
- Run the pipeline on different genres and report results
- Compare Genesis Score predictions against actual sales data
- Identify new AI patterns not in the 20-pattern scan

## How to Contribute

1. Fork the repo
2. Create a branch (`git checkout -b feature/your-feature`)
3. Make your changes
4. Test: install locally and run at least one skill
5. Submit a PR with:
   - What you changed
   - Why
   - How you tested it

## Skill File Format

Skills live in `skills/<skill-name>/SKILL.md` with frontmatter:

```markdown
---
name: skill-name
description: What this skill does in one sentence.
---

[Skill instructions here]
```

## Code of Conduct

Be direct. Be useful. Don't waste people's time.

## Questions?

Open an issue. Keep it specific.
