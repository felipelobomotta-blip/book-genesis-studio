"""Carry the existing skill's allowed craft material into tool-free roles.

These are separate reading views, never modifications of the references. The
draft writer does not receive revision moves, AI-tell checks, scoring criteria
or prior verdicts. Editors can use the existing repair techniques after prose
exists and only for their assigned tickets. Blind readers receive none of it.
"""
import re
import unicodedata
from editorial_context import method_section


def _read(skill, name):
    return (skill / "references" / name).read_text(encoding="utf-8")


def _editor_view(text):
    # Reference code samples are commands for a human host, not actions for a
    # read-only native role. Rubric cross-links belong to evaluators, not editors.
    text = re.sub(r"^```[^\n]*\n.*?^```[ \t]*$", "", text, flags=re.M | re.S)
    return "\n".join(line for line in text.splitlines() if not re.search(r"scoring/|\brubric\b", line, re.I)).strip()


def draft_knowledge(skill):
    text = _read(skill, "specialists/prose-craft.md")
    start = text.index("## 1. Openings")
    end = text.index("## 6. Revision moves")
    return {"use": "Optional craft knowledge from the existing skill, not a quota or a live checklist. "
        "Write the scene first. Do not run after-draft checks while composing, imitate a named author, "
        "or open referenced files. The book's voice and character cards govern this chapter.",
        "specialists/prose-craft.md#sections-1-5": text[start:end].strip(),
        "integrated_method": method_section(skill, 'Drafting')}


def language_tells(language):
    normalized = "".join(c for c in unicodedata.normalize("NFKD", language.casefold()) if not unicodedata.combining(c)).strip().replace("_", "-")
    if normalized == "pt" or normalized.startswith(("pt-", "portugues", "brazilian portuguese")):
        return "patterns/ai-tells-pt-br.md"
    if normalized == "en" or normalized.startswith(("en-", "english")):
        return "patterns/ai-tells-en.md"
    return None


def revision_knowledge(skill, language):
    paths = ["specialists/prose-craft.md", "patterns/prose.md", "patterns/structure-and-emotion.md", "patterns/causal-evidence.md"]
    tells = language_tells(language)
    if tells:
        paths.append(tells)
    return {"use": "Existing craft and repair knowledge for Phase 5 only. Use a technique only when the assigned "
        "ticket and its source evidence call for it. Preserve voice, earned exceptions and facts. "
        "Reference examples and measurements are guidance, not quotas or a mandate to imitate their authors. "
        "No tools, further file access or unticketed changes. Do not assign or optimize a score.",
        "language_specific_tells": tells or "No language-specific reference is shipped for this language; do not substitute English rules.",
        "integrated_method": method_section(skill, 'Revision'),
        "references": {name: _editor_view(_read(skill, name)) for name in paths}}
