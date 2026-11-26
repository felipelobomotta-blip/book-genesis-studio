"""Deterministic prose and machine-tell telemetry for audit and revision planning.

This module computes objective candidate counts and rhythm statistics directly
from accepted manuscript prose. It makes no model calls, assigns no scores,
and never proves authorship or literary quality. Every candidate count must be
verified in context by the auditor or revision planner before issuing a ticket.
"""
from __future__ import annotations

import math
from pathlib import Path
import re
import unicodedata

from evidence_passages import evidence_passages


_PT_DIALOGUE_START = re.compile(r"^\s*(?:—|–|-)")
_SCENE_BREAK = re.compile(r"^\s*(?:[-*_]\s*){3,}$")
_HEADING = re.compile(r"^\s*#{1,6}\s+")
_SENTENCE_SPLIT = re.compile(r"[.!?]+(?:\s+|$)")

_PT_DASH_RE = re.compile(r"—|–|--| - ")
_EN_DASH_RE = re.compile(r"—|--| - ")

_PT_NEGATION_SEMI = re.compile(r"(?i)\bnão\b[^.;!?]*;")
_PT_NEGATION_OTHER = re.compile(
    r"(?i)\bnão\b[^.;!?]*,\s*(?:mas|e sim)\s+"
    r"|\bnão\s+(?:é|era|foi|seria)\b[^.;!?]*[.,]\s*(?:é|era|foi|seria)\b"
    r"|\bnão se trata de\b|\btrata-se de\b"
    r"|\bmais do que\b[^.;!?]*,\s*(?:é|era|foi)\b"
)
_PT_NAO_HOUVE = re.compile(r"(?i)\bnão houve\b")
_PT_EMOTION_LABELS = re.compile(
    r"(?i)(?:\b(?:sentiu|sentia|sente|uma (?:onda|pontada|sensação|mistura) de|tomad[oa] por)\b[^.!?]{0,40}"
    r"(?:tristeza|raiva|medo|pavor|angústia|culpa|vergonha|alívio|alegria|felicidade|"
    r"solidão|saudade|desespero|esperança|ciúme|mágoa|luto|pânico|ódio))"
)
_PT_GERUND = re.compile(r"(?i)\b(?!quando\b|lindo\b|segundo\b|fundo\b|mundo\b)[a-zà-ú]+(?:ando|endo|indo|ondo)\b")
_PT_HEDGE = re.compile(
    r"(?i)\b(?:quase|talvez|de alguma forma|de algum modo|de certa forma|de certo modo|"
    r"meio que|uma espécie de|um tipo de|como se|parecia|parecesse|um pouco|algo como)\b"
)
_PT_MORAL_END = re.compile(
    r"(?i)\b(?:afinal|no fundo|de alguma forma|talvez fosse isso|só (?:muitos )?(?:anos )?depois|"
    r"mal sabia|e foi assim que|aquilo bastava|entenderia que)\b"
)

_EN_NEGATION = re.compile(
    r"(?i)\bnot\b[^.;!?]*[.;]\s*(?:not\b[^.;!?]*[.;]\s*)?(?:but|just|only|merely|a |an |the )"
    r"|\bit wasn't\b[^.;!?]*[.,;]\s*(?:it was|just)\b"
    r"|\bnot because\b[^.;!?]*,\s*but because\b"
)
_EN_ABSENCE = re.compile(r"(?i)\bthere was no (?:answer|response|sound|reply|movement|tears)\b")
_EN_EMOTION_LABELS = re.compile(
    r"(?i)\b(?:felt|washed over|surged through|a (?:wave|pang|surge|rush|flicker|sense) of)\b[^.!?]{0,35}"
    r"\b(?:sadness|anger|fear|dread|guilt|shame|relief|joy|loneliness|grief|despair|hope|rage|panic)\b"
)
_EN_HEDGE = re.compile(
    r"(?i)\b(?:almost|perhaps|somehow|sort of|kind of|a bit|seemed to|as if|nearly|somewhat|maybe)\b"
)
_EN_MORAL_END = re.compile(
    r"(?i)\b(?:in the end|perhaps that was|only later would|she would not understand until|"
    r"he would not understand until|and somehow,? that was enough|that was the lesson|little did)\b"
)


def language_code(language: str | None) -> str | None:
    if not language:
        return None
    normalized = "".join(
        c for c in unicodedata.normalize("NFKD", language.casefold()) if not unicodedata.combining(c)
    ).strip().replace("_", "-")
    if normalized == "pt" or normalized.startswith(("pt-", "portugues", "brazilian portuguese")):
        return "pt-br"
    if normalized == "en" or normalized.startswith(("en-", "english")):
        return "en"
    return None


def _strip_comments(text: str) -> str:
    return re.sub(r"<!--.*?-->", "", text, flags=re.S)


