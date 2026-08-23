# S195 — The Marg correction checklist (A3+++)  ·  **LIVE**

**Live pin:** `finance_app.py` = `8c7dc9660444ee8724402920bf1e3438` · smoke **613/613** (was 573)
Installed 22-Aug-2026 07:22 from `deploy_kits/S195_A123D.tar.gz` (`1fdbd3bdf9ed69e12275db85c2c66380`)
Backup: `/root/finance/_backup_S195_A123D_20260822_072214`
Previous live pin (gate): `e3a4ba79c2e060bcebe11c075bdbbc7b`

Superseded and **never installed**: `S195_A123`, `S195_A123B`, `S195_A123C`.

---

## Why

The bank statement is the only independent witness to the cash/UPI split. Marg labels
every bill `.CASH`, so the split is read off the POS screen in the morning and typed
by hand. `_upi_misclass()` (A3) finds the days where the bank and the books disagree,
**and which way** — but a finding is not work. Someone has to change the bill in Marg,
someone has to check it happened, and Darpan has to learn from it.

This turns each finding into a tracked item.

## The one design decision that matters

**The checklist closes itself.**

An item is open *because its day still disagrees*. Correct the bill in Marg, re-export
that day (BILL WISE SALES, Detail, With Item Deta. = Yes), send it, apply it — the day
stops disagreeing, and `_correction_sync()` moves the item to Done on the next read.

Nobody ticks anything off. A checklist that relies on someone remembering to tick it
stops being true within a fortnight; this one cannot drift from the books, because it
*is* the books.

Two consequences follow deliberately:

- A **partial** fix re-opens the item and updates the amount. Half a correction is not
  a correction.
- A finished item is **kept, not deleted** (`?all=1` shows them), and its description is
  rebuilt from the stored `diff_p`/`direction`, so the record still reads as a piece of
  work after the disagreement is gone.

## What is live

| Route | Who | What |
|---|---|---|
| `/finance/marg-worklist` | checker | The list. Status · deadline · owner · note per day. One control sets the schedule for the whole open list at once. Printable (controls and finished items drop out in print). |
| `GET /finance/api/marg-corrections` | checker | JSON; `?all=1` includes finished. |
| `POST /finance/api/marg-corrections` | checker | Set status / `due_date` / `assigned_to` / `note` for one day. |
| `POST /finance/api/marg-corrections/schedule` | checker | Deadline + owner for every unfinished item — the "I set a schedule for him" half. Never touches a finished item. |
| `GET /finance/api/marg-corrections.csv` | checker | The file to hand Amir. Carries the re-export warning as a row. |

Table `marg_correction` (lazily created): `unit · business_date · diff_p · direction ·
status · due_date · assigned_to · note · created_at · updated_at · resolved_at`,
`UNIQUE(unit, business_date)`.

Statuses: `open` → `sent` (given to Amir) → `corrected` (fixed in Marg, awaiting
re-export) → `resolved` (books agree). Only the last is set by the system.

**Health page** gained a *Correction checklist* line: how many days are outstanding, how
they are distributed across the statuses, and **bad** (not warn) if anything is past its
deadline, with a link straight to the list.

**Darpan's feedback** — `_maker_accuracy(con, 30)`: of the days the bank could actually
verify, how many of his splits matched. It rides in two places:

- `api_my_day_summary` gained an `accuracy` block (for the portal tile — *the portal
  renders it only after `portal.py` is touched; not done*).
- His **own save response** names the score and the differing dates. Silent when every
  checked day matched. This is the part he sees today, in his own workflow, without any
  UI file changing — and it is what tells him the entries are being watched.

## Reading an empty list

An empty checklist means one of two very different things, and the page cannot tell them
apart on its own: *every checked day matched*, or *the bank side was never loaded, so
there was nothing to check against*. `_upi_misclass()` only sees a day that has a
`upi_statement` row against that date.

The health page's **UPI evidence** line is what separates them — it names the days with
no statement matched. Read the two together.

## Three defects, three lessons

