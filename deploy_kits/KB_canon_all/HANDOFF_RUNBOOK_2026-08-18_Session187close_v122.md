# HANDOFF RUNBOOK — v122 (Session 187 close · 18 Aug 2026)

> **Tier 0.** §0 what happened · §1 mental models · §2 the live backlog · §3 install discipline.
> **The canon is current and NOTHING is owed at this close** — third clean handover in a row, and the
> first whose pin list the checker can PROVE against the manifest on the box (F-110/F-117/F-122 all
> structurally closed). Expect the pin run to read **GREEN, and mean it.**

---

## §0 — WHAT HAPPENED (Session 187)

**Eight kits live in one session, every one landing exactly to its stated projection.** Two design
contracts signed. The publish step collapsed to one desktop icon. No incident — one install went RED
(F-125) and the gate restored byte-perfect; one installer died AFTER its work (F-126) with nothing
half-applied.

**Thread 1 — the attestation chain, made provable (`S187_V1a`).** Runbook v121 item 0 ("~3-line
fix") turned out to be unbuildable as written: the manifest's own "recomputed last" rule makes its
whole-file hash transient, so **every** `--manifest` generation had minted a phantom (`78881ddd…`,
`04eff42c…` — nothing in 157 commits; **F-122**). v1.2 of both tools: the generator writes the
stable `manifest_current_register_pin`; the checker **proves it on the box** (hash-hunt in
`/root/deploy/repo` canon by `source_md5`, manifest CURRENT-row parse) and cannot print VERIFIED
without proof. Found en route: **F-123**, a second, S177-stale `CANONICAL_MANIFEST.md` in
`canonical-docs/` still calling itself canonical — retired at this close. The V1a publish also fired
**F-124** live: `PUSH.bat` printed "pushed" over a swallowed `HEAD.lock` fatal; v2 verifies origin
HEAD before claiming success.

**Thread 2 — B5: reception pushes the Marg report (`S187_M1a`, D325).** Double-click sender on the
medical PC (dependency-free; copies first, never writes in `D:\MARGERP`, sent-hashes, dated copies,
bilingual output) → scoped stage-only `FINANCE_MARG_TOKEN` (one path, no identity, fail-closed) →
file parsed, surveyed, staged in `marg_push_staging`, **deleted in-request** → the checker alone
applies from the Hub through the same guarded ingest. **Proven end to end: reception's first real
push was ACCEPTED and staged the same day.** Setup cost two token lessons — one typed into a repo
copy (caught by masked diff, reverted before push), one pasted into chat (declared burned, rotated
on the spot). The sender now wears a desktop icon ("SEND TO CLINIC").

**Thread 3 — Daily Flow v2 contracted; stage D1 live (`S187_D1a`, D326).** One canonical Day Page;
save-then-see with `edited_after_reveal`; salary bridges to the Staff Ledger (gated on §2-item
backlog: the ₹70,000 check); Yes Bank feeds via the owner's personal Gmail at D5. The owner then
specified the **returns-at-reception system in full** (eligibility legends: expired = INELIGIBLE ·
>2 months = FLAGGED · ≥1 month old AND <1 month expiry = DISQUALIFIED; print slip; Darpan books the
CN; CN ⇄ logged-return reconciliation), the 360 lookup, refill-skipper intelligence, orthotics stock
from **asset-app-scanned purchase bills**, and Tailscale+RustDesk remote access — all signed into
the addendum. **Build PAUSED by the owner: S188 opens on this contract.** D6 (contextual per-user
instructions) parked in the same addendum.

**Thread 4 — every seat's portal tile speaks (`S187_P1a`→`P1b`→`P2a`).** The Sanjeevni tile lands on
the Hub with live pending counts; Darpan's Daily Sale tile carries his own D322-aware to-do line;
clinic tiles carry maker/checker counts server-side. P1a's install RED (388/389) was **our test
broken by the first real push** (F-125) — gate restored, check scoped to its own bytes, re-rehearsed
against the failing condition, 392/392 live.

**Thread 5 — the Sanjeevni Hub (`S187_H1a`→`H1c`).** "This page shd become the sole place for any
Sanjeevni info and work for me" — Marg upload + pushed-Apply moved in, cash register with
drill-down, custody (the money with Dr Bhawna), month grid, orthotics (vocabulary as a setting; qty
deliberately not summed), exceptions; one shared Day-Page renderer; 400/400. Then the design ruling:
**`Clinic_Design_Language_v1.md` is THE DEFAULT from here** (warm surfaces, sticky branded header +
tabs, tabular numerals, bounded tables, stat tiles, icon+label status, folded help, floating
back-to-top). H1b retired unlived; **H1c live: the owner's real Canva logo + "Dr. Manoj Agarwal
Clinic" with the tagline beneath.**

**Thread 6 — publishing (`PUBLISH_ALL.bat`, D328).** One desktop icon publishes everything pending
with every gate; origin HEAD verified before success is printed; proven on its first field run.
Autonomy boundary stated: repo-write credentials never transit chat; a deploy key is an explicit
S188+ decision if wanted.

**At this close:** Archive **v1.36** · Fault Register **v2.22** (F-122…F-126, no owed append —
second close running) · Register **v5.22** · manifest rebuilt and **de-duplicated** (the five
"(pre-…) CURRENT" rows) · the two owed S186 docs + three S187 design docs **filed and pinned** ·
F-123 executed · pin list regenerated from v5.22 → **the first provable GREEN** · morning's three
record faults (START_HERE 187 self-contradiction · v120 footer on v121 · the duplicate CURRENT
rows) all corrected in the rebuilt documents.

---

## §1 — MENTAL MODELS

1. **Carried and undiminished:** survey the box before writing to it · the bank arbitrates, the
   human confirms · the fold-in belongs at the head of a session, never the tail · a record
   asserting something about another component is a claim, not a fact · a true statement can expire
   · test the mechanism, do not argue about it · the projection is the check · a count beats a
   derivation · record live pins as they move.
2. **⭐ Never attest to the hash of a file whose rules say it will change after you hash it (F-122).**
   Attest to the stable value inside it that constitutes the claim. A true hash of a state that no
   longer exists is indistinguishable from an invented one — three phantoms in two sessions came
   from this one mechanism, not from three mistakes.
3. **⭐ A checker may not print a claim it did not test (F-117/F-122).** "VERIFIED" is a word the
   tool must be structurally unable to emit without proof. The v1.2 checker earns the word on the
   box or says AMBER and why.
4. **⭐ A gate that fires is the system working (F-125).** The P1a RED was caused by our own test and
   restored everything byte-perfect. The right response to a RED is gratitude and a root cause,
   never a retry. Fourth firing of the F-106 family — tests assert behaviour, never store
   population, and a fixed test is re-run against the state that broke it.
5. **⭐ The untested path was the exit (F-126).** A rehearsal exercises one path; `bash -n` reads
   them all. An installer that dies after acting is indistinguishable from one that died before.
6. **⭐ Secrets have a one-way valve into chat (D328).** A token pasted into chat is burned — proven
   twice in one day, once averted from a public repo by a masked diff. Repo-write credentials never
   transit chat at all, because repo-write is the deploy chain's trust anchor.
7. **Design is a contract, not a coat of paint.** The Hub redesign shipped as a page-only kit with
   every element id and API path byte-preserved, provable by the selftest differential. Presentation
   and contract can move independently when the contract is pinned.

---

## §2 — LIVE BACKLOG

**⭐ 0. Prove the GREEN.** After this close is published and pulled: regenerate/place the close's pin
list, run `python3 /root/deploy/verify_live_pins.py` — expect **GREEN with `source: VERIFIED`**, the
first the checker can prove. If AMBER, read its stated reason; if RED, the record moved after the
close and the drift is evidence about the record first (F-118).

**⭐ 1. The S188 build, on the signed contract** (`S187_Daily_Flow_v2_Target_Design` + the
returns/360 addendum — both pinned): **D-R returns at reception** (with the **D327 `counter` role**)
→ **D2 Darpan's mirror** → **360 wiring** (Console strip + refill-skippers) → **orthotics
purchase side** (read the asset app's scan-purchase data model first) → **D5 feeds** (Yes Bank via
personal Gmail — forward-rule vs scoped script decision) → **D6 contextual instructions** (parked).
Proposed order recorded in the addendum §8.4; the owner picks the entry point.

**⭐ 2. The §4a gate: the Staff Ledger ₹70,000 check.** Darpan's advances (₹40,000 S184 + ₹30,000
17 Aug) rest on an unverified SQL-comment claim ("tracked in salary system, NOT posted to Ledger");
he is also skipping an August loan instalment to be recovered in September. **D326(c) blocks the
salary bridge until this is verified.** Read-only check first.

