#!/usr/bin/env python3
"""Score answers to eval/questions.jsonl (DEC-012).

Usage:  python eval/score.py answers.jsonl [--questions eval/questions.jsonl]

The answers file has one JSON line per question: {"id": "Q01", "answer": "yes"}.
A missing or malformed answer counts as wrong; for a repeated id the last line wins. Normalisation, by answer type:
    token    case, surrounding space, backticks, quotes and a final full stop are ignored
    yes-no   yes, y, true, no, n, false (any case, trailing full stop ignored)
    number   "3", "3.0", 3 and " 3 " are equal
    set      a list or a comma/semicolon/"and" separated string; order and case are ignored
Standard library only; Python 3.10 or newer.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable, Sequence

DEFAULT_QUESTIONS = Path(__file__).resolve().parent / "questions.jsonl"
ANSWER_TYPES = ("token", "yes-no", "number", "set")
_YES = {"yes", "y", "true"}
_NO = {"no", "n", "false"}


def _clean(text: str) -> str:
    text = re.sub(r"\s+", " ", text.strip()).casefold()
    text = text.strip("`'\"")
    return text.rstrip(".").strip()


def normalize(answer_type: str, value: Any) -> Any:
    """The comparable form of an answer, or None when it cannot be read as that type."""
    if answer_type == "token":
        return _clean(value) if isinstance(value, (str, int, float)) and not isinstance(value, bool) else None
    if answer_type == "yes-no":
        if isinstance(value, bool):
            return "yes" if value else "no"
        text = _clean(value) if isinstance(value, str) else ""
        if text in _YES:
            return "yes"
        if text in _NO:
            return "no"
        return None
    if answer_type == "number":
        if isinstance(value, bool):
            return None
        try:
            number = float(_clean(value).replace(",", "")) if isinstance(value, str) else float(value)
        except (TypeError, ValueError):
            return None
        return int(number) if number == int(number) else number
    if answer_type == "set":
        if isinstance(value, str):
            parts: Iterable[Any] = re.split(r"\s*(?:,|;|\band\b)\s*", value)
        elif isinstance(value, (list, tuple)):
            parts = value
        else:
            return None
        items = set()
        for part in parts:
            if not isinstance(part, str):
                return None
            cleaned = _clean(part)
            if cleaned:
                items.add(cleaned)
        return frozenset(items)
    raise ValueError(f"unknown answer type: {answer_type}")


def is_correct(question: dict, answer: Any) -> bool:
    got = normalize(question["answer_type"], answer)
    want = normalize(question["answer_type"], question["key"])
    return got is not None and got == want


def load_questions(path: Path = DEFAULT_QUESTIONS) -> list[dict]:
    questions = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            questions.append(json.loads(line))
    return questions


def load_answers(path: Path) -> dict[str, Any]:
    """Answer by question ID. Lines that are not a JSON object with `id` are skipped."""
    answers: dict[str, Any] = {}
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except ValueError:
            continue
        if isinstance(item, dict) and isinstance(item.get("id"), str) and "answer" in item:
            answers[item["id"]] = item["answer"]
    return answers


def score(questions: Sequence[dict], answers: dict[str, Any]) -> dict:
    """Per-question results and totals, in total and by category."""
    results = []
    by_category: dict[str, list[int]] = {}
    for question in questions:
        ok = question["id"] in answers and is_correct(question, answers[question["id"]])
        results.append({"id": question["id"], "category": question["category"], "correct": ok})
        tally = by_category.setdefault(question["category"], [0, 0])
        tally[0] += 1 if ok else 0
        tally[1] += 1
    return {
        "correct": sum(1 for r in results if r["correct"]),
        "total": len(results),
        "results": results,
        "by_category": {name: {"correct": c, "total": t} for name, (c, t) in by_category.items()},
    }


def render(result: dict) -> str:
    lines = [f"{r['id']} {r['category']:<10} {'ok' if r['correct'] else 'wrong'}" for r in result["results"]]
    for name, tally in result["by_category"].items():
        lines.append(f"{name}: {tally['correct']}/{tally['total']}")
    lines.append(f"total: {result['correct']}/{result['total']}")
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None, out=None) -> int:
    parser = argparse.ArgumentParser(prog="score", description="Score an answers file against the eval questions.")
    parser.add_argument("answers", type=Path)
    parser.add_argument("--questions", type=Path, default=DEFAULT_QUESTIONS)
    args = parser.parse_args(argv)
    stream = out if out is not None else sys.stdout
    try:
        questions = load_questions(args.questions)
        answers = load_answers(args.answers)
    except (OSError, ValueError) as exc:
        sys.stderr.write(f"score: {exc}\n")
        return 1
    stream.write(render(score(questions, answers)) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
