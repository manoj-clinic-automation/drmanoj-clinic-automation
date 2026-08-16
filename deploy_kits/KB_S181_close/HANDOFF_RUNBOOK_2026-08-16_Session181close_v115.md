# HANDOFF RUNBOOK — v115 (2026-08-16 · Session 181 close — the clinic module LIVE; the deploy chain; the KB swap automated)

*Tier 0. §0 what happened · §1 mental models · §2 live backlog (⭐ top task at head) · §3 install discipline. Companion to KB Register v5.3 (state) + Archive v1.29 (history). S181 was the longest session on record: housekeeping cleared, the UPI gap root-caused, the clinic finance module built, redesigned to the owner's spec and installed live through a NEW one-command deploy chain.*

## §0 — WHAT HAPPENED LAST (S181 — FULL; two green installs on `clinic-finance`, six kits, a new deploy chain)

Phase 0 green **41/41** (the three D316 LOST rows correctly did not halt).

- **Housekeeping debts cleared:** Fault Register **v2.17** (three owed appends applied; §7.1 full text; seven changelog rows reconstructed from evidence, one relabelled v2.9→v2.7 on two independent Archive proofs) · **KB_Asset_Register v1.11.0-R** (the D316 rebuild, provenance-honest, adversarially verified) · the **first FULL cold kit since S171** (42/42 pins; ⚠ flagged PHI-BEARING — six unmasked patient numbers live in the canonical set itself, owner ruling pending).
- **The UPI gap root-caused to ₹0 unexplained:** UPI-typed-as-Cash at Docterz reception (₹17,900, F-91) + missing Procedure-heavy revenue (₹9,200) + unattributed tender (₹3,300). The Docterz export's own footer carries a 7-tender day breakdown nothing was reading; the tracker parser drops Wallet/Debit-Card split legs (`docterz_report.py` delivered to fix, 22/22). Discount capture stopped 18 Jun (F-92); the concession parser mints three fake patients a day into the staff sheet (F-93).
- **The CLINIC module went LIVE** — final **SMOKE 316/316 on the real store**. English four-tender entry (cash/upi/card/razorpay), strays with narration, drawer expenses, grand-total-of-cash, two-stage approval (**Shavez verifies · owner final**; self-verify barred), tracker-day read-only panel for all three levels. Makers seeded real: **shavez, alisha, shivani**. Five installs to get there: three honest reds (installer environment assumptions — F-94), one red that was the system working (the bank arbiter refusing over a real mismatch — F-95), then green C1e (240/240) and green C2a (316/316).
- **The deploy chain (D317) exists and is proven:** owner does one double-click on the PC + pastes one command on the VPS; every gate retained; the C1b red proved the restore path end-to-end. **The repo was found PUBLIC (F-90)** — owner decision owed.
- **The KB swap is automated (D319):** from this close on, the assistant writes canonical docs straight into project knowledge; the owner's EOS work is one double-click + one download.
- **Next free: D320 · F-96 · A-D25 · Session 182.**

## §1 — MENTAL MODELS WORTH CARRYING

