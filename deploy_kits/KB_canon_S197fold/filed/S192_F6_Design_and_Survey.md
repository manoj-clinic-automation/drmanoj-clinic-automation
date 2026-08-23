# S192 · F6 — the request-not-draw flow: SURVEY + DESIGN (build not started)
### Session 192 · 19 Aug 2026 · D332 §2.5 · closes F-148

> **Nothing built.** This is the evidenced design, taken from the LIVE bytes, plus the honest reason
> the build was not started in this session.

---

## 1 · Provenance

Live `finance_app.py` = `deploy_kits/S190_F5/finance_app_F5.py`, md5
**`17e6b84ce90ca7d7a0a9ba0c668ab15f`** — hashes exactly to the Register's live pin. 7,867 lines.
The repo's `finance/finance_app.py` (`7b62b7ae…`) is **nine builds stale** and was not used
(F-97 part 2 / F-52; D188 — the kit copy was located BY HASH, not by filename).

## 2 · What the survey found — F6 is NARROWER than the contract implies

Three of the four pieces §2.5 asks for are **already live**:

| §2.5 requirement | State in the live bytes |
|---|---|
| Request capped inline at the ceiling, refused past it **with both figures** | **BUILT** — D330 "gate 1" at ~line 1467: returns `advance_over_ceiling` with `advance_taken`, `advance_ceiling` and a message naming both; hard refusal, no escape hatch |
| The ceiling is derived, never typed | **BUILT** — `advance_ceiling_p(con)` (D330/F-136) |
| Approval — not entry — is what posts to the Staff Ledger | **BUILT AS INTENT** — see below |
| The approval actually **writes the Staff Ledger row** | **STUBBED — this is F-148, and this is F6** |

The live approval endpoint (~line 1681) carries this, verbatim:

```
# Approval is what posts a salary advance to the Staff Ledger. Not entry.
advances = con.execute("SELECT id, amount_p, staff_id FROM day_expense "
                       "WHERE day_entry_id=? AND category_fixed='salary_advance' "
                       "AND ledger_posted=0", (e["id"],)).fetchall()
for a in advances:
    # B6 wires the real Staff Ledger call. Until then this records intent
    # explicitly rather than pretending the posting happened.
    con.execute("UPDATE day_expense SET ledger_posted=0, ledger_ref=? WHERE id=?",
                ("PENDING_LEDGER_WIRING", a["id"]))
```

**This is the codebase being honest about its own gap** — it records intent instead of claiming a
posting that never happened, and it returns `salary_advances_pending_ledger` to the review screen.
The schema is ready: `day_expense.ledger_posted` and `.ledger_ref` already exist and are already
surfaced (line 410). `staff_ref` is seeded with Darpan (F-139 fixed at S189).

## 3 · The design

**F6a — the ledger bridge (the actual F-148 closure).** At the approval point, replace the stub with
a real Staff Ledger write, then set `ledger_posted=1, ledger_ref=<ledger row id>`.

- **Mechanism: direct import, same box.** `sys.path.insert(0, "/root"); import staff_ledger` and call
  `make_entry(users, checker, staff, "ADVANCE_ISSUE", …, against_month=<the day's month>)`. Both apps
  run as root on the same machine; the ledger's store is a JSONL file its own module owns, so the
  write still goes **through the ledger's own writer** rather than around it (D235's principle kept:
  one writer per store — the module IS the writer).
- **The row it creates:** amount = the expense amount, `against_month` = the business month,
  narration naming the finance day and expense id, entered by the approving checker.
- **Idempotency is the whole game.** `ledger_posted=0` is the guard; the ledger row id goes into
  `ledger_ref`, and a re-approval must never double-post. The finance commit and the ledger append
  are two stores — **order matters**: append to the ledger FIRST, then record `ledger_ref` and
  commit finance. A crash between them leaves a ledger row with no finance ref (visible, recoverable)
  rather than a finance record claiming a posting that does not exist (invisible, the F-132 shape).
- **Fail-loud:** if the ledger import or write raises, the approval must **refuse** and say so — it
  must not approve the day while silently failing to post. A partial success that looks complete is
  the thing this system exists to prevent.
- **The ceiling is enforced twice, deliberately:** the finance gate refuses at entry, and the ledger's
  own D331 gate refuses at write. Above the ceiling it must be a SPECIAL with the signed application
  — which the finance path cannot supply, so an above-ceiling request correctly cannot complete here.

**F6b — "the drawer is not touched".** §2.5 says the request must not move drawer cash until the
owner approves. **Not yet verified**, and it must be before anything is built: it depends on whether
`v_day_cash` counts expenses on draft/submitted days or only on approved ones. **If the drawer only
moves when the day is filed/approved, F6b is already true and needs no code.** Establish this by
reading the view before designing anything — a display of the drawer built on an assumption is
F-133's shape.

## 4 · WHY THE BUILD WAS NOT STARTED — the honest blocker (F-87)

`finance_app.py`'s `selftest()` begins:

```
live_db = DB_PATH
shutil.copyfile(live_db, tmp_db)     # a throwaway COPY of the real store
```

The 550-check smoke suite **runs against a copy of the live `finance.db`**, which exists only on the
VPS. It **cannot be run in this session at all.** Shipping a change to it on reasoning alone is
precisely **F-87** — *"a change was shipped to a test suite that could not be run offline, twice"* —
which this project has already minted, and whose stated RULE is: **if a test suite cannot be run,
making it runnable is the FIRST task, not an optional one.**

The remedy asset exists and is named in the Register as deliberately kept:
**`finance/dev/dev_seed_smoke_db.py`** (3,266 bytes, in the repo). The correct sequence is therefore:

1. Build the seeded store from `dev_seed_smoke_db.py`, extended to carry the **live SHAPE** (F-140):
   an approved day carrying a `salary_advance` expense with `ledger_posted=0`, plus a `staff_ref` row.
2. Run the **unmodified** app against it and record the score (it will NOT be 550 — the store
   differs; that is expected and is exactly why the method is differential).
3. Build F6a, run the **modified** app against the identical seeded store, and require
   **zero failures added** — the F-87 method, the one that worked at S180.
4. Only then the D317 kit, with the projection written before measuring.

**A cross-book money writer is the last thing that should ship on a plausible argument.**

## 5 · State of D332 at this point

| Kit | Contents | State |
|---|---|---|
| `S192_SL5` | waiver instrument · policy settings · F-151 wording | **LIVE** (`0ed19495…`, 218→240) |
| `S192_SL6` | schedule lane · DEFER · capacity rule (F-147) | **LIVE** (`0279540e…`, 240→274) |
| `S192_SL7` | per-staff Perks view (F-149) | **built + in the repo**, awaiting install (`44e39d6a…`, 274→287) |
| `S192_F6` | the ledger bridge (F-148) | **designed, not built** — blocked on the seeded-store rehearsal above |

Also done this session: the **gated data corrections** (D332 §6 items 1–4) executed after survey →
dry run → owner's GO; see `S192_Gated_Data_Corrections_Executed.md`.

## 6 · Process note (the F-45 family, third instance this session)

Two of the three kits this session had a projection that missed by a small margin — SL6 projected 270
and measured 274, SL7 projected 286 and measured 287 — **both times because the assistant counted his
own new checks by eye.** Neither was a behavioural surprise; both reconciled exactly against the test
block (`ck(` occurrences minus the `ck(False, …)` guards that sit inside `try` blocks and never run).
**The fix is procedural and was adopted mid-session: count the block programmatically BEFORE running,
never by eye.** Recorded because a projection discipline whose misses go unstated is theatre.

---
*Survey and design only. Session 192.*
