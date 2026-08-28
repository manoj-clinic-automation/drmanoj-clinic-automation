# S207_JOINER — adding a person, and removing one

**Staged, not installed.** Two lines in `finance_app.py` when you want it.

## Why it is a register and not a checklist

Adding a person touches four places — the roster sheet, the portal, their scope, and the biometric
device — done by different people on different days, and **the biometric is routinely last because
it needs the person physically present.**

A paper checklist handles that badly. It reaches *"biometric pending"*, the person starts working,
and the last line is never ticked. The roster row keeps no Emp Code, `build_staff_master.py` skips
it forever, and **attendance quietly does not cover somebody who has been at the counter for a
month.** Nothing breaks. A person is simply not there.

## The order, and where it came from

Read out of the code that already runs, not invented:

| observed in | what it means for the order |
|---|---|
| `build_staff_master.py` skips a row with no Emp Code — *"not on the biometric device (salary-only)"* | a person without one never reaches `staff_master.csv`; correct while pending, a hole if unchased |
| `staff_register.staff_for_user` matches `staff.username` first, then an **unambiguous first name** | with no username set, two people sharing a first name give **None** — no self page, no error |
| `build_staff_master.py` refuses rows whose `sunday_group` is not A/B/C/ARJ or `minutes_exempt` not Y/N | one blank cell stops the whole rebuild |

So: **the roster row is the anchor and is created first**, the username is written onto it
**explicitly** rather than left to the fallback, and the Emp Code goes into **that same row** when
the biometric is finally captured — never a new row, which would make one person two.

```
DECIDED -> ROSTER_ROW -> PORTAL_USER -> LINK_USERNAME -> SCOPE_SET
        -> FIRST_LOGIN -> BIOMETRIC -> STAFF_MASTER
```

**Only `BIOMETRIC` may lag.** It stays on the pending list and is named after 14 days.

### "May lag" is not "may be skipped"

A real bug, caught by the selftest before this shipped: marking `BIOMETRIC` late-ok let
`STAFF_MASTER` be signed off while the Emp Code was still missing — **which is precisely the hole
this register exists to close.** `HARD_REQUIRES` now states that `STAFF_MASTER` cannot be true
without `BIOMETRIC`, whatever the ordering rule says.

## What the register refuses, and why it says so in words

- **A step before its prerequisite** — and the refusal names the missing step and what breaks.
- **`PORTAL_USER` without the username recorded** — it is what the next step writes onto the row.
- **`BIOMETRIC` without the Emp Code** — *"without it the roster row stays invisible to the staff master."*
- **A second open record for the same person** — it names the first one instead.
- **Any step with nobody named against it.**

## Leavers

The same register reversed, because the failure is the same shape: **a login that still works after
somebody has gone is the same missed tick as a biometric never captured.**

```
DECIDED -> PORTAL_DISABLED -> BIOMETRIC_REMOVED -> ROSTER_INACTIVE
        -> DUES_SETTLED -> ITEMS_RETURNED -> STAFF_MASTER
```

**Pravesh leaves on 31 August** — three days. First run of the exit side.

## Install

```python
import joiner_app
joiner_app.init(app, get_db, require)
```

Copy `joiner_app.py` and `joiner_schema.sql` beside `finance_app.py`, add the two lines, restart.
The schema builds itself and is safe to run twice.

## Selftest

```
python selftest_joiner_app.py     42 checks, 0 failed
```

Drives a real Flask app with a real sqlite file through the real auth gate, including proving a
caller with no role and a caller with the wrong role are both refused.

**No contact number is stored here (F-185).** Numbers live in the config store beside the archive.

---

# S207.2 — the owner's flow, 28-Aug

## Six steps, because two failure points were engineered away

```
DECIDED -> ACCOUNT_CREATED -> CREDENTIALS_SENT -> FIRST_LOGIN -> BIOMETRIC -> STAFF_MASTER
```

- **`LINK_USERNAME` is gone.** The username is **derived** from the first name, so the portal login
  and the roster row cannot diverge. There is nothing to copy across and therefore nothing to
  forget. This was the step most likely to be skipped and the one that failed most quietly.
- **`SCOPE_SET` is gone as a step.** Authorities are **ticked at `DECIDED`** and applied with the
  account. They stay editable afterwards.

## The login

`amir` / `amir1234` — first name lower case, plus 1234. Handed back the moment the record opens, so
nobody types it. **Two people with the same first name are warned about before the account is
made**, naming who already has it.

**The password is derived, never stored.** Nothing in the database holds it, and
`/api/message` composes the WhatsApp on demand:

