#!/usr/bin/env python3
"""Generate the Quillmere two-window synthetic tax-timing corpus.

SEED=20260210. Deterministic. SYNTHETIC DATA ONLY.
"""
from __future__ import annotations

import csv
import json
import random
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

SEED = 20260210
TZ = timezone(timedelta(hours=-5))  # EST
OPEN_MIN = 8 * 60
CLOSE_MIN = 20 * 60

BASELINE_START = date(2026, 1, 20)
BASELINE_END = date(2026, 1, 31)
SPIKE_START = date(2026, 2, 10)
SPIKE_END = date(2026, 2, 21)

# Calls per weekday; weekends thinner.
BASELINE_WEEKDAY = 16
SPIKE_WEEKDAY = 24
WEEKEND = 4

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
TRANS_DIR = DATA / "transcripts"

SITES = ["Los Angeles", "Miami", "Atlanta"]
QUEUES = ["TAX_DOCS", "SERVICE", "ADVISOR_SUPPORT", "DIGITAL"]
DISPOSITIONS = ["resolved", "callback", "transfer", "unresolved"]
AGENT_FIRST = [
    "Jordan", "Riley", "Casey", "Avery", "Morgan",
    "Quinn", "Sage", "Cameron", "Hayden", "Reese",
]


def daterange(start: date, end: date):
    d = start
    while d <= end:
        yield d
        d += timedelta(days=1)


def n_for_day(d: date, window: str) -> int:
    if d.weekday() >= 5:
        return WEEKEND
    return SPIKE_WEEKDAY if window == "spike" else BASELINE_WEEKDAY


def pick_theme(rng: random.Random, window: str) -> str:
    if window == "spike":
        roll = rng.random()
        if roll < 0.52:
            return "tax_timing"
        if roll < 0.60:
            return "tax_find"
        if roll < 0.70:
            return "advisor"
        if roll < 0.78:
            return "digital"
        if roll < 0.86:
            return "transfer"
        if roll < 0.92:
            return "fee"
        return "profile"
    roll = rng.random()
    if roll < 0.18:
        return "tax_timing"
    if roll < 0.28:
        return "tax_find"
    if roll < 0.44:
        return "advisor"
    if roll < 0.56:
        return "digital"
    if roll < 0.70:
        return "transfer"
    if roll < 0.82:
        return "fee"
    if roll < 0.92:
        return "profile"
    return "other"


def tax_form_token(rng: random.Random) -> str:
    return rng.choice(
        ["1099", "1099", "1099", "ten ninety nine", "ten nine nine", "tax form"]
    )


def asr_mess(rng: random.Random, text: str) -> str:
    if rng.random() < 0.14:
        text = text.replace("the ", "teh ", 1)
    if rng.random() < 0.08:
        text = text.replace("ing ", "in ", 1)
    if rng.random() < 0.07:
        text = text.replace(" to ", " t ", 1)
    return text


def fmt_mmss(sec: int) -> str:
    return f"{sec // 60:02d}:{sec % 60:02d}"


def pick_times(rng: random.Random, day: date) -> tuple[datetime, datetime, int]:
    minute = OPEN_MIN + rng.random() * (CLOSE_MIN - OPEN_MIN)
    start = datetime(day.year, day.month, day.day, tzinfo=TZ) + timedelta(
        minutes=minute, seconds=rng.randint(0, 59)
    )
    duration = int(rng.choice([90, 120, 150, 180, 210, 240, 300, 360, 420]))
    duration += rng.randint(-15, 30)
    duration = max(80, min(duration, 600))
    return start, start + timedelta(seconds=duration), duration


def caller_tax_timing(rng: random.Random, window: str) -> list[str]:
    form = tax_form_token(rng)
    if window == "baseline":
        return rng.choice(
            [
                [
                    f"just checking if my {form} is posted yet",
                    "usually they show up in the tax center sometime in January right",
                    "no rush I am early I know",
                ],
                [
                    f"when do the {form}s usually go out",
                    "I like to give my CPA a heads up",
                    "if it is not there yet I can wait",
                ],
                [
                    f"I saw a note about tax documents and wanted to know the timing for my {form}",
                    "the page said it depends on the account type",
                    "okay so I should look again in a couple weeks",
                ],
                [
                    f"is the {form} going to be paper or in the tax center",
                    "I have e-delivery on I think",
                    "fine I will watch the tax center",
                ],
            ]
        )
    return rng.choice(
        [
            [
                f"where is my {form} the IRS said January 31",
                "my neighbor already received theirs last week",
                "you told people it would be here and it is mid February",
            ],
            [
                f"my CPA needs the {form} this week I cannot file",
                "january 31 already passed I thought that was the deadline",
                "still waiting and the tax center still says pending",
            ],
            [
                f"I still have not received my {form}",
                "IRS deadline was January 31 why is this late",
                "I need to file my taxes and I am stuck",
            ],
            [
                f"the tax center says my {form} is still pending",
                "supposed to have it by now everyone else does",
                "when will I get the 1099 exactly not the usual language",
            ],
            [
                f"you are late on my {form}",
                "my CPA called me this morning asking where it is",
                "last year the page said allow extra time that did not help",
            ],
            [
                f"when will I get my {form} I sold stock last year",
                "I think this is the brokerage package not the bank interest one",
                "nobody told me those arrive later than January 31",
            ],
        ]
    )