1. **A synthetic store proves logic, not life** (F-95). The reds that mattered came from real bank statements, a placeholder username, and an auth-mode-dependent refusal shape — none visible offline. Enrich the offline store with live-shaped data before a first live gate; make every check print what it saw.
2. **An installer's environment assumptions are part of its specification** (F-94). Delivery path, available binaries, message honesty — gate the installer through its ACTUAL invocation path, preflight its tools, and print success only from the code path that succeeded.
3. **A red that is the system working must be recognised as such.** C1c's refusal was D313's bank arbiter doing its job on data the test db could never hold. The fix was to make the smoke exercise that path everywhere — not to weaken the gate.
4. **No ledger-internal check can catch entry-mode misclassification** (F-91). The corrupted field and its derived fields agree by construction. The typed daily tab is the reconciliation anchor — it has been quietly right all along, and it must never be retired into "legacy".
5. **The estate keeps capturing the gross and losing the concession** (F-92 + Marg U7 + the tab's dead Expenses). Discounts/concessions need a first-class home, not a column someone stops filling.
6. **Evidence over theory, twice a day.** The split-leg hypothesis was refuted by an arithmetic ceiling; the id-collision theory by a reproduction that refused to reproduce; the 302 by reading the gate. Every wrong idea died cheaply because it was tested before it was shipped.

## §2 — LIVE BACKLOG

⭐ **S182 top task — finish the clinic go-live surroundings:** (a) **portal tiles** — Daily Collection for shavez/alisha/shivani, Clinic review for owner+bhawna (portal.py kit, D317 chain); (b) **wire `VPS_Push_TrackerDay.gs`** in the clinic Gmail (Script Properties + ~21:30 trigger; fails loudly if CSV headers drift); (c) **first parallel-run checks** — clinic day vs Google Form to the rupee, the verify→approve flow exercised for real, the variance alarm observed.

**Owner actions, in rough order:**
1. **F-90 ruling:** make the repo private + read-only deploy key on the VPS (keeps D317 working), or accept it public knowingly.
2. **Docterz-side behavioural fix (F-91):** reception selects the true payment mode; split payments entered as splits. One sentence to the staff; the variance alarm will show whether it lands.
3. **Gmail auto-forwards:** Razorpay settlement report + ICICI MIS (card) to the clinic Gmail — then the GAS parsers follow the proven pattern.
4. **The cold-kit PHI ruling:** the canonical set itself carries six unmasked patient numbers (Archive v1.27/v1.28, API card). Masking would break every pin and the Archive prefix-proof — needs a deliberate decision, not a quiet edit.
5. Tracker-side (when the folder is reachable / on-computer session): integrate `docterz_report.py`, fix the concession footer bug (F-93), investigate the 18–19 Jun regression cluster (F-92), add clinical-report ingestion as the additional daily input.
6. **See the missing-day alarm fire** for clinic; watch the deposit-threshold shout.
7. Carried: Marg chain (U5·U7·U8·U9·U12) · the August Button A export gate · lab module (parked; its tab silent since 30 Jul; its ₹2,71,380 no-tender block recorded) · WABA go-live (F-82, vendor) · security rotations · console follow-ons · August salary reconciliation · cold-kit cadence (**count: 1 of 3–5** — the S181 kit restarted the clock; this close's KB kit is docs-only, not a full kit).

**Medical unchanged** throughout (proven at every install by the smoke's medical-untouched checks).

## §3 — INSTALL DISCIPLINE (S181 revision)

**The D317 chain is now the standard:** kit → `deploy_kits/` via `push_kit.bat` (one double-click) → `vps_deploy.sh <KIT>` (one paste). Inside every kit, the S177 shape survives whole: SUMS gate → KIT_ID currency (F-88) → stage FROM THE KIT DIR → `.bak` backups (app + db + any UI file being replaced) → swap → **python3-scripted migration with a marker setting** (the sqlite3 CLI does not exist on the box) → **smoke suite as the gate, on a throwaway copy** → restart only on green → **an HONEST red** that states whether live files were touched and restores only what was. Preflight every binary the script uses. A re-issued kit takes a NEW name. Never numbered steps; never pasted heredocs. A filename is not provenance — trust the hash (F-66/D188). Salary/PHI/finance.db never in repo or kit (F-31/F-49) — the tracker-feed endpoint refuses payloads carrying names or phones by design. Prefer additive tables/side tables over ANY rebuild (the C1 attachment rebuild was the once). Smoke checks are self-describing; environment-dependent behaviour is asserted as an invariant. **EOS mechanics per D319:** assistant writes the canonical set into project knowledge + MD5SUMS; owner double-clicks the KB kit push and downloads the cold kit.

**END OF HANDOFF RUNBOOK v115 (Session 181).**
