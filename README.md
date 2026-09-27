# quillmere-call-drivers

SYNTHETIC DATA. Fictional firm. No affiliation with any financial institution or speech-analytics vendor.

Call-driver text mining for a **mid-February 1099 timing** problem in a fictional wealth contact center (Quillmere Service Center).

Speech-query volume can tell leadership that tax-document contacts rose. It cannot tell them *why*, and it cannot tell them whether last year’s FAQ sentence worked. This repo takes the **tax-document queue** and scores **client phrases** in a spike week against a same-year normal week (Monroe Fightin’ Words + c-TF-IDF), then emits a short leadership memo.

It does **not** use real customer audio, real tax documents, or employer code. It does **not** publish an outcome percentage.

## The story (fixed)

Clients collapse two clocks into one. They hear “1099s are due January 31.”

For tax year 2025 / filing season 2026 the public calendar is:

- Standalone recipient copies (1099-INT, 1099-DIV, and similar): **Monday, February 2, 2026** (January 31 is a Saturday).
- 1099-B and any **consolidated brokerage package** that includes it: **Tuesday, February 17, 2026** (February 15 is a Sunday; February 16 is Presidents’ Day).

Mid-February is therefore not automatically “we mailed late.” It is the week a brokerage household is still waiting, while the folklore deadline has already passed.

Quillmere already tried to say this. The tax page and the IVR used cautious language: *mailed by the IRS due date; brokerage may arrive later.* Clients called anyway, with the same question as last year. That is the point of a same-season week-vs-week contrast. Previous communication was not sufficient. The scores are the packet you take to legal and risk to change the page and the IVR.

## Windows

- **Baseline (normal):** 2026-01-20 to 2026-01-31
- **Spike:** 2026-02-10 to 2026-02-21

Production pattern this reconstructs: a normal-week corpus and the following spike-week corpus, same year. The demo stretches the gap so the two furnish dates sit on the calendar in plain sight.

## How to run

```bash
python3 scripts/generate_synthetic_data.py
python3 scripts/score_drivers.py
python3 scripts/build_memo.py
python3 scripts/check_forbidden_terms.py
```

Then read:

- `output/driver_scores.csv` — ranked phrases
- `output/leadership_memo.md` — the decision packet

Seed is `20260210`. Regenerating the corpus is deterministic.

## What to look at first

1. `docs/deadlines.md` — why mid-February confuses a wealth client.
2. `docs/method.md` — Fightin’ Words z and c-TF-IDF, then the combined driver score.
3. `output/leadership_memo.md` — FAQ copy + IVR, in that order, because a web edit is not a same-day change.

## What this is not

- Not a real broker, bank, or contact center
- Not a production speech-query library or a vendor export
- Not an Average Treatment Effect on the FAQ/IVR change
- Not a claim about a percentage drop in tax-document calls

If the copy ships, measure the next mid-February window the same way. That measurement does not belong in this repository.

## License

MIT
