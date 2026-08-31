# S213_RETURNS_CARD — the returns line, sourced from the sump (⭐1.2)

**Built and proven offline at Session 213, 31-Aug-2026. NOT YET INSTALLED.**
*(That line is a claim, not evidence — the live pins and the service are the
evidence, after the owner's install below.)*

## What this is

The next build after F-261, in the owner's decided S213 order: **the returns
line on his page** — the live card's approval workflow kept, its data source
swapped to the S212 sump, its two S212-found defects fixed, and the API
pass-through that `patch_finance_app_panel.py` dropped at the `jsonify`.

| piece | what changes |
|---|---|
| `patch_darpan_returns.py` | `cn-detail` rebuilt on `finance_returns_audit` (the UNION of both spines — the old card saw 63 of 179 returns). Three populations named. Gross AND net, so a discount on a refund is a verdict. **The GET no longer writes** (old `:944-947` did `INSERT … commit()` in a read); the approval row is created by the POST that decides. Raw `item_name` matching is gone — the sump audits on `item_key`. The 30-Aug owner ruling survives verbatim and now also covers orphans and no-item-detail returns. |
| `patch_finance_app_panel_r2.py` | the S211 day-gaps endpoint, r2: `returns=` and `payment=` are no longer dropped at the `jsonify` — `day_report()` computed both all along. r1 was never installed; r2 supersedes it whole (`S211_PANEL` remains for provenance). |
| `finance_approvals.html` | full-file replacement, chain `2521685e…` (live, S210) → `73b5f7bc…` (S211_PANEL, gaps card) → **this file**: ONE collapsed SALE RETURNS card in the §8 shape — populations, gross→net, verdicts, the bill as Marg exported it, the earlier-purchase audit, approve/reject — plus the day-gaps card gains the returns and declared-vs-bank lines. No links, no duplication, all data on the page. |
| `WALK_returns_card.py` | the live-shape walk, **35 checks**: rebuilds the LIVE `darpan_app.py` bytes from sibling kits (S208_CONSOLE + S209_LEDGERMSG + S210_HANDOVER, proving the pin `b694bfdd…`), patches them, builds a real database from the real schemas, and drives the real routes through a Flask test client — every population, every refusal, the GET-writes-nothing proof, the create-on-POST flow, and the r2 JSON keys. All paths RELATIVE to this folder (the S212 sandbox-mount lesson). |

## Dependencies this install carries to the VPS (all already built and gated)

`S212_SUMP`: `finance_money.py` + `finance_returns_audit.py` (the engine).
`S211_MATCH`: `finance_daily_gaps.py` + `finance_patient_match.py` (the day-gaps
report the r2 endpoint serves). None of the four is live yet; this kit's
install puts all four in `/root/finance/` alongside the two patches and the page.

## Safety

- `patch_darpan_returns.py` refuses any target that is not byte-identical to
  the S212-close live pin (`b694bfdd…`) and not already patched. Backup +
  `py_compile` + automatic restore, house pattern.
- `patch_finance_app_panel_r2.py` is anchor-gated on the apply route, refuses
  if the r1 endpoint is somehow present, backup + compile + restore.
- Ladder rung 4 (`finance_returns_audit.py:108-111`, rates-vs-money) is **NOT
  touched here** — it is ⭐1.3, its own re-measurement, per the decided order.
- Rollbacks: every patch prints its timestamped backup path; the html's
  predecessor is the live `2521685e…` bytes (in `S210_APPLYFEEDBACK/`).

## Gate

From INSIDE this folder: `md5sum -c SUMS.md5` · then `python -B WALK_returns_card.py`.
