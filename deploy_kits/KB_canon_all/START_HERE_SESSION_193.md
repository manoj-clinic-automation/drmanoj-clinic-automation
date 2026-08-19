# START HERE — SESSION 193
### Generated at the Session 192 close · 19 Aug 2026

Hi Claude. This is **Session 193** of Dr. Manoj Agarwal's clinic-automation project.
The evergreen procedure is the project's custom instructions (`START_HERE_PROMPT_v5`). This file
carries only what is specific to opening THIS session.

---

## PHASE 0 — verification before work (D247). Do this FIRST.

**1. Documents.** Clone the repo anonymously and verify the canonical set by md5:

```
rm -rf /tmp/kbv && git clone --depth 1 https://github.com/manoj-clinic-automation/drmanoj-clinic-automation /tmp/kbv
cd /tmp/kbv/deploy_kits/KB_canon_all && md5sum -c MD5SUMS_ALL.txt
```

**`md5sum -c` must exit 0 with no WARNING line** — a WARNING is a FAIL, not a note (**F-119**).

**2. The F-88 cross-check.** A passing `md5sum -c` proves a kit internally consistent, never current.
Cross-check every md5 token in `CANONICAL_MANIFEST.md` against real file hashes; tokens that match no
file must each be legitimately non-document (live VPS code pins · Tier-2 digests · the three D316
closed-as-lost rows · kit IDs · superseded versions named only in narrative).

**3. The F-107 inverse check.** Every Tier-0 doc actually in use must HAVE a manifest row. Phase 0 asks
*"do these bytes still match?"* — it does not ask *"are you listed?"* unless you make it.

**4. F-123.** Exactly ONE file named `CANONICAL_MANIFEST.md` in the repo.

**5. A8 / F-134.** Confirm the pin list's `source_md5` equals the manifest's CURRENT Register pin by
**hashing the Register file directly** — not by reading the claim.

**6. Live code (D321).** On the box:

```
cd /root/deploy/repo && git pull && cp deploy_kits/KB_canon_all/live_pins_S192close.txt /root/deploy/live_pins.txt && python3 /root/deploy/verify_live_pins.py
```

**Expect GREEN, match 43, drift 0, `source: VERIFIED`.** The S192 close moved
`/root/staff_ledger.py` three times and regenerated the list from Register **v5.40**, so a RED on that
file means the copy step above did not happen.

---

## WHAT IS TRUE NOW

- **Live ledger pin:** `/root/staff_ledger.py` = **`44e39d6abf34db5e11acc2223ac908d3`** (kit `S192_SL7`, selftest **287**).
- **D332 is three-quarters built and live:** `S192_SL5` (waiver instrument · policy-date settings · F-151 wording) · `S192_SL6` (schedule lane · DEFER · capacity rule) · `S192_SL7` (per-staff Perks view). **`S192_F6` is designed and deliberately unbuilt.**
- **Attendance enforcement is OFF by design.** `attendance_enforce_from` is unset, so **every month is preview-only**: attendance deductions are shown struck-through and do not reduce anyone's pay. Turning it on is a policy act at `/ledger/settings`, taken when the notice is served.
- **Darpan's money after the S192 corrections:** open advances are the two loan tranches only (₹1,79,000 interest-bearing + ₹1,80,000 interest-free); ceiling **50% = ₹10,000**; the consolidated **₹20,000 SPECIAL** (`0cc0b26b38c5`) is **PENDING** on its signed application, scheduled **₹8,000 Aug + ₹4,000 × 3**.
- **Project knowledge is at ~57% of its ceiling** after the S192 cleanup (was 96%).

---

## SESSION 193 TASKS

**⭐0 — check first, it may already be done and it has a clock.** Has the owner scanned Darpan's signed
application against `0cc0b26b38c5` and approved it? If not, and the August close is near, say so
plainly: unapproved means **no ₹8,000 collected in August** (the schedule shifts; nothing breaks).

**⭐1 — `S192_F6`, the drawer→ledger bridge (F-148).** The **first task is the seeded store**, not the
feature: `finance_app.py`'s 550-check smoke copies the live `finance.db` and cannot run offline, so
building against it blind is **F-87**, a fault this project has already minted twice. Use
`finance/dev/dev_seed_smoke_db.py`, extend it to the live SHAPE (F-140), baseline it, then build, then
verify **differentially**. Everything else — mechanism, idempotency, write ordering (ledger first, then
the finance commit), fail-loud — is in **`S192_F6_Design_and_Survey.md`**. **Read whether `v_day_cash`
counts expenses on unapproved days before assuming anything about "the drawer is not touched".**

**⭐2 — F-153**, one line: `make_contra` must carry the original's `against_month`.

**⭐3 — the July salary close** from the owner-side sheet (waivers + actual-paid). The waiver
workflow's first real test.

**⭐4 — watch the August close** — the first month-end where the schedule lane, the capacity rule and
the quota lane all fire together.

**Live backlog in full: HANDOFF_RUNBOOK v128 §2.**

---

## CARRY THESE

- **A warning is a finding** (F-152 came from a line of publish output nobody had to act on).
- **A gate that fires wrongly is worse than no gate** (D316; met twice at S192).
- **Count checks programmatically, never by eye** — two S192 projections missed for exactly that reason.
- **Before asking the owner to do manual work, check what is already connected** (F-154), and never put
  an ellipsis in a command.
- **Survey → dry run → GO** for any correction to live money.

---

**Next free: D333 · F-155 · A-D25 · Session 193.**
**Cold kit: taken at the S192 close (count reset to 0 of 3–5).**

*START_HERE_SESSION_193 · generated at the S192 close. The manifest wins on what is canonical.*