def _word_count(text: str) -> int:
    cleaned = re.sub(r"—|–", " ", text)
    return len(re.findall(r"\S+", cleaned))


def _narration_sentences(paragraphs: list[str]) -> list[str]:
    joined = " ".join(paragraphs)
    cleaned = re.sub(r"—|–", " ", joined)
    return [s.strip() for s in _SENTENCE_SPLIT.split(cleaned) if _word_count(s) > 0]


def _sentence_rhythm(sentences: list[str]) -> dict:
    lengths = [_word_count(s) for s in sentences]
    if not lengths:
        return {"sentences": 0, "mean": 0.0, "sd": 0.0, "min": 0, "max": 0, "metronome_flag": False}
    mean = sum(lengths) / len(lengths)
    variance = sum((n - mean) ** 2 for n in lengths) / len(lengths)
    sd = math.sqrt(variance)
    return {
        "sentences": len(lengths),
        "mean": round(mean, 2),
        "sd": round(sd, 2),
        "min": min(lengths),
        "max": max(lengths),
        "metronome_flag": len(lengths) >= 10 and sd < 5.0,
    }


def _split_paragraphs(body: str, code: str) -> tuple[list[str], list[str], list[str]]:
    raw_blocks = re.split(r"\r?\n\s*\r?\n", _strip_comments(body))
    paragraphs: list[str] = []
    for block in raw_blocks:
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if not lines:
            continue
        if code == "pt-br" and any(_PT_DIALOGUE_START.match(line) for line in lines):
            for line in lines:
                if not _HEADING.match(line) and not _SCENE_BREAK.match(line):
                    paragraphs.append(line)
        else:
            joined = " ".join(lines)
            if not _HEADING.match(joined) and not _SCENE_BREAK.match(joined):
                paragraphs.append(joined)
    narration: list[str] = []
    dialogue: list[str] = []
    for p in paragraphs:
        if code == "pt-br":
            if _PT_DIALOGUE_START.match(p):
                dialogue.append(p)
            else:
                narration.append(p)
        else:
            quoted = re.findall(r'["“][^"”]+["”]', p)
            if quoted:
                dialogue.append(" ".join(quoted))
                outside = re.sub(r'["“][^"”]+["”]', " ", p).strip()
                if outside:
                    narration.append(outside)
            else:
                narration.append(p)
    return paragraphs, narration, dialogue