**3. First pending reception push** — awaiting the owner's **Apply** on the Hub's Marg card.

**4. Darpan's ₹30,000** (three scans; the ₹10,000's category still undecided — free text if it
settled July salary, `salary_advance` if new). Cash reads ₹2,05,198 until entered; ₹1,75,198 after.

**5. 14 & 15 Aug** — still `draft`; submit and approve.

**6. 12 June ₹8,487 over + 3 May zero-lines** (re-upload May's export through the Hub; 9 May −₹665
and 2 Jun −₹690 likely clear with it).

**7. Orthotics vocabulary** — the Hub's orthotics card waits on the owner entering keywords
(a setting, no kit needed).

**8. Tailscale + RustDesk rollout** — guided config, owner's PC + medical PC first (~30 min at both
machines), then lab / reception / manager. Parallel to any build stage.

**9. Hindi labels** (parked by owner) — unblocks the custody block on Darpan's entry screen; pairs
naturally with D6.

**10. Owed and named:** CLI `marg_backfill.py` NOT-FILED flag + its `attributed ? · review ?`
display bug (F-113 remainder) · F-106 selftest split (invariant vs fixture halves) · F-97 part 2
(loaded-in-memory check · PC-side pin half · triage of the **76** untracked live files) · F-107/F-108
structural checks made mechanical · 4 May and 27 May missing days · medical-PC icon run
(`MAKE_DESKTOP_ICON.bat`, one double-click, files already in the M1a kit folder).

