# START HERE — Session 184

Hi Claude. Continuing my clinic-automation project (**Session 184**).
I'm Dr. Manoj Agarwal, orthopaedic surgeon, Advanced Orthopaedic Surgery Centre, Bareilly.
Solo practice, older Hindi-first semi-urban patients.

*(Session-specific entry point regenerated at the S183 close. The evergreen procedure is
`START_HERE_PROMPT_v5` = this project's custom instructions; follow it. This file carries only the
Phase-0 pointers current as of S183 and the S184 top task.)*

**Working protocol:** plain language · ONE step at a time, wait for explicit confirmation · full-file
replacements · ALL-CAPS = urgent · mask patient numbers to last-4, never print secrets · nothing live
rebuilt without explicit OK, manual workflow stays the fallback · build/test offline, **rehearse the
installer against a throwaway target**, then install via the **D317 kit chain** · the asset and finance
apps use system `/usr/bin/python3` (F-53); `/root/wa` scripts and the portal's gunicorn use
`/root/wa/venv/bin/python3`.

---

## Phase 0 — do this FIRST (verification before work)

**Documents** — one command does the whole check against git bytes:

```
cd /tmp && rm -rf kbv && git clone --depth 1 -q \
  https://github.com/manoj-clinic-automation/drmanoj-clinic-automation.git kbv \
  && cd kbv/deploy_kits/KB_canon_all && md5sum -c MD5SUMS_ALL.txt
```

**Live code (NEW at S183 — the F-97 fix) — run this too, every session:**

```
python3 /root/deploy/verify_live_pins.py
```

1. Open **`CANONICAL_MANIFEST.md`**. STATUS should read **current at S183**.
2. Verify every doc row by md5 (a hash verdict is pronounced only on bytes delivered as a FILE — F-88).
   The three **D316 CLOSED-AS-LOST rows do NOT halt**.
3. Run the **pin verifier**. It should be GREEN (39/39) — the Register's live pins were corrected to
   the box at S183. A DRIFT means the box changed since; correct the Register FROM the box, never the
   reverse (D321). Note `verify_live_pins` still can't see the 5 blind rows (Apps Script, migrations,
   PC-side) — they print every run, never counted as passes.
4. Read into context only **Tier 0**: the manifest, this file, **KB Register v5.5**,
   **HANDOFF_RUNBOOK v117**, any open incident (none open). Tier 1 on demand — for S184 that means
   `S183_Sanjeevni_Cash_Reconciliation_YesBank` and `S183_Sanjeevni_Daily_Cash_Design_and_Marg_Findings`.
5. Confirm, then ask which backlog item to start (Runbook §2).

## Where the truth lives
- **`CANONICAL_MANIFEST.md`** — doc set, tiers, hashes. WINS on "what is canonical/current." (S183)
- **KB Register v5.5** — live-file table (Marg feed live, 9 pins corrected, `/root/deploy/` tool added),
  decisions through **D321**, findings through **F-104**.
- **KB History Archive v1.31** — §S183 is the last section (pure append).
- **HANDOFF_RUNBOOK v117** — §0 what happened · §1 mental models · §2 backlog · §3 install discipline.
- **Fault_Action_Register v2.19** — CURRENT (F-100…F-104 in §7.1).

## ⭐ S184 TOP TASK — book the Sanjeevni cash correction (gated, no ad-hoc SQL)
The cash chain is reconciled and **whole** (no money missing — the −₹30,056 was 16 unrecorded Yes Bank
deposits). Now BOOK it, via a tested offline-rehearsed gated migration:
**(a)** record the 16 verified Yes Bank cash deposits (₹16,45,600, 9 Apr → 13 Aug);
**(b)** record the ₹40k salary advances drawn from the drawer (₹15k 9 Apr · ₹15k 30 May · ₹10k 18 Jun);
**(c)** set the opening anchor (~₹31k on 1 Apr, or Count-the-drawer to a confirmed count ≈ ₹75k);
**(d)** build the **Yes Bank cash-deposit reconciliation** (F-103) parallel to `finance_upi` + a named
"Yes Bank deposit" movement type.
Sole reference: **`S183_Sanjeevni_Cash_Reconciliation_YesBank`**.

**Then:** reclassify legacy no-ID Marg bills to WALK-IN (F-104, clears 118 exceptions + 2,062 review
items) · **check whether Darpan's salary advances are in the Google Sheet + his scanned copy** (owner
parked; the advance ledger is being folded into the recently-built salary system; **July payable to
Darpan = ₹10,000**) · Darpan's daily catch-up (file 14 Aug cash≈11,413/UPI 6,530, 15 Aug cash≈3,926/UPI
4,925, mark 16 Aug closed) · build the daily Marg live flow B4–B9 (design doc).

**Owner decisions still open:** the daily-flow home-medicine auto-deduction shape · Razorpay/ICICI MIS
auto-forwards (not needed for medical — cash+UPI only) · lab module (parked).

**Connected sources:** Google Drive · Gmail · Notion · GitHub (`drmanoj-clinic-automation`, PUBLIC by
D320 — no PHI artefact enters it) · ClickUp parked (D17). Patient data is NOT in this project. The
Sanjeevni scans live in a DIFFERENT Drive account than the connected one (not readable from here).

**Cold-kit count: 3 of 3–5** (F-89). Next free: **D322 · F-105 · A-D25 · Session 184.**

*START_HERE_SESSION_184 — regenerated at the S183 close. Supersedes START_HERE_SESSION_183.*