def analyze_chapter(chapter_name: str, text: str, language: str | None) -> dict:
    code = language_code(language)
    if code is None:
        return {
            "chapter": chapter_name,
            "supported": False,
            "note": "No language-specific machine-tell telemetry is defined for this language.",
        }
    paragraphs, narration, dialogue = _split_paragraphs(text, code)
    nwords = sum(_word_count(p) for p in narration)
    dwords = sum(_word_count(p) for p in dialogue)
    total_words = nwords + dwords
    per_1k = (lambda n: round(n * 1000.0 / nwords, 2)) if nwords > 0 else (lambda _n: 0.0)
    sentences = _narration_sentences(narration)
    rhythm = _sentence_rhythm(sentences)
    last_paragraph = paragraphs[-1] if paragraphs else ""
    first_words = " ".join(re.findall(r"\S+", paragraphs[0])[:6]).casefold() if paragraphs else ""
    last_words = " ".join(re.findall(r"\S+", last_paragraph)[-6:]).casefold() if last_paragraph else ""

    if code == "pt-br":
        dash_counts = [len(_PT_DASH_RE.findall(p)) for p in narration]
        dashes = sum(dash_counts)
        over_2_dashes = sum(1 for n in dash_counts if n > 2)
        neg_semi = sum(len(_PT_NEGATION_SEMI.findall(p)) for p in narration)
        neg_other = sum(len(_PT_NEGATION_OTHER.findall(p)) for p in narration)
        absence = sum(len(_PT_NAO_HOUVE.findall(p)) for p in narration)
        emotion_labels = sum(len(_PT_EMOTION_LABELS.findall(p)) for p in narration)
        gerund_chains = sum(1 for s in sentences if len(_PT_GERUND.findall(s)) >= 3)
        hedge_stacks = sum(1 for s in sentences if len(_PT_HEDGE.findall(s)) >= 2)
        moral_end = bool(_PT_MORAL_END.search(last_paragraph))
        exceeded = []
        if per_1k(dashes) > 3.0 or over_2_dashes > 0:
            exceeded.append("narration_dashes")
        if neg_semi > 0 or neg_other > 1:
            exceeded.append("corrective_negation")
        if absence > 1:
            exceeded.append("nao_houve")
        if per_1k(emotion_labels) > 2.0:
            exceeded.append("emotion_labels")
        if rhythm["metronome_flag"]:
            exceeded.append("metronome_rhythm")
        if gerund_chains > 2:
            exceeded.append("gerund_chains")
        if hedge_stacks > 2:
            exceeded.append("hedge_stacking")
        if moral_end:
            exceeded.append("moral_at_the_door_candidate")
        return {
            "chapter": chapter_name,
            "supported": True,
            "language_profile": "pt-br",
            "narration_words": nwords,
            "dialogue_words": dwords,
            "dialogue_ratio": round(dwords / total_words, 3) if total_words else 0.0,
            "narration_dashes": dashes,
            "narration_dash_rate_per_1k": per_1k(dashes),
            "paragraphs_over_2_narration_dashes": over_2_dashes,
            "corrective_negation_semicolon": neg_semi,
            "corrective_negation_other": neg_other,
            "nao_houve_count": absence,
            "emotion_label_candidates": emotion_labels,
            "emotion_label_rate_per_1k": per_1k(emotion_labels),
            "gerund_chain_sentences": gerund_chains,
            "hedge_stack_sentences": hedge_stacks,
            "ending_moral_candidate": moral_end,
            "sentence_rhythm": rhythm,
            "candidates_above_default_ceiling": exceeded,
            "opening_fingerprint": first_words,
            "closing_fingerprint": last_words,
        }

    dash_counts = [len(_EN_DASH_RE.findall(p)) for p in narration]
    dashes = sum(dash_counts)
    over_2_dashes = sum(1 for n in dash_counts if n > 2)
    negations = sum(len(_EN_NEGATION.findall(p)) for p in narration)
    absence = sum(len(_EN_ABSENCE.findall(p)) for p in narration)
    emotion_labels = sum(len(_EN_EMOTION_LABELS.findall(p)) for p in narration)
    hedge_stacks = sum(1 for s in sentences if len(_EN_HEDGE.findall(s)) >= 2)
    moral_end = bool(_EN_MORAL_END.search(last_paragraph))
    exceeded = []
    if per_1k(dashes) > 4.0 or over_2_dashes > 0:
        exceeded.append("narration_dashes")
    if negations > 1:
        exceeded.append("corrective_negation")
    if per_1k(emotion_labels) > 2.0:
        exceeded.append("emotion_labels")
    if rhythm["metronome_flag"]:
        exceeded.append("metronome_rhythm")
    if hedge_stacks > 2:
        exceeded.append("hedge_stacking")
    if moral_end:
        exceeded.append("moral_at_the_door_candidate")
    return {
        "chapter": chapter_name,
        "supported": True,
        "language_profile": "en",
        "narration_words": nwords,
        "dialogue_words": dwords,
        "dialogue_ratio": round(dwords / total_words, 3) if total_words else 0.0,
        "narration_dashes": dashes,
        "narration_dash_rate_per_1k": per_1k(dashes),
        "paragraphs_over_2_narration_dashes": over_2_dashes,
        "corrective_negation_candidates": negations,
        "absence_as_event_candidates": absence,
        "emotion_label_candidates": emotion_labels,
        "emotion_label_rate_per_1k": per_1k(emotion_labels),
        "hedge_stack_sentences": hedge_stacks,
        "ending_moral_candidate": moral_end,
        "sentence_rhythm": rhythm,
        "candidates_above_default_ceiling": exceeded,
        "opening_fingerprint": first_words,
        "closing_fingerprint": last_words,
    }


def analyze_manuscript(chapter_paths: list[Path], language: str | None) -> dict:
    """Compute neutral per-chapter prose telemetry across a complete snapshot."""
    code = language_code(language)
    rows = [
        analyze_chapter(path.name, path.read_text(encoding="utf-8"), language)
        for path in sorted(chapter_paths, key=lambda p: p.name)
    ]
    if code is None:
        return {
            "language": language,
            "profile": None,
            "supported": False,
            "interpretation": (
                "No language-specific machine-tell profile is shipped for this language. "
                "Do not apply English punctuation or tell ceilings. Evaluate natural prose in context."
            ),
            "chapters": rows,
        }
    ranked = sorted(
        rows,
        key=lambda row: (len(row.get("candidates_above_default_ceiling", [])), row.get("narration_dash_rate_per_1k", 0.0)),
        reverse=True,
    )
    flagged_chapters = [row["chapter"] for row in ranked if row.get("candidates_above_default_ceiling")]
    return {
        "language": language,
        "profile": code,
        "supported": True,
        "interpretation": (
            "Deterministic candidate pattern telemetry measured from canonical chapter text. "
            "Not a literary score, verdict, or proof of authorship. Brazilian Portuguese dialogue "
            "travessões are excluded from narration dash counts. Verify every candidate in context "
            "before issuing a ticket."
        ),
        "chapters_with_candidates_above_default": flagged_chapters,
        "worst_five_candidates": flagged_chapters[:5],
        "chapters": rows,
    }
