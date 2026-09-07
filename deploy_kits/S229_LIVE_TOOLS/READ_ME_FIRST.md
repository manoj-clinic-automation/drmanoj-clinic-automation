# S229_LIVE_TOOLS — what manojz is actually running after the S229 close

Two files changed on **manojz** this session. These are the bytes as captured at the close, and they
were verified **against the live source**, not against this kit's own sums — a kit verified against
its own copy proves nothing about what is running (A11).

| file on manojz | why it changed |
|---|---|
| `D:\Downloads\margsync\MargPull\signatures.json` | 13 → **17 signatures**: `SALT_WISE_ITEM_LIST`, `STOCK_VALUATION` ×2, `ITEM_MASTER`. **STRIPS_TAB is listed BEFORE the 4-column DEFAULT on purpose** — `identify()` compares only the first *n* columns, so the shorter signature would swallow the longer file and its unit columns would vanish in silence. Two types carry `"dating": "file_mtime"` because they have no date of their own. |
| `D:\Downloads\margsync\MargPull\marg_rescan.py` | **F-351.** It unpacked three values from `read_preamble()` after S228 gave it four, so it raised `ValueError` on the first quarantined file of every run — 69 consecutive ten-minute cycles, logged as `PROBLEM: rescan=1` and reported nowhere else. |

## Install order and destinations

Both files sit in `D:\Downloads\margsync\MargPull\` on **manojz**. Nothing else moves. The
ten-minute scheduled task `Marg pull from medical` picks up a changed `signatures.json` by itself
(`marg_rescan.py --if-signatures-changed --apply`) — no restart, no manual run.

## Credentials needed

**None for these two files.** The pull chain as a whole uses the medical-PC share and the clinic
server token; **their values are never recorded here.**

## The five scheduled tasks on manojz, for the record

`Clinic stock nightly` · `Marg pull from medical` · `MargExpectedOnCapture` · `MargPullWatchdog` ·
`MargSnapshotOnCapture` — all running as the owner's account.

## Verify

From INSIDE this folder:

```
md5sum -c SUMS.md5
```
