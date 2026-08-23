# S196 — Portal-health work (renewals line · tile wire · A4 revival) — BUILD STATE

**ALL THREE KITS LIVE. The S193→S195 portal-health plan is COMPLETE end to end.**

## Kit `S196_HLT1` — LIVE (renewals line)

654 → **665/665** on projection. Token wired by the owner on the box (end-to-end proof: `bad_payload` with the real token; token never entered chat). GAS `Renewal_Nag_v2.gs` pasted + Script Property set + first push landed: **the Renewals card is LIVE** — "nothing inside 30 days · pushed 2026-08-23 11:01".

## Kit `S196_HLT2` — LIVE (the crisis lesson's last inch)

665 → **667/667** on projection. `tile-summary` now carries `health_line`; the Sanjeevni portal tile shows the worst problem's one-line headline FIRST (None/unchanged when all is well). Closes **F-161 candidate**: S195 built `_health_headline()` "for the portal tile" and nothing ever consumed it — page red, tile innocent. Found by reading live bytes when the owner asked "is the crisis lesson fully taken care of?" **LIVE PIN: `portal.py` = `ee749cd9f3ac1294aab0d13ce069efc1`.**

## Kit `S196_HLT3` — LIVE, 23-Aug 11:07 (**F-162 candidate closed by code**)

667 → **668/668** on projection, first pass. **LIVE PIN: `finance_app.py` = `388c8ac0fdfecdee6029c0033b9b0ef8`.** The finding: the owner's first real read of the live health page caught "This month vs Marg — could not be read ('datetime.date' object is not callable)" (the F-132 pattern — a human looking beats a green suite). Root cause in the S195 baseline: `_health_state` sets a local `today = dt.date.today()` and the A4 block called `today()` — the local shadowed the module function, so **BOTH A4 cards ("This month vs Marg" + "Marg days never filed") died into their except on every render since S195**; the S195 close had recorded the check as done. Fix: one line, plus a **class-refusing smoke check** — no health card may ever be a swallowed Python exception. Differential offline: +1 exact, fail-set identical. Kit ID `S196_HLT3 fc99c7d15dfa4baede5b5e6adf82971b`.

## The full health surface (S193 → S196, COMPLETE)

Cash-position + Hub card (S193, D333) · applied-status truth F-155 (S193) · Darpan accuracy on tile + save response (S195, verified in live bytes) · `/finance/health` cards: Marg push · days filed · cash position · cash/UPI split · correction checklist · UPI evidence · **month-vs-Marg + never-filed (alive from HLT3)** · flags · backup (S195) · **Renewals** (HLT1) · **worst-problem headline on the Sanjeevni tile itself** (HLT2). Live findings the page is currently flagging for the owner: 21-Aug unfiled · 1 Marg push to apply · 4 small UPI/bank disagreements · 1 cash/UPI split day to fix.

## Provenance (F-97 part 2, all kits)

Repo `finance/`/`portal/` trees stale (S180/S182). Live bytes recovered by hash from kit tarballs: `S195_SIGN/finance_app.py` == `df750243…` · `S195_CLUB2/portal.py` == `ff089807…` · `staff_ledger` == `acd7b538…`. Offline harness: S193_F6 `seed_live_shape.py` + `migrations_concat.sql` + S194 store bits — the finance smoke's first offline runs; every kit differential-proven (+11 / +2 / +1, fail-sets identical); the HLT1 differential caught a request-context fault in my own test code before the box could.

## Close owed (S196, six kits: ATT1 · ATT2 · HLT1 · HLT2 · HLT3 all LIVE + the GAS v2)

Register pins: `staff_register.py` → `9087954c8a4a891e8cdd848d6a9d48b2` (v0.4) · `att_month_report.py` → `9ab98313bbda7ae5555fb4b5a5a82c4b` (v2.6) · `finance_app.py` → `388c8ac0fdfecdee6029c0033b9b0ef8` · `portal.py` → `ee749cd9f3ac1294aab0d13ce069efc1`. `live_pins.txt` regen (A8). Mint candidates: **D334** (present-request policy) · **F-160** (delivery outside the git tree, remedied same hour) · **F-161** (headline built, never wired — closed by HLT2) · **F-162** (A4 dead since S195 via shadowed `today()` — closed by HLT3). Notes: `.gitattributes` gap `*.md`/`*.gs` (F-152 family) · stale repo mirrors of live code (with the auditor) · S195 carry-overs unchanged (token rotation ⭐, ₹20,000 ledger entry, Darpan application scan, 18-Aug review queue). **[All done at the S197 fold.]**