def agent_tax_timing(rng: random.Random, window: str) -> list[str]:
    # Last year's script, on purpose. Same in both windows.
    lines = rng.choice(
        [
            [
                "Tax documents are mailed by the IRS due date. Allow several days for delivery.",
                "Brokerage packages may arrive later. Please check the tax page FAQ.",
            ],
            [
                "I am looking at the tax center status on our side.",
                "The FAQ says forms go out by the IRS date and brokerage can take longer.",
            ],
            [
                "If it is not in the tax center yet it may still be in mailing.",
                "The tax page says allow extra time after January 31.",
            ],
        ]
    )
    if window == "spike":
        lines.append(
            rng.choice(
                [
                    "I know that is the same answer as last year. I can note the complaint.",
                    "I do not have a different date than what is on the tax page.",
                    "I can read the FAQ again but it does not name a February date.",
                ]
            )
        )
    return lines


def caller_tax_find(rng: random.Random) -> list[str]:
    form = tax_form_token(rng)
    return rng.choice(
        [
            [
                f"I need help finding last year's {form} in the tax center",
                "I can sign in I just cannot see the document list",
            ],
            [
                f"can you email me a copy of the {form}",
                "I have e-delivery but I want a pdf today",
            ],
            [
                "how do I turn on e-delivery for tax documents",
                "I do not want paper going to the old address",
            ],
        ]
    )


def other_lines(theme: str, rng: random.Random) -> tuple[list[str], list[str]]:
    table = {
        "advisor": (
            [
                "can you get a message to my advisor I need a callback",
                "desk please I was told to call the service line first",
            ],
            [
                "I can request an advisor callback. What is the best number?",
                "the mobile on the profile is fine",
            ],
        ),
        "digital": (
            [
                "I can't log in to the app it just spins",
                "portal says try again later",
            ],
            [
                "Are you on the mobile app or the website?",
                "I am not seeing a completed password reset on our side.",
            ],
        ),
        "transfer": (
            [
                "I want to transfer funds I started it in the app and it stalled",
                "checking on an ACH I submitted yesterday",
            ],
            [
                "I see a transfer request in a pending state.",
                "I cannot release it from this line.",
            ],
        ),
        "fee": (
            [
                "why was I charged an advisory fee this week",
                "question on billing the line item looks off",
            ],
            [
                "Fee lines post on a cycle. I can note the question for review.",
                "Alright I will flag it.",
            ],
        ),
        "profile": (
            [
                "I need to update my address we moved last month",
                "change my email on file the old one is shut down",
            ],
            [
                "I can take the new address. I will repeat it back.",
                "Please do I do not want a statement going to the old place.",
            ],
        ),
        "other": (
            [
                "calling about a confirmation I thought I would get",
                "just wanted to confirm you have my mobile number",
            ],
            [
                "I have the profile open. What should I confirm?",
                "Just that you can reach me if something posts.",
            ],
        ),
    }
    return table[theme]