**11. Carried:** WABA go-live (F-82, vendor) · security rotations · console follow-ons · F-92
discount capture · F-93 concession-parser footer · item-wise go-live decision formally recorded
(de facto live daily via B5).

**12. If the owner wants full publish autonomy:** a scoped deploy-key decision (D328's boundary),
risks written down first.

**Cold-kit count: reset at this close** (`KB_S187_close` zip delivered; next due within 3–5
sessions).

---

## §3 — INSTALL DISCIPLINE

The D317 kit chain stands: SUMS → KIT_ID → currency/state gate → precheck or smoke **before** any
swap → backup → apply → verify → **an honest red that restores**. Standing additions this session:
**`bash -n` the WHOLE installer before shipping (F-126)** · a fixed test is re-rehearsed against the
state that broke it (F-125) · `gen_live_pins.py`/`verify_live_pins.py` **v1.2** — attest the stable
claim, prove it on the box, VERIFIED only on proof (F-122) · **`PUBLISH_ALL.bat` is the default
publish method** (D328): whole-tree, HEAD.lock refusal, scoped F-100 gate, real commit failures,
origin-HEAD-verified success; per-kit `PUSH.bat` v2 as fallback.

Financial-book changes remain **gated migrations, offline-rehearsed against a copy of the real
store, reversible, never ad-hoc SQL**, projected before applied. `verify_live_pins.py` at every open
and close; the Register is corrected **FROM the box** (D321(d)). PHI, `finance.db`, raw Marg exports
and tokens never enter the repo, a kit, or chat (F-31 / F-49 / D320 / D328); exports upload through
the portal or push from reception and die inside the request.

**END OF HANDOFF RUNBOOK v122 (Session 187).**
