# HANDOFF RUNBOOK — v153 · Session 221 close · 03 September 2026 IST (midday)

**Tier 0.** §0 what happened · §1 mental models · §2 the live backlog · §3 install discipline ·
§4 the boundary. **§2 is the close-time snapshot; `OWNER_TODO_LIVE.md` is the always-current truth.**

---

## §0 — WHAT HAPPENED AT S221

**The ladder session. NINE KITS, ELEVEN LIVE FILES, every pin predicted offline and read back
identical** — and the queue-head fault (F-283, raised the night before) was closed and **proven on
the owner's own data within the same morning**. A man was onboarded end to end in the middle of it.

| kit | what went live | pin after |
|---|---|---|
| `S221_D355_LADDER` | **the identity ladder runs BEFORE the confidence gate** — clinic ID · full mobile · last-4 + name · same-day Docterz visit. The mobile is fingerprinted in memory and **stripped from stored raw** (F-287) | finance_ingest **747b4a50** |
| `S221_JAANKARI` | the Vaapsi desk's three Hindi lists — one question a row, three buttons; **an answer is append-only evidence, never a verdict** | returns_desk **1dc1fd62** · page **6d98e1b0** |
| `S221_CARDS_SCOPED` | the shared directory became **मेरे काम** — his four job buttons, filtered by owner, fail-safe when nothing declares one | darpan_card **4a31f14e** · registry **ded2f66e** |
| `S221_STOCK_FINDING` | the stock difference as a **printed, sealed audit document** — md5 over the quantities, recomputed on every read; answers, rulings and Marg vouchers in three append-only tables | stock_app **ed2f76ef** · page **83b0a1b0** |
| `S221_TWO_PRICES` | **loss at MRP and loss at cost, both honest** after F-290; coverage stated on the page; the drift log begins | stock_app **c627e440** |
| `S221_NIGHTLY` | the 22:30 push, the feed-health banner, and **of two exports of one date the later-taken wins** | push_snapshot **7722c33a** (CRLF) |
| `S221_PURCHASE_DUE` | **his punch became the ask** — purchases known to `pur_to`, Amir last here on `last_visit`; later means *he came and the export did not*. Read-only, fail-soft | stock_app **74825031** · drift page **ffe7333c** |
| `S221_AMIR_ACCESS` | the corrections desk and the count screens accept a named `viewer`; **seven routes verified still closed to him**; walk 29/29 | darpan_app **c98f0c24** · stock_app **4e929d0b** |
| `PUSH_STOCK_DAILY.bat` v2 · `PUSH_STOCK_NIGHTLY.bat` | baseline pinned to 02-09-2026; **a refusal can no longer print "Done"** (exit 3) | manojz, PC-side |

### The numbers that shaped the design

**78 %** of pharmacy bills carrying a real patient were bought **on the day that patient visited**;
only **2.3 %** more within three days — **D11's "days, not hours" is false for this pharmacy**.
**1,871 last-four values are shared; only 719 whole numbers are** — and the full mobile separated
**22 of 22** remaining ambiguities. On the owner's own 02-Sep export, re-ingested: **7 parked → 3**,
day total held at ₹17,644, variance 0, **all four named by the FULL MOBILE** (last-4: zero;
same-day Docterz: zero). Median **MRP ÷ cost = 1.40** over 147 items, 2 below cost; cost covers 187
of 376 items, MRP 180, **neither 156**. The sale-day test: **77 % of testable returns explain
themselves**, and three credit notes (₹2,878) survive scrutiny.

### The man in the middle of it

Amir Sohail — roster row (Emp Code **101**, biweekly, **₹2,500 fixed** regardless of visits,
minutes_exempt Y, allowed_offs 26 so absence cannot eat the retainer) · biometric enrolled · portal
login created (**it was never created by the joiner page — F-295, found when he stood in front of
the owner and it refused him**) · `unit_role` viewer on medical · his two PDFs delivered.

**Decisions:** none minted; **D367 remains free**. **Rulings closed:** *"history too"* approved ·
**F-244 RETIRED** · **§S205 STRUCK** · the registry gains one rule (ownership per card) · the
spot-count bridge PARKED until the drift log has a month or two. **Findings:** F-286 … F-296 minted,
**nine of eleven the assistant's own**; F-295 and F-296 are the owner's.

---

## §1 — MENTAL MODELS EARNED HERE

1. **Measure the question before answering it.** The owner asked what three identity strategies were
   worth. Measuring them overturned D11's window rule and proved the full mobile — not the Docterz
   list — was the rung that would do the work. Had the ladder been built to F-283's description, all
   four bills it named this morning would still be parked.