def build_transcript(
    rng: random.Random, theme: str, window: str, agent: str, duration: int
) -> str:
    lines = []
    t = 0
    lines.append(f"[{fmt_mmss(t)}] IVR: Thank you for calling Quillmere Service Center.")
    t += rng.randint(16, 40)
    if theme.startswith("tax") and rng.random() < 0.45:
        lines.append(
            f"[{fmt_mmss(t)}] IVR: For tax documents please visit the tax page. "
            "Forms are mailed by the IRS due date."
        )
        t += rng.randint(8, 16)
        lines.append(
            f"[{fmt_mmss(t)}] CALLER: um that menu did not answer when I get the form "
            "can I speak to a person"
        )
        t += rng.randint(6, 12)
    lines.append(
        f"[{fmt_mmss(t)}] AGENT: Quillmere Service Center, this is {agent}. How can I help?"
    )
    t += rng.randint(4, 9)

    if theme == "tax_timing":
        caller = caller_tax_timing(rng, window)
        agent_l = agent_tax_timing(rng, window)
    elif theme == "tax_find":
        caller = caller_tax_find(rng)
        agent_l = [
            "Tax documents that have published should appear under Tax Center.",
            "I can walk you to Statements and Documents then Tax Documents.",
        ]
    else:
        caller, agent_l = other_lines(theme, rng)

    for i, text in enumerate(caller):
        text = asr_mess(rng, text)
        lines.append(f"[{fmt_mmss(t)}] CALLER: {text}")
        t += rng.randint(5, 14)
        if i < len(agent_l):
            a = asr_mess(rng, agent_l[i])
            lines.append(f"[{fmt_mmss(t)}] AGENT: {a}")
            t += rng.randint(5, 13)
        if t > duration - 20:
            break
    for i in range(len(caller), len(agent_l)):
        if t > duration - 20:
            break
        a = asr_mess(rng, agent_l[i])
        lines.append(f"[{fmt_mmss(t)}] AGENT: {a}")
        t += rng.randint(5, 12)

    closer = rng.choice(
        [
            "CALLER: that's all thanks",
            "CALLER: okay um thanks",
            "CALLER: that does not really help but thanks",
        ]
        if theme == "tax_timing" and window == "spike"
        else ["CALLER: that's all thanks", "CALLER: okay um thanks"]
    )
    lines.append(f"[{fmt_mmss(t)}] {closer}")
    t += rng.randint(3, 8)
    lines.append(
        f"[{fmt_mmss(t)}] AGENT: Thank you for calling Quillmere Service Center."
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    rng = random.Random(SEED)
    TRANS_DIR.mkdir(parents=True, exist_ok=True)
    for old in TRANS_DIR.glob("CALL-*.txt"):
        old.unlink()

    meta_rows = []
    seq = 0
    for window, start, end in (
        ("baseline", BASELINE_START, BASELINE_END),
        ("spike", SPIKE_START, SPIKE_END),
    ):
        for day in daterange(start, end):
            for _ in range(n_for_day(day, window)):
                seq += 1
                theme = pick_theme(rng, window)
                agent = rng.choice(AGENT_FIRST)
                start_ts, end_ts, duration = pick_times(rng, day)
                cid = f"CALL-{day.strftime('%Y%m%d')}-{seq:04d}"
                queue = (
                    "TAX_DOCS"
                    if theme.startswith("tax")
                    else rng.choice(["SERVICE", "ADVISOR_SUPPORT", "DIGITAL"])
                )
                text = build_transcript(rng, theme, window, agent, duration)
                (TRANS_DIR / f"{cid}.txt").write_text(text, encoding="utf-8")
                meta_rows.append(
                    {
                        "call_id": cid,
                        "window": window,
                        "call_date": day.isoformat(),
                        "start_ts": start_ts.isoformat(),
                        "end_ts": end_ts.isoformat(),
                        "duration_sec": duration,
                        "site": rng.choice(SITES),
                        "queue": queue,
                        "theme": theme,
                        "agent_name": agent,
                        "agent_id": f"AGT-2{rng.randint(100, 199)}",
                        "acct_token": f"ACCT-8{rng.randint(1000000, 9999999)}",
                        "disposition": rng.choice(DISPOSITIONS),
                        "transcript_path": f"data/transcripts/{cid}.txt",
                    }
                )

    meta_path = DATA / "call_metadata.csv"
    with meta_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(meta_rows[0].keys()))
        w.writeheader()
        w.writerows(meta_rows)

    windows = {
        "seed": SEED,
        "firm": "Quillmere Service Center",
        "season": "TY2025 / filing season 2026",
        "baseline": {
            "start": BASELINE_START.isoformat(),
            "end": BASELINE_END.isoformat(),
            "role": "same-year normal week(s) before the standalone furnish date",
        },
        "spike": {
            "start": SPIKE_START.isoformat(),
            "end": SPIKE_END.isoformat(),
            "role": "mid-February timing-confusion window before consolidated furnish date",
        },
        "public_dates": {
            "standalone_recipient": "2026-02-02",
            "consolidated_1099b_recipient": "2026-02-17",
            "note": "Weekend and Presidents Day shifts. Not a Quillmere mail calendar.",
        },
        "n_calls": len(meta_rows),
    }
    (DATA / "windows.json").write_text(json.dumps(windows, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(meta_rows)} calls -> {meta_path}")
    print(f"transcripts -> {TRANS_DIR}")


if __name__ == "__main__":
    main()
