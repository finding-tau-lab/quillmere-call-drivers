# data/ — SYNTHETIC

Every file in this folder is generated. Fictional firm: Quillmere Advisory / Quillmere Service Center.

| File | Role |
|---|---|
| `windows.json` | Baseline vs spike date bounds and public IRS furnish dates |
| `call_metadata.csv` | One row per call (window, queue, theme, paths) |
| `transcripts/*.txt` | Timestamped dialogue, intentionally imperfect ASR |

Themes labeled `tax_timing` and `tax_find` exist so you can sanity-check the scorer. The scorer itself does **not** read the theme column. It only sees caller text.

Do not treat IDs, names, or phrases as real clients or employees.
