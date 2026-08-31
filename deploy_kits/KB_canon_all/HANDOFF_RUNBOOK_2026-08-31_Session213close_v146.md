# HANDOFF RUNBOOK — S213 close · 31-Aug-2026 (night) · v146

## §0 · WHAT HAPPENED — the evening the decided order went live

S213 executed **⭐1.1 through ⭐1.4 of the order decided at S212, all live, all measured**:

1. **F-261 CLOSED.** `finance.db` ships to the owner's Drive nightly (cron 01:40) — kit
   `S213_FINDB_DRIVE` v2. The v1 design was refused live: **service accounts now hold ZERO Drive
   quota (F-265)**; v2 updates two owner-owned slot files (nightly ≈30 revision restore points;
   monthly pinned forever). First shipment verified by Drive's own md5 read-back, twice.
2. **The returns card reads the sump** — kit `S213_RETURNS_CARD`. Live darpan bytes rebuilt
   offline byte-for-byte before patching; the GET write removed; item_key matching; the day-gaps
   API's `returns=`/`payment=` restored — and its r1 route was found ALREADY LIVE, unrecorded
   (**F-266**: a pin's identity note is not the file; the grep is). **Live-shape from the owner's
   own page: 2026-08 · 45 returns · ₹19,226.75 · 26 NEED YOU · three populations named.**
   Display polish / analytics / send-to-Darpan **PARKED by the owner (D357)**.
3. **Rung 4 through `finance_money`** — kit `S213_RUNG4`, **measured on the live db before
   install**: +37 recovered (the `S186-F104-…` composite refs), 1 rate-coincidence retired,
   0 re-attributed. **Examinable coverage 81 → 117 of 179.**
4. **F-245 CLOSED — the stock screen exists.** Kit `S213_STOCK_SCREEN`: the S207 counting page
   served live from the ledger's own snapshot; "Send to ledger" fills `stock_count` /
   `stock_count_item` / `stock_diff`; the diffs page names the doors; the server's snapshot is
   the authority on `marg_qty`. Both pages owner-verified.

Also: the Phase-0 manifest sweep re-pinned two stale rows with recorded dispositions (**F-267**);
**F-268** — sqlite must never write inside the mounted repo, and a walk is not finished until it
has run on the machine it claims to prove. Faults **F-265…F-268** minted; **eleven live pins**
moved/created, each verified against kit bytes. Archive **v1.60** · Fault Register **v2.47** ·
Register **v5.62**. Four publishes, each verified.

**New fault codes:** F-265 (SA zero Drive quota) · F-266 (pin identity ≠ file) · F-267 (two stale
manifest pins, one unprovable) · F-268 (sqlite on the mount). **SOP changes:** every SA-to-Drive
design starts from update-in-place; database writes never inside `mnt\`. **Surveillance-scope:**
no change — the returns card widens the OWNER's view of existing data only.

## §1 · MENTAL MODELS THAT HELD

- *A kit's KIT_ID, a pin's identity note, a README's claim — none is the machine. The grep is;
  the database is better.* (F-266 joined the S212 rule's family the same day.)
- *Measure before install where the change moves numbers* — the rung-4 table (+37/−1/0) is what
  made that install a formality instead of a debate.
- *A walk that has not run on the target machine has not walked* (F-268; also how S213 caught
  the sandbox-vs-manojz sqlite difference the same hour it mattered).
- *Preflights exist to be refused* — the zero-quota 403 cost one design, not one byte of data.

## §2 · THE LIVE BACKLOG — the truth is `OWNER_TODO_LIVE.md`; the shape:

**⏰ with a clock:** VINBACTUM DS write-off · RUNVACE TP · the unbanked pile (32+ days) · the
August close items · Amir biometric.
**⭐0 owner:** F-185 in `marg_report.py:599` (his ruling) · Amir's salt work list · the S210 seven ·
publish-sweep extension OK · delete lists (now incl. `_to_delete_S213\`) · token rotation (parked) ·
F-244 ruling · the carried tail.
**⭐1 build order (remaining):** 5 `marg_effective` wherever a month is totalled · 6 the anomaly
baseline (before that card nears a page) · 7 the counter flow (S187 D-R) · Docterz · the 360 strip.
**Parked by D357:** returns-card display setup · further analytics · send to Darpan.
**Phase B of the stock screen (recorded):** batches into the snapshot push · revive
`PUSH_STOCK_DAILY.bat` (never completed a run) · the orthotic category flag.
**First real use:** a staff stock count with a bill anchor — the day the three tables fill.

## §3 · INSTALL DISCIPLINE — unchanged, and it earned its keep four times tonight

Build/test offline → walk on the REAL machine where possible → publish (owner's double-click) →
deploy-clone pull → owner pastes, one line each → pins captured the same hour and verified
against kit bytes. Patches refuse on anything but the exact expected bytes; pre-checks before
overwrites; every backup path printed.

## §4 · THE BOUNDARY

Patient data stays out of git (F-185); the db.gz on Drive goes only to the clinic's own account,
which already carries `patient_diagnosis.csv` nightly. The VPS credentials remain the owner's
alone, by design. Nothing in S213 changed who can see what — except the owner, who can now see
his returns and his stock.

---
*v146 · S213 close · supersedes v145. §0 is the session record; the Archive §S213 is the narrative
of record.*
