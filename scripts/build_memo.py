#!/usr/bin/env python3
"""Write the short leadership memo from scored phrases + quotes."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output"
DATA = ROOT / "data"


def md_table(df: pd.DataFrame, cols: list[str]) -> str:
    sub = df[cols].copy()
    header = "| " + " | ".join(cols) + " |"
    sep = "| " + " | ".join("---" for _ in cols) + " |"
    rows = []
    for rec in sub.to_dict(orient="records"):
        cells = []
        for c in cols:
            v = rec[c]
            if isinstance(v, float):
                cells.append(f"{v:.2f}")
            else:
                cells.append(str(v))
        rows.append("| " + " | ".join(cells) + " |")
    return "\n".join([header, sep, *rows])


def main() -> None:
    scores = pd.read_csv(OUT / "driver_scores.csv")
    quotes = json.loads((OUT / "example_quotes.json").read_text(encoding="utf-8"))
    windows = json.loads((DATA / "windows.json").read_text(encoding="utf-8"))
    summary = json.loads((OUT / "score_summary.json").read_text(encoding="utf-8"))

    show = scores.head(12)[
        ["phrase", "fightin_words_z", "c_tfidf_spike", "driver_score", "n_spike", "n_baseline"]
    ].rename(
        columns={
            "fightin_words_z": "z (spike vs base)",
            "c_tfidf_spike": "c-TF-IDF",
            "driver_score": "driver",
            "n_spike": "n spike",
            "n_baseline": "n base",
        }
    )

    quote_lines = []
    seen_quotes = set()
    for phrase in scores["phrase"].head(20):
        for q in quotes.get(phrase, []):
            if q["quote"] in seen_quotes:
                continue
            seen_quotes.add(q["quote"])
            quote_lines.append(f"- `{q['call_id']}` / *{phrase}*: “{q['quote']}”")
            if len(quote_lines) >= 6:
                break
        if len(quote_lines) >= 6:
            break

    memo = f"""# Quillmere Service Center — mid-February 1099 timing

**Decision asked:** Do we change the tax-page FAQ and the tax IVR prompt, and is there enough evidence to send that copy through legal and risk?

**Answer:** Yes. Same-season phrase scores show the mid-February week is not “tax documents are up.” It is clients treating **January 31** as *their* deadline, then calling because last year’s language did not name the later brokerage furnish date.

**This packet is synthetic.** Fictional firm. No real accounts, agents, or employer data. Public IRS calendar dates are real; Quillmere volumes and quotes are generated.

## Windows

| Window | Dates | Role | Calls |
|---|---|---|---|
| Baseline (normal) | {windows['baseline']['start']} – {windows['baseline']['end']} | Same-year language before the standalone furnish date | {summary['n_baseline']} |
| Spike | {windows['spike']['start']} – {windows['spike']['end']} | Mid-February, still before the consolidated 1099-B date | {summary['n_spike']} |

Public furnish dates for TY2025 / season 2026 (weekend and Presidents Day shifts): standalone recipient copies **2026-02-02**; 1099-B / consolidated package **2026-02-17**. Details in `docs/deadlines.md`.

## What keyword volume would have said

A speech query on `1099` / `tax document` / `tax center` fires in both windows. Leadership would have seen “tax-doc contacts are elevated” and stopped there. That is how last year’s page stayed generic: *mailed by the IRS due date; brokerage may arrive later.*

Clients are still asking the same question this year. The previous action was not sufficient.

## What the driver scores say

Fightin’ Words z (spike vs baseline) plus spike-side c-TF-IDF. Method in `docs/method.md`. **Tax-document queue only**, caller channel only. ASR left noisy on purpose. A keyword query already selected these calls; the scores say what changed inside that query.

{md_table(show, list(show.columns))}

Read the table as: **the spike week is deadline talk**, not document-lookup talk. `1099` rises because more tax calls exist. The phrases that *only* exist in the spike week are the driver: `january 31` (73 vs 0), `pending`, `deadline`, `when will`, `irs`, `late`. `my cpa` is the pressure sitting on top of that calendar error.

## What the floor actually heard

{chr(10).join(quote_lines) if quote_lines else "- (no quotes; re-run scoring)"}

Agents are still reading last year’s script. In the spike transcripts they admit it: same FAQ, no named February date.

## Recommended change (fund this, in order)

1. **Tax-page FAQ — specific dates, two clocks.** Replace “by the IRS due date” with the two recipient dates for this season: standalone forms by **February 2**; consolidated / 1099-B packages by **February 17**. Say out loud that a household with brokerage activity should not expect the full package on the January 31 folklore date. Expect a legal and risk cycle. Budget time for that routing; do not treat a web edit as a same-day ops tweak.
2. **IVR tax branch — one sentence before the queue.** If the caller is in the tax-document menu during February 1–17, play the same two dates and offer the tax center path before a live agent. The current prompt (“visit the tax page; mailed by the IRS due date”) is what they already ignored.
3. **Agent talk-off after the page clears.** One screen: standalone vs consolidated, what “pending” in the tax center means, when to stop arguing the calendar. This is cheaper once legal has blessed the public sentence.

## What this packet is for

This is a **micro-analysis** inside tax season, not a season-long model and not an outcome study. It exists to justify funding the copy and IVR work. Phrase scores are the evidence that last year’s communication failed on the exact week clients always get confused.

Do not attach a volume-reduction target to this repo. If the change ships, measure the next season’s mid-February window the same way: same contrast, same phrases. That is a later packet.

## How to rebuild

```bash
python3 scripts/generate_synthetic_data.py
python3 scripts/score_drivers.py
python3 scripts/build_memo.py
python3 scripts/check_forbidden_terms.py
```

Seed `{windows['seed']}`. Regenerating the corpus is deterministic.
"""
    path = OUT / "leadership_memo.md"
    path.write_text(memo.strip() + "\n", encoding="utf-8")
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
