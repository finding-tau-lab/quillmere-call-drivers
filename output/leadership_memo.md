# Quillmere Service Center — mid-February 1099 timing

**Decision asked:** Do we change the tax-page FAQ and the tax IVR prompt, and is there enough evidence to send that copy through legal and risk?

**Answer:** Yes. Same-season phrase scores show the mid-February week is not “tax documents are up.” It is clients treating **January 31** as *their* deadline, then calling because last year’s language did not name the later brokerage furnish date.

**This packet is synthetic.** Fictional firm. No real accounts, agents, or employer data. Public IRS calendar dates are real; Quillmere volumes and quotes are generated.

## Windows

| Window | Dates | Role | Calls |
|---|---|---|---|
| Baseline (normal) | 2026-01-20 – 2026-01-31 | Same-year language before the standalone furnish date | 40 |
| Spike | 2026-02-10 – 2026-02-21 | Mid-February, still before the consolidated 1099-B date | 127 |

Public furnish dates for TY2025 / season 2026 (weekend and Presidents Day shifts): standalone recipient copies **2026-02-02**; 1099-B / consolidated package **2026-02-17**. Details in `docs/deadlines.md`.

## What keyword volume would have said

A speech query on `1099` / `tax document` / `tax center` fires in both windows. Leadership would have seen “tax-doc contacts are elevated” and stopped there. That is how last year’s page stayed generic: *mailed by the IRS due date; brokerage may arrive later.*

Clients are still asking the same question this year. The previous action was not sufficient.

## What the driver scores say

Fightin’ Words z (spike vs baseline) plus spike-side c-TF-IDF. Method in `docs/method.md`. **Tax-document queue only**, caller channel only. ASR left noisy on purpose. A keyword query already selected these calls; the scores say what changed inside that query.

| phrase | z (spike vs base) | c-TF-IDF | driver | n spike | n base |
| --- | --- | --- | --- | --- | --- |
| january 31 | 3.06 | 306.91 | 0.87 | 73 | 0 |
| pending | 2.43 | 214.38 | 0.67 | 46 | 0 |
| deadline | 2.32 | 199.53 | 0.64 | 42 | 0 |
| file | 2.29 | 195.75 | 0.63 | 41 | 0 |
| when will | 2.29 | 195.75 | 0.63 | 41 | 0 |
| received | 1.99 | 156.61 | 0.54 | 31 | 0 |
| irs | 1.93 | 148.43 | 0.52 | 29 | 0 |
| late | 1.93 | 148.43 | 0.52 | 29 | 0 |
| already passed | 1.82 | 135.90 | 0.48 | 26 | 0 |
| cannot file | 1.82 | 135.90 | 0.48 | 26 | 0 |
| cannot file january 31 | 1.82 | 135.90 | 0.48 | 26 | 0 |
| cpa needs | 1.82 | 135.90 | 0.48 | 26 | 0 |

Read the table as: **the spike week is deadline talk**, not document-lookup talk. `1099` rises because more tax calls exist. The phrases that *only* exist in the spike week are the driver: `january 31` (73 vs 0), `pending`, `deadline`, `when will`, `irs`, `late`. `my cpa` is the pressure sitting on top of that calendar error.

## What the floor actually heard

- `CALL-20260210-0158` / *january 31*: “where is my 1099 the IRS said January 31”
- `CALL-20260210-0159` / *january 31*: “january 31 already passed I thought that was teh deadline”
- `CALL-20260210-0157` / *pending*: “teh tax center says my ten nine nine is still pending”
- `CALL-20260210-0159` / *pending*: “still waiting and the tax center still says pending”
- `CALL-20260210-0160` / *deadline*: “january 31 already passed I thought that was the deadline”
- `CALL-20260210-0159` / *file*: “my CPA needs the ten ninety nine this week I cannot file”

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

Seed `20260210`. Regenerating the corpus is deterministic.
