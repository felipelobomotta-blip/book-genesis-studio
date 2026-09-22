# Contributing

Book Genesis welcomes improvements to the skill's instructions, the patterns library, the installer, tests, casebook entries and documentation.

## Setup

```bash
git clone https://github.com/felipelobomotta-blip/book-genesis-studio.git
cd book-genesis-studio
python runner/installer.py verify-suite
python -m unittest discover -s tests -v
```

No API key is needed. Nothing in this repository calls a model.

## Where things live

- `skills/book-genesis/` is the product. Edit instructions there.
- `skills/book-genesis/references/roles/` is the only source for the blind reader and auditor. After editing a role file, run `python runner/installer.py generate-agents` and commit the regenerated `agents/` files. Never edit `agents/` by hand; CI fails when it drifts.
- `skills/book-genesis/references/patterns/` holds the measured patterns. Every new rule names its comparable book, author or study.
- `skills/beta-reader/`, `skills/editorial-package/` and `skills/literary-agent-panel/` must stay standalone: no reference to the core, its phases or its files.
- `runner/` is the installer. Standard library only unless a dependency earns its cost.

## Rules the suite check enforces

- Every `references/...` path a skill mentions exists inside that skill.
- No shipped skill points outside itself (`skills/<other>/`, `knowledge/`, desktop paths, scripts that do not ship).
- No shipped skill names a retired skill as something to run.
- The pipeline keeps its order, its adversarial audit and its revision loop.
- `name` matches the folder and `description` is 1 to 1,024 characters.

## Rules reviewers enforce

- Never skip the adversarial audit before scoring.
- Critics never see targets or earlier scores; the writer never sees the rubric.
- Revision stays bounded: three passes per gate.
- No promise of sales or bestseller status.
- Book and author-facing messages follow the book's language; the skill's own files stay in English.

## Pull requests

Include the problem, the behavior change, the phases or roles affected, and test evidence. For changes to instructions, a short before and after from a real run is the best evidence; say which host and model produced it.

Keep manuscripts, API keys, session logs and private reader data out of commits.
