# HANDOFF RUNBOOK — v145 · Session 212 close · 31 August 2026 IST

**Tier 0.** §0 what happened · §1 mental models · §2 the live backlog · §3 install discipline ·
§4 the boundary. **§2 is the close-time snapshot; `OWNER_TODO_LIVE.md` is the always-current
truth, and each points at the other.**

---

## §0 — WHAT HAPPENED AT S212

**A survey-and-repair session. NOTHING WAS INSTALLED — not one file on the VPS, on manojz, or on
the medical PC. One publish is pending.** The value is in what was found, and in **four
corrections the owner made from his own memory, every one of them right.**

It began as a build — the sump — and he stopped it to ask whether it duplicated the Marg
purchase and stock system he built at S206. **It did not.** But the question turned the session
into a full audit of the estate against the running machines rather than against its own
documents.

### The finding that reframed everything

```
stock_snapshot   376     a machine filled this
stock_rate       187     a machine filled this
stock_count        0     a PERSON must fill this
stock_count_item   0     a PERSON must fill this
stock_diff         0     computed from the two above
```

**Everything a machine can fill is filled; everything a person must fill is empty, because there
is no page for them to fill it on.** He said it first — *"all ready at VPS, working at backend,
writing data, only front end was not installed"* — and the database proved it.
**The remaining work is screens, not engines.**

### Five findings of record

1. **A sale-returns card is ALREADY LIVE** and no backlog noted it — `finance_approvals.html:740-798`
   with `cn-detail`/`cn-approve`, `darpan_return_approval`, an approval workflow, and the owner's
   own ruling in the code. **It reads `sale_item` only: 63 of 179 returns.** It also writes on a
   GET and matches raw `item_name` rather than `item_key`.
2. **The reinstall kit cannot restore the medical PC (F-259/F-260).** Its sender is the pre-AF-1
   version that can blacklist a real sale report **permanently**; the agent is two versions old;
   four files are in no kit at all, including screen coordinates that cannot be recreated. **The
   kit's own MANIFEST predicted the drift; five sessions passed while `SUMS.md5` stayed green,
   because it hashes the kit against itself.**
3. **`finance.db` has no offsite backup (F-261)** while the clinic CSVs get one nightly.
4. **Marg's two expiry reports are indistinguishable (F-262)** and had silently hidden
   `VINBACTUM DS` — the shop's entire expired exposure, ruled for write-off.
5. **S206 already held the money model (F-264)**, and the pack rule is written **seven times**.

### Built — staged, gates green, installed nowhere

`S212_SUMP` · `S212_SUPERSEDE` · `S212_LIVE_TOOLS`. Three PC kits repaired (they were hard-coded
to the assistant's sandbox mount and **could not run on manojz at all**). Four brittle selftests
re-based from frozen snapshots to invariants.

**234 selftest checks green, 0 failed. 1,071 gate rows green across 186 kits, 0 red.**

### Close artefacts

Archive **v1.59** (§S211 + §S212, prefix proven, +11,212 bytes) · Fault Register **v2.46**
(**F-247…F-264**, discharging the twelve S211 left owed) · KB Register **v5.61** · manifest
updated and pin list regenerated with **`register_pin_verified: yes`** · canon snapshot ·
`MANIFEST.md5` **773 rows** · **SSD mirror and cold kit taken and verified by listing back** —
S211's one data-safety gap, closed · **the complete session transcript exported** at the owner's
request · reduction tranche **−124,985 bytes, 71.4% → 65.2%**.

---

## §1 — MENTAL MODELS EARNED HERE

1. **A kit's `KIT_ID.txt` is not evidence of what is running. The live pin is. The database is
   better.** Two kits declare "STAGED, NOT INSTALLED" while their bytes run on the VPS.
2. **A gate that compares a thing to itself cannot detect drift.**
3. **`uploadable: false` is the quietest possible way for a feed not to exist** — nothing fails,
   nothing is logged; the reports are captured, verified, archived, mirrored offsite, and stop.
4. **Before deriving a rule, search the repository for it.** Named as the largest waste of S211
   and repeated at S212.
5. **A test pinned to a moving number teaches people to ignore red.**
6. **Three empty tables beside seventy full ones is a missing screen, not a broken pipeline** —
   read *which* tables are empty before diagnosing why.
7. **`F:` has three states, not two:** mounted-in-shell (never), reachable by transfer tools
   (normal), and **gone entirely** (new at S212 — connected in the app, path absent).

---

## §2 — THE LIVE BACKLOG (close-time snapshot)

**⭐0 owner:** publish · the VPS deploy-clone pull · `VINBACTUM DS` write-off voucher · Amir's
untouched salt work list + a fresh `SALT WISE ITEM LIST` afterwards · the S210 seven · the
publish-sweep extension · the delete lists · token rotation · F-244.

**⭐1 build, in order:** `finance.db` into the nightly Drive backup · the returns line (**keep the
live card's approval workflow, swap its data source to the sump**) · ladder rung 4, which sums
rates against money · the stock screen (F-245) · adopt `marg_effective` · fix the anomaly
baseline before that card goes near a page · then the counter flow (S187 D-R, signed and
unbuilt), Docterz, the 360 strip.

---

## §3 — INSTALL DISCIPLINE

Unchanged, plus three earned at S212: **`python -B` always** (two kits were built with bytecode
inside their own gate) · **check `.git` for `*.lock` as a whole class** · **`MARG_ARCHIVE` is the
one setting that locates the archive for the PC kits** — never hard-code a path again, and never
a sandbox path.

---

## §4 — THE BOUNDARY

Nothing live is rebuilt without his OK. The publish is his double-click. The assistant cannot
delete on his machines and should not want to — it moves, marks and proves, and he decides.

**S212 respected this completely: not one live file was touched.**

---
*HANDOFF_RUNBOOK v145 · S212 close · 31-Aug-2026. Next free: D357 · F-265 · Session 213.*
