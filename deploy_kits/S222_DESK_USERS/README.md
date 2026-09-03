# S222_DESK_USERS — `returns.desk_users`, and the end of F-296

**Session 222 · ⭐1-1 · 03-Sep-2026**

## The question that opened this

> *"Why have you added him to the medicine return वापसी desk?"* — the owner, at the S221 close

He had not been added. **`viewer` IS the desk's key**, and has been since S214. Amir needed
`viewer` for his corrections desk and the stock count, and that one word also handed a
purchase man the power to issue cash refunds.

The cause is older than Amir and worse than a slip. S214's ruling was *"the desk is worked by
NAMED reception staff"* — and **the name was never written into code**. The desk asks *are you
a viewer?* and has never asked *are you one of them?*. So the rule was: **anyone ever given
viewer gets the returns desk**, for as long as the clinic exists.

The S214 file even carried the reassurance, in its own docstring:

> *"and NO other finance route accepts viewer, so it grants THIS desk and nothing else"*

True when written. **False from S221**, when `darpan_app.py` and `stock_app.py` both learned to
accept a viewer. Nobody went back to the sentence. **A comment that states a guarantee the code
does not enforce is how this happened**, and this kit corrects the sentence as well as the code.

*And it should be said plainly: the S221 walk recorded* `AMIR CAN OPEN: the Vaapsi desk` *as a*
***PASS***. *The walk was asking whether the grant worked, never whether it was too wide. The
owner read the list and saw what the walk could not.*

## What is built

One opt-in setting, read at the desk's single door.

| `returns.desk_users` | what happens |
|---|---|
| **set** | only those logins — plus **any maker or checker** — may open the desk |
| **unset, blank, or unreadable** | **nothing changes.** Every viewer reaches the desk exactly as today |

Seeded with the owner's own four: **Darpan · Shavez · Alisha · Shivani**.

**The unset case is a ruling, not laziness.** It is the owner's constraint: reception must not
be lockable out by a half-applied change. For the same reason a *database error* while reading
the setting **allows**. This gate exists to keep a purchase man out of a cash-refund screen; it
is not a lock on the front door, and it must never be the reason the counter stops working at
eight in the evening. Written here so it is never mistaken for an oversight.

**Makers and checkers never appear on a list.** Darpan is a maker and the owner is a checker;
neither should depend on a row somebody might blank.

## Why one file, and only one place in it

Every route the desk serves — the page, `/api/search`, `/api/history`, `/api/items`,
`/api/catalog`, `/api/slip`, `/api/slip/settle`, `/api/slip/void`, `/api/slips`, and the S221
`/api/jaankari` pair — calls `_auth()` and returns its error unchanged. **`_auth()` is the only
door.** That was verified by reading all eleven routes, not assumed, and the walk re-checks it
on the box (`_require(*DESK_ROLES)` must appear exactly once).

`returns_desk.html` **is not touched**. Its pin must read the same before and after.

## What it is proven by

| gate | result | what it actually did |
|---|---|---|
| `selftest_desk_users_s222.py` | **GREEN 26/26** | the truth table through the **real** `_auth()` — unset, blank, set, mixed case, a broken database, and a caller who is not even a viewer |
| `walk_desk_users_s222.py` | **GREEN 36/36** | mounts the **real patched blueprint** on a copy of the database; refuses Amir on **all twelve** routes; opens the desk for all four; then **blanks and deletes the row and re-walks** to prove the fail-safe is real |
| `RENDER_TEST_jaankari_s221.py` | **GREEN 26/26** | headless chromium opening the patched desk and **tapping through the Hindi card** — the standing rule for this page since S214 shipped it with dead taps |

Offline proof rests on an exact reproduction, not a resemblance: the repo's S214 bytes
(`afc8b0d0…`) plus the repo's own S221 patcher reproduce **`1dc1fd6229e74c60e0eceb4a14db8aeb`**,
the live pin recorded at the S221 close — and the html chain reproduces `6d98e1b0…` likewise.
See `PREDICTED_PINS.txt`. Those two rows are still **PENDING** until one `md5sum` on the box:
a reproduction is not a box read, and **A0 stands**.

## What Amir keeps

Everything else S221 gave him: his corrections desk, the stock count screen, the differences
list, the audit finding, and answering a difference line. **No role is added or removed** —
this kit writes one `setting` row and nothing else. The walk's §8 re-opens his other screens as
him; in the workspace those two modules are not present, so **that section is proven on the box,
at install, and nowhere else**.

**And that is exactly where it bit.** §8 shipped with a *guessed* route (`/finance/stock/count`;
the real one is `/finance/stock/page/count`) and a *guessed* init signature (`darpan_app.init`
takes no `url_prefix`). On the box Flask answered **404 for a path that does not exist**, and the
walk read 404 as *"he lost the screen"* — **`WALK RED 36/37`, on a screen this kit never touched.**
The install stopped at the walk, correctly, and nothing was restarted.

The lesson is the section's own: **a check you cannot run is a check you cannot trust.** The three
gates that could run offline were exact — the box read the predicted pin `3296eca0…` to the
character — and the one section that could not run offline was the one that shipped a guess. The
paths and signatures are now taken from `walk_amir_access_s221.py`, which exercises them daily,
and every §8 line prints its path and status code so a future failure names itself.

## Files

| file | what it is |
|---|---|
| `patch_desk_users_s222.py` | the patcher. Anchor A (the gate) is **required**; anchor B (the stale sentence) is **optional** — a comment is not behaviour, so a reworded docstring does not block the fix, and the patcher says which it applied |
| `seed_desk_users_s222.py` | the one row. **Never overwrites** an existing one |
| `walk_desk_users_s222.py` | the live-shape walk. Runs on a **copy** |
| `selftest_desk_users_s222.py` | the offline truth table |
| `EVIDENCE_*.txt` | what those three actually printed |

Rolling back is the `.bak_S222_deskusers_*` file beside `returns_desk.py`, and a restart.