```
Namaste Amir,
Aapka clinic portal login ban gaya hai.
Link : https://followup.dr-manoj.in/portal
User : amir
Password : amir1234
Pehli baar login karke password badal lijiye.
```

⚠ **One caution, once.** With the username convention public and the password derived from it,
anyone who knows a staff first name can guess a login. The record returns
`force_change_at_first_login: true` — **enforcing that on the portal is the cheap fix**, and it
keeps the convention exactly as you want it.

## 🔴 EMPLOYEE CODES — the answer to "this stumped me"

**A code must never be reissued, and nothing in the system currently remembers that one was used.**

`punches.csv` is append-only and keyed on `(user_id, datetime)`. It holds **every punch ever taken,
including people who left years ago.** The name behind a `user_id` lives only in `staff_master.csv`,
which is rebuilt from the roster sheet and contains **only rows that still have an Emp Code — every
one written `active="Y"`.** There is no inactive state anywhere.

So when somebody leaves and their roster row goes, **their punches stay under a code with no name.**
Reissue that code and every historical punch under it becomes the new person's — in attendance, in
the month report, in salary — **with no error and no trace.** The ONtime-era codes that outlived
their staff are exactly this case.

**The rule: one above the highest ever seen. Never fill a gap** — a gap is somebody's code, and
their punches are still under it.

`emp_code` is the register that remembers. It **never deletes a row**; a leaver's code is marked
`retired_on` and can never be issued again. `/api/next_code` suggests the next one and says why;
`/api/seed_codes` loads the codes already in use.

### Do this once, before anybody else is enrolled

Seed the register from the roster **and from `punches.csv`** — the latter is the only place a
departed person's code survives:

```
sort -t, -k1,1n -u /root/punches.csv | cut -d, -f1 | sort -n -u | tail -5
```

Until those are on the register, "the next code" is a guess, and a guess that lands on a departed
person's number silently rewrites their history.

## Amir, as recorded

Biweekly part-time · role purchase · authorities: purchase orders, purchase bill entry, salt
corrections, own attendance. Login `amir` / `amir1234`. Biometric on his next visit, code allocated
from the register.

**48 checks, 0 failed.**

---

# S207.3 — passwords the simplest way, and the code baked into the flow

## Forgotten passwords: one button, on the owner's page

**Staff never manage a password.** They say they are stuck, the owner presses reset, it goes back
to first-name-plus-1234 and the page shows what to read out. `POST /api/reset_password` returns the
username, the password and a ready line to send. **Nothing is stored** — not the password, not a
token, nothing to expire.

**Not an OTP to their mobile**, which was the other idea. It reads simpler than it is: it must be
wired and paid for, and it then fails in exactly the moments somebody is already stuck — no
balance, no signal, phone at home, number changed and nobody updated it. Every one of those becomes
a call to the same person who would have pressed reset. **A button that always works beats a
message that usually does.**

`GET /api/resets` counts repeats, because **somebody resetting every week means the flow is
confusing them**, not that they are careless.

**What bounds the damage** is not password strength — it is scope. Salary stays doctor-only (F-31),
a staff login sees its own tiles and its own attendance without money, and every reset is on the
record with who did it and why.

## The employee code, baked in

`GET /api/next_code` gives the number, and **the onboarding page shows it beside the person** so
nobody works it out standing at the device. A used code is refused with what would have happened,
and the right one offered.

### `seed_codes_from_vps.py` — run once, on the VPS, before anybody else is enrolled

```
/root/wa/venv/bin/python3 seed_codes_from_vps.py --dry     # prints, sends nothing
/root/wa/venv/bin/python3 seed_codes_from_vps.py
```

Reads `punches.csv` **and** `staff_master.csv`. The roster only holds people still here;
**`punches.csv` is the only place a departed person's code survives**, and those are precisely the
codes that must never come back. Ghost codes are registered as
`(left -- name not recorded)` and marked retired — we cannot recover who they were and do not need
to. What matters is that the number is spoken for, permanently.

**The worked example, and it is the whole argument.** Roster holds 11, 12, 27. `punches.csv` also
carries 19 and 33 from people long gone.

| seeded from | next code | what happens |
|---|---|---|
| the roster alone | **13** | marches straight into 19, then 33 — each one silently inheriting somebody's old attendance |
| roster **+ punches** | **34** | every ghost cleared |

*(Tested with exactly these numbers — `selftest_joiner_app.py` §11.)*

## Checking it landed

`GET /api/staff_master` renders the file as it stands, plus **which codes are not yet on the
register** and a warning when any are. ⚠ **Owner-gated.** `staff_master.csv` carries base salaries
and F-31 says salary is doctor-only — the route withholds the salary column even from the owner,
so that opening it wider later cannot leak one.

**65 checks, 0 failed.**
