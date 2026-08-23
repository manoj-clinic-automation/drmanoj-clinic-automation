# HANDOFF RUNBOOK — v129 (Session 193 close · 20 Aug 2026)

**Tier 0. §0 what happened · §1 mental models · §2 the live backlog · §3 install discipline · §4 the EOS automation boundary.**

---

## §0 — WHAT HAPPENED (Session 193)

**A long build session, entirely on the Sanjeevni (medical) finance surface. F6 and F-155 landed, the discount column shipped forward + backfilled, the cash-position view was built and hardened over four passes, Darpan's 18-Aug day was rescued (not deleted), and the Daily Sale v2 redesign was prototyped and approved.**

**1. F6 (F-148) + F-153 — LIVE (`S193_F6`).** The drawer→ledger bridge: approving a Sanjeevni day that carries a salary advance now posts an `ADVANCE_ISSUE` to the Staff Ledger, through the ledger's own writer, fail-loud + idempotent + ordered. Built via the F-87 seeded-store differential (the task the S192 close set as first). Ledger selftest 287→289, finance smoke 550→555. F-153 (contra `against_month`) bundled in. **F-148 CLOSED.**

**2. F-155 — LIVE (`S193_F155`).** A Marg push showed "✓ applied" while the day carried no linked bills (17-Aug read applied with empty books). Now a run is "applied" ONLY when every day it carries actually ingested; otherwise it stays `pending` with its payload kept for replay. Smoke 555→557.

**3. The discount column (Hub Fix 5) — LIVE + BACKFILLED (`S193_DISC`).** Per-bill Gross · Disc · Net in the Marg bill drill, for new pushes AND all history. Store gross (Marg rounds the net, so gross ≠ net+disc for 1,312 bills). Adapter reads gross/disc directly from the CSV row. Historical backfill two-pass. 3,141 bills filled across 124 days, recovered 16–19 Aug from the medical-PC `SENT\` folder over the bridge. Smoke held 557.

**4. Stale not-filed flag self-heal — LIVE (`S193_STALE`).** The `MARG_DAY_NOT_FILED` data_flag was written at push time and never cleared. The Hub note now hides any such flag for a day that has a Marg batch (display-only, self-healing, no row deleted).

**5. The Cash-position view — LIVE, four passes (`S193_CASHPOS` → `_2` → `_3` → `_4`).** New `/finance/api/cash-position`: drawer = `v_cash_ledger` closing − parked; reserve (Dr Bhawna) and Dr Manoj from `cash_custody_event`; bank deposits from `cash_movement`. Reconciles: drawer + reserve + manoj = unbanked. Today: drawer ₹65,697 · reserve ₹1,56,235 · manoj ₹18,963 · unbanked ₹2,40,895 · banked ₹15,70,600. New Hub card, drawer day-wise since the last clearing, fetch cache-busted. Also fixed the custody box (never rendered since it shipped — F-157).

**6. Darpan's 18-Aug day — RESCUED, not deleted.** The DB had ONE entry (id 124) holding the day's 22 Marg bills; deleting the "spare draft" would have cascaded ₹25,176 away. Guided the owner to fill (23,879 / 6,707 / 17,172) + reason-for-scans → File → Approve. Now approved.

**7. Daily Sale v2 — PROTOTYPED + APPROVED.** Clickable prototype OK'd; the live `POST /finance/api/day` contract mapped. To be built next at a new URL, current page kept as fallback.

**8. Findings.** F-155 used. **F-156 · F-157 · F-158 · F-159 minted.** **D333 minted** (the cash-position model).

---

## §1 — MENTAL MODELS (added this session)

- **The browser is part of the system.** A correct server fix looked broken for two rounds because Chrome served a cached API GET. Any JSON the UI must show fresh gets a cache-busted fetch (`?_=<ts>` + `no-store`). (F-159)
- **Read the payload's type before comparing it.** Comma-formatted string balances made `x>0` become `NaN>0`; every hand vanished from the day it shipped. (F-157)
- **A derived figure is only meaningful over its valid window.** Subtracting today's reserve from every historical closing produced false negatives to mid-July. (F-158)
- **Don't delete what holds live data.** A "spare draft" was the day's only entry and carried its Marg bills — the fix was to *finish* it.
- **Recover from what the system already kept.** 16–19 Aug discounts came from the medical-PC `SENT\` folder's dated copies.
- **When the repo is behind the box, import by hash and patch in place.** finance_ingest was changed by a fail-loud in-place patch built against the two exact live regions, verified by reconstructing live and hashing.

---

## §2 — THE LIVE BACKLOG

**⭐1 Daily Sale v2 page** (APPROVED prototype) — build at a NEW route; leave `/finance/entry` as fallback. Contract + design in `S193_Daily_Page_v2_and_Backlog.md`.
**⭐2 Home-medicine bills** from the Marg export (scan optional). NEED: how a home-medicine bill is marked in Marg.
**⭐3 Cash/UPI reclassification tracker** (`mode_change_log` in `ingest_day`).
**⭐4 Record hand-overs to Bhawna/Manoj as `cash_movement`s** — owner "will start soon"; then reserve/Manoj track live.
**⭐5 Full-auto ping-pong email query agent** — NEED: owner Gmail app password; read-only + trusted-sender.
**Carried:** ⭐0 Darpan's signed-application scan vs advance `0cc0b26b38c5` (clock — before the August close); July salary close; the August month-end first run.

---

## §3 — INSTALL DISCIPLINE (reinforced this session)

- **Currency-gate on the TEMPLATE bytes, not a rendered snapshot** (`S193_CASHPOS` patch-3 RED'd on a JS-added `collapsed` class).
- **Cache-bust any UI fetch whose freshness matters.**
- **Trash goes to the REPO ROOT `_to_delete/`** (gitignored), never `deploy_kits/_to_delete/`.
- device_bash cannot `rm`/overwrite mounted files: `mv` old kit dirs aside, extract fresh; or `device_commit_files force:true`.

---

## §4 — THE EOS AUTOMATION BOUNDARY (held, with one honest caveat)

The assistant executes the close. **This close's caveat:** the monolithic KB Register, History Archive, and CANONICAL_MANIFEST are append/prepend canon too large to fully rewrite in-session; the S193 state (narrative, D333, F-156…F-159, all final pins) is captured completely in `S193_Close_Summary_and_Pins.md` + this Runbook + START_HERE_194, and the mechanical prepend/append + md5 refresh + `live_pins` regen (A1/A2/A7/A8) is the one fold owed — flagged, not skipped. **Owner residual: `PUBLISH_ALL.bat` + on-box pin-list copy.**

*(This caveat's debt grew to four sessions and was cleared at the S197 fold-in.)*

---

*HANDOFF_RUNBOOK v129 · Session 193 close · supersedes v128. If §0, §2 or this end-marker is absent, this file is truncated and must not be used as canonical.*