**1 · `S195_A123` — a name that was never assigned.** The save-time Marg comparison wrote
its `TOTAL_VS_MARG` flag but the assignment of `_marg_gap_p` / `_marg_net_p` had been lost
during editing, so every medical day save would have raised `NameError`. Found by a static
undefined-name sweep, **not** by reading, and not by the local suite — which cannot run in
the Cowork sandbox at all, because `finance_ingest` is not there.

> **Standing lesson:** run `python3 -m pyflakes finance_app.py` before packaging any kit.
> `py_compile` proves the file parses; it proves nothing about names. The same sweep caught
> raw `%` in CSS inside a `%`-formatted page template (`flex:1 1 44%`, `width:100%`) — also
> accepted by `py_compile`, also fatal the first time the page opened.

**2 · `S195_A123B` — rolled back with no message.** A new check called `db()` directly.
`db()` needs a Flask application context; outside a request it raises, and the exception
aborted the whole suite before it could print a SMOKE line — so the installer saw nothing
and rolled back silently.

> **Standing lesson:** selftests ask over HTTP through the test client. Never reach for
> `db()`, `g`, or anything context-bound from the suite body.
> The installer now prints the **last 40 lines of the selftest** whenever no SMOKE line
> appears, so a crash is readable instead of blank.

**3 · `S195_A123C` — rolled back at 611/612.** One check demanded the per-day controls on
the checklist page unconditionally. On a box with nothing to correct the page correctly
renders "Nothing to correct" and has no controls. The assertion was pinned to one state of
the *data*, not to a property of the code — the **F-106 shape**, hit for the third time
this session. Split in two: the export is always offered; the controls are asserted only
where a day exists, and the empty state is asserted to say so.

## Deploy (for reference)

Publish from manojz (`PUBLISH_ALL.bat`), then on the VPS:

```bash
R=$(find /root -maxdepth 4 -type d -name deploy_kits 2>/dev/null | head -1)
cd "$R/.." && git pull --ff-only && \
cd /root/finance && tar -xzf "$R/S195_A123D.tar.gz" --overwrite && \
bash S195_A123D/install_s195_a123d.sh
```

## Not done

- `portal.py` does not render the `accuracy` block on Darpan's tile yet.
- No push of the list — it is pulled, not sent. Amir's editing schedule is still to be
  set, and until it is, a scheduled push has nothing to be late against.

---

## The git-lock fault, and the fix baked in (S195)

**What happened.** I ran `git status` against the mounted repo from the Cowork sandbox.
Git created `.git/index.lock`, and the sandbox **cannot delete files** — so the lock
survived. `PUBLISH_ALL.bat` then died on every run with
*"Unable to create '.git/index.lock': File exists"*.

**Two standing rules from it:**

1. **Never run git from the sandbox against the mounted repo.** Not `status`, not `log`,
   not anything — every one of them can take the index lock, and nothing in the sandbox
   can release it. Read files directly (`ls`, `cat`) and let the `.bat` files on manojz do
   all git work. To clear a lock the sandbox made, `mv` it into `_to_delete/` (move works
   where delete does not).

2. **A lock is only real while a git process is running.** Both publishers now check that
   themselves:

   - `PUBLISH_ALL.bat` and `PUBLISH_CLOSE.bat` scan for `index.lock`, `HEAD.lock`,
     `config.lock` (and `shallow.lock` in ALL).
   - Lock present and `tasklist` shows **no** `git.exe` → stale. The script deletes it,
     **says so on screen**, re-checks, and continues.
   - Lock present and git **is** running → real contention. Refuses, publishes nothing.
   - Lock will not go → refuses and names the reason.

   The old behaviour (refuse on `HEAD.lock`, tell the user to rename it by hand) is
   replaced by this. Nothing is cleared silently.

`PUBLISH_ALL.bat` was also converted from bare-LF to **CRLF** in the same edit. It now
uses `goto` labels, and `goto` in an LF-only batch file is a documented cmd.exe hazard —
CRLF is the native form, and every other `.bat` on that machine already uses it.

Originals kept at `_to_delete/PUBLISH_ALL.bat.before_S195` and
`_to_delete/PUBLISH_CLOSE.bat.before_S195`.
