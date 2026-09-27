#!/usr/bin/env python3
"""Fail if forbidden substrings appear outside an explicit allow list."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TERMS_FILE = ROOT / "FORBIDDEN_TERMS.txt"
SKIP_PARTS = {".git", "__pycache__", ".grok"}
SHORT_WORD = {"wfc", "wim", "slc", "clt", "phx", "ssn", "jpm"}


def load_terms() -> list[str]:
    terms = []
    for line in TERMS_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        terms.append(line.lower())
    return terms


def allowed(rel: Path) -> bool:
    s = str(rel).replace("\\", "/")
    if s == "FORBIDDEN_TERMS.txt":
        return True
    if s.endswith("check_forbidden_terms.py"):
        return True
    return False


def main() -> int:
    terms = load_terms()
    hits = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(p in path.parts for p in SKIP_PARTS):
            continue
        if path.suffix.lower() in {".duckdb", ".db", ".pyc"}:
            continue
        rel = path.relative_to(ROOT)
        if allowed(rel):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore").lower()
        except Exception:
            continue
        for term in terms:
            if term in SHORT_WORD or len(term) <= 3:
                if re.search(rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])", text):
                    hits.append(f"{rel}: word '{term}'")
            elif term in text:
                hits.append(f"{rel}: '{term}'")
    if hits:
        print("FORBIDDEN TERM HITS:")
        for h in hits:
            print(" ", h)
        return 1
    print("forbidden-term check passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