2. **A walk that supplies its own scaffolding proves the scaffolding** (F-286). The dead rung was
   green because the test built a connection the caller never builds. Exercise the real path with
   the real caller's objects.
3. **Never pipe a gate** (F-291). `| tail -1` took the walk's exit code and the chain restarted the
   service past a RED walk — **F-142, in the project that recorded F-142**. Check `$?` before `&&`.
4. **When a feed gains a column, every store that keeps the row WHOLE has gained it too** (F-287).
   A schema change upstream is a privacy review downstream.
5. **Prove what a column IS before it becomes money on a page** (F-290). A ratio on real rows —
   here MRP ÷ cost — is a ten-minute check that would have caught an inverted pair of prices.
6. **A role is not a scope** (F-296). The moment a second desk keys off the same role, the role has
   become a group, and a group needs a membership list. A permission walk must enumerate what a
   grant opens ELSEWHERE, not only what it was asked to open.
7. **A page never spells its own mount** (F-292) and **only a renderer proves what a page shows**
   (F-289, F-293). The S209 lesson and the F-142 family, both again.
8. **Predict PC-side pins as CRLF, VPS-side as LF, and say which** (F-294).

---

## §2 — THE LIVE BACKLOG (close-time snapshot)

**⭐0 — the owner:** the close publish (below) · export the stock and sale reports this evening (the
rest is automatic) · give Darpan his sheet · tap OK on any ₹1,000+ return · the rulings still owed
(the S214/S215/S216 candidate sets).

**⭐1 — the build order:**
1. **`returns.desk_users` — F-296, THE FIRST THING NEXT SESSION.** An opt-in allow-list on
   `returns_desk.py`: if set, only those people plus maker/checker may open the desk; **if unset,
   nothing changes**, so reception's access cannot break. One live file, plus its browser gate
   re-run (the page's standing rule since S214). *Approved by the owner at this close, deliberately
   not built here.*
2. **Amir's finish** — hide the owner-only ledger-check and transfer controls the corrections page
   still draws for a viewer (they refuse him safely, but a control that refuses is a trap); tick
   CREDENTIALS_SENT and STAFF_MASTER so his joiner record closes at 6/6.
3. **The joiner page** — a `wa.me` send link, and create the portal login it prints (F-295).
4. **The whole-history re-join** — approved (*"history too"*), tool on the box, one command.
5. **Marg's user-wise register on the router** (⭐1-3, parked by the owner) — WHO keyed each bill.
6. Then: M3 purchase tables (backfills loss-at-cost on every finding) · M4 Phase B · M5 · M6 · the
   F-269 route patch · Docterz feed Phase 1 · the August staff close · the scanner A5 vertical resize.

**Standing holds:** AUGUST PURCHASE IS PROVISIONAL · NEFT portal WAITS · the hub's shape is not
reopened · **the spot-count bridge is PARKED by the owner** until the drift log has a month or two
of Marg cross-checks.

---

## §3 — INSTALL DISCIPLINE (as S220, extended by this session's own failures)

- Anchored patchers, verbatim anchors, refuse-unless-exactly-once, `.bak` beside the file, compile
  check with restore, `MARK` for idempotence. One paste per kit, every current pin guarded by `test`.
- **Reproduce the live bytes offline before anchoring**; predict every pin, and **name the line-ending
  convention** — PC-side CRLF, VPS-side LF (F-294).
- Selftest on a COPY of the live db, then a **LIVE-SHAPE walk through the real entry point with the
  real caller's objects** — not the harness's (F-286). Where a helper's contract is invisible, cross-
  check two implementations against each other on real rows.
- **Never pipe a gate** (F-291). Check the exit code explicitly before chaining.
- A browser render in real Chromium for any page change, run as a **differential against the
  unpatched artefact** so the harness's own gaps cannot be reported as the page's (F-293).
- A permission change ships with a list of **every route that keys on that role** (F-296).
- No compile, no `git status`, nothing that writes, inside a kit folder on the owner's disk.

---

## §4 — THE BOUNDARY

Built and live: everything in §0. **Designed, approved and deliberately NOT built at this close:
`returns.desk_users` (F-296)** — it is §2 ⭐1-1 by the owner's instruction, *"EOS HERE, AND DO
WHATEVER NEEDED NEXT SESSION TO SETUP THIS."* Also unbuilt: hiding the owner-only controls on the
corrections page; the joiner page's send link and login creation; the whole-history re-join (approved,
one command, not run); the spot-count bridge (parked by the owner, not by the assistant); loss at
purchase for the 189 unvalued items (backfills when M3 lands).
