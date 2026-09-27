#!/usr/bin/env python3
"""Score spike-window phrases with Fightin' Words + c-TF-IDF.

SYNTHETIC DATA ONLY. Reads data/call_metadata.csv and data/transcripts/.
"""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "output"

ALPHA0 = 500.0
NGRAM_N = (1, 2, 3)
MIN_TOTAL = 8
DRIVER_Z_WEIGHT = 0.65
DRIVER_C_WEIGHT = 0.35
TOP_N = 25
QUOTES_PER = 2

STOP_UNI = {
    "a", "an", "the", "and", "or", "to", "of", "in", "on", "for", "is", "it",
    "i", "you", "we", "my", "your", "this", "that", "was", "be", "are", "am",
    "at", "as", "by", "from", "with", "not", "no", "yes", "um", "uh", "okay",
    "ok", "please", "can", "just", "so", "if", "do", "did", "have", "has",
    "will", "would", "me", "im", "dont", "its", "there", "here", "they",
    "them", "our", "out", "up", "then", "than", "but", "about", "into",
    "agent", "caller", "ivr", "quillmere", "service", "thanks",
    "thank", "calling", "help", "how", "does", "really",
}

# Drop any n-gram that is wrap-up or channel debris.
STOP_ANY = {
    "caller", "agent", "ivr", "thanks", "thank", "really", "help",
    "menu", "speak", "person", "okay", "quillmere",
}

# Unigrams allowed to stand alone on the leadership table.
KEEP_UNI = {
    "1099", "january_31", "irs", "cpa", "pending", "deadline",
    "brokerage", "neighbor", "february", "file", "taxes",
    "late", "waiting", "received", "posted", "mailed",
}

CONTENT = KEEP_UNI | {
    "waiting", "pending", "neighbor", "deadline", "received",
    "brokerage", "february", "passed", "needs", "file", "taxes",
    "late", "irs", "cpa", "1099", "january_31", "still", "when",
}

SKIP_TABLE = {
    "does not", "that does", "that does not", "not the", "i get",
    "get the", "i get the", "the 1099", "1099 i", "1099 this",
    "will i", "will i get", "when will i", "not really",
    "already passed i", "1099 this week",
}

# Spoken variants collapse into one token before ngrams.
CANON = [
    (re.compile(r"\bten\s+ninety\s+nine\b"), "1099"),
    (re.compile(r"\bten\s+nine\s+nine\b"), "1099"),
    (re.compile(r"\btax\s+form\b"), "1099"),
    (re.compile(r"\bjanuary\s+thirty\s+first\b"), "january_31"),
    (re.compile(r"\bjan(?:uary)?\s*31\b"), "january_31"),
    (re.compile(r"\bjanuary\s+31\b"), "january_31"),
    (re.compile(r"\bc\s*p\s*a\b"), "cpa"),
    (re.compile(r"\bi\s*r\s*s\b"), "irs"),
]

TOKEN_RE = re.compile(r"[a-z0-9_]+")


def normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"\[\d{2}:\d{2}\]\s*", " ", text)
    for rx, repl in CANON:
        text = rx.sub(repl, text)
    return text


def speaker_lines(raw: str, speaker: str = "CALLER") -> str:
    keep = []
    marker = f"] {speaker}:"
    marker_l = f"] {speaker.lower()}:"
    for line in raw.splitlines():
        if marker in line:
            keep.append(line.split(marker, 1)[1])
        elif marker_l in line:
            keep.append(line.split(marker_l, 1)[1])
    return " ".join(keep)


def tokens(text: str) -> list[str]:
    return TOKEN_RE.findall(normalize(text))


def ngrams(toks: list[str]) -> list[str]:
    out = []
    nmax = max(NGRAM_N)
    for n in range(1, nmax + 1):
        if n not in NGRAM_N:
            continue
        for i in range(0, len(toks) - n + 1):
            gram = toks[i : i + n]
            if any(g in STOP_ANY for g in gram):
                continue
            if n == 1 and gram[0] not in KEEP_UNI:
                continue
            if n == 1 and gram[0] in STOP_UNI:
                continue
            if n == 1 and len(gram[0]) < 3 and gram[0] not in {"1099", "cpa", "irs"}:
                continue
            out.append(" ".join(gram))
    return out


def minmax(arr: np.ndarray) -> np.ndarray:
    lo, hi = float(np.min(arr)), float(np.max(arr))
    if hi - lo < 1e-12:
        return np.zeros_like(arr, dtype=float)
    return (arr - lo) / (hi - lo)


def fightin_words(
    y_s: np.ndarray, y_b: np.ndarray, n_s: float, n_b: float, p: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    alpha_w = ALPHA0 * p
    num_s = y_s + alpha_w
    den_s = n_s + ALPHA0 - y_s - alpha_w
    num_b = y_b + alpha_w
    den_b = n_b + ALPHA0 - y_b - alpha_w
    # Guard empty prior mass.
    den_s = np.maximum(den_s, 1e-9)
    den_b = np.maximum(den_b, 1e-9)
    delta = np.log(num_s / den_s) - np.log(num_b / den_b)
    var = 1.0 / num_s + 1.0 / num_b
    z = delta / np.sqrt(var)
    return delta, z


def c_tfidf(y_s: np.ndarray, y_b: np.ndarray) -> np.ndarray:
    tf_s = y_s.astype(float)
    tf_all = y_s + y_b
    a = float(np.mean([y_s.sum(), y_b.sum()]))
    return tf_s * np.log(1.0 + a / np.maximum(tf_all, 1.0))


def example_quotes(
    phrase: str, records: list[dict], limit: int = QUOTES_PER
) -> list[dict]:
    # phrase uses canonical tokens; search a loose pattern on caller text
    parts = phrase.split()
    rx = re.compile(r"\s+".join(re.escape(p) for p in parts))
    found = []
    for rec in records:
        if rec["window"] != "spike":
            continue
        caller = speaker_lines(rec["text"], "CALLER")
        norm = normalize(caller)
        if not rx.search(norm):
            continue
        # grab a raw caller line that still looks related
        raw_line = ""
        for line in rec["text"].splitlines():
            if "] CALLER:" not in line:
                continue
            body = line.split("] CALLER:", 1)[1].strip()
            if any(p.replace("_", " ") in body.lower() for p in parts if p not in STOP_UNI):
                raw_line = body
                break
        if not raw_line:
            raw_line = caller[:180].strip()
        found.append({"call_id": rec["call_id"], "quote": raw_line})
        if len(found) >= limit:
            break
    return found


def main() -> None:
    meta = pd.read_csv(DATA / "call_metadata.csv")
    # Same unit a speech query would have given you: tax-document queue only.
    # Scoring the whole center just rediscovers that February has more 1099 calls.
    n_all = len(meta)
    meta = meta[meta["queue"] == "TAX_DOCS"].copy()
    print(f"scoring tax-doc queue only: {len(meta)} / {n_all} calls")
    records = []
    spike_grams: Counter[str] = Counter()
    base_grams: Counter[str] = Counter()

    for row in meta.itertuples(index=False):
        path = ROOT / row.transcript_path
        text = path.read_text(encoding="utf-8")
        caller = speaker_lines(text, "CALLER")
        grams = ngrams(tokens(caller))
        rec = {
            "call_id": row.call_id,
            "window": row.window,
            "theme": row.theme,
            "text": text,
            "grams": grams,
        }
        records.append(rec)
        bucket = spike_grams if row.window == "spike" else base_grams
        bucket.update(grams)

    vocab = sorted(set(spike_grams) | set(base_grams))
    y_s = np.array([spike_grams[w] for w in vocab], dtype=float)
    y_b = np.array([base_grams[w] for w in vocab], dtype=float)
    support = y_s + y_b
    keep = support >= MIN_TOTAL
    vocab = [w for w, k in zip(vocab, keep) if k]
    y_s, y_b = y_s[keep], y_b[keep]

    n_s = float(y_s.sum())
    n_b = float(y_b.sum())
    p = (y_s + y_b) / (n_s + n_b)
    delta, z = fightin_words(y_s, y_b, n_s, n_b, p)
    ctf = c_tfidf(y_s, y_b)

    # Rank on spike-distinctive side only for the leadership table.
    z_pos = np.clip(z, 0, None)
    driver = DRIVER_Z_WEIGHT * minmax(z_pos) + DRIVER_C_WEIGHT * minmax(ctf)

    df = pd.DataFrame(
        {
            "phrase": vocab,
            "n_spike": y_s.astype(int),
            "n_baseline": y_b.astype(int),
            "n_total": (y_s + y_b).astype(int),
            "log_odds_delta": np.round(delta, 4),
            "fightin_words_z": np.round(z, 4),
            "c_tfidf_spike": np.round(ctf, 4),
            "driver_score": np.round(driver, 4),
        }
    )
    df["ngram"] = df["phrase"].str.split().str.len()
    df["phrase_display"] = df["phrase"].str.replace("january_31", "january 31", regex=False)
    df = df.sort_values(["driver_score", "fightin_words_z"], ascending=False)

    def on_table(phrase: str) -> bool:
        if phrase in SKIP_TABLE:
            return False
        parts = phrase.split()
        if not any(p in CONTENT or p == "still" for p in parts):
            return False
        # Drop fragments that are 80% function words and no calendar/doc token.
        content_hits = [p for p in parts if p in KEEP_UNI or p in {"still", "when", "waiting", "needs", "passed"}]
        return bool(content_hits)

    top = df[(df["fightin_words_z"] > 0) & (df["phrase"].map(on_table))].head(TOP_N).copy()
    quotes = {}
    for rec in top.itertuples(index=False):
        quotes[rec.phrase_display] = example_quotes(rec.phrase, records)
    top["phrase"] = top["phrase_display"]

    OUT.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT / "driver_scores_full.csv", index=False)
    top.to_csv(OUT / "driver_scores.csv", index=False)
    (OUT / "example_quotes.json").write_text(
        json.dumps(quotes, indent=2) + "\n", encoding="utf-8"
    )

    summary = {
        "n_calls": int(len(meta)),
        "n_baseline": int((meta.window == "baseline").sum()),
        "n_spike": int((meta.window == "spike").sum()),
        "n_phrases_scored": int(len(df)),
        "top_phrase": None if top.empty else top.iloc[0]["phrase"],
        "top_z": None if top.empty else float(top.iloc[0]["fightin_words_z"]),
        "alpha0": ALPHA0,
        "driver_weights": {"z": DRIVER_Z_WEIGHT, "c_tfidf": DRIVER_C_WEIGHT},
    }
    (OUT / "score_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    print(f"scored {len(df)} phrases; top {len(top)} -> {OUT / 'driver_scores.csv'}")
    if not top.empty:
        print(top[["phrase", "fightin_words_z", "driver_score", "n_spike", "n_baseline"]].head(12).to_string(index=False))


if __name__ == "__main__":
    main()
