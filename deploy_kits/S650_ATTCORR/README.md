# S650_ATTCORR — the month-end attendance correction flow (kit S650, session S354, 25-Oct-2026)

**Why.** D786, the owner, 25-Oct-2026 07:19 → 08:40 IST, ruled on the mock-up `https://claude.ai/artifact/8gg5NKJThNmSMJXPgeUNHM`
(rev 2 + the fallback): *"At the month end, there is a discrepancy between the punches recorded and the actual attendance of the
staff … automating and delegating this task to the reception staff … I only need to check them and verify those corrections."* ·
*"include sundays · present, absent, leave · no time … no reason · shavez does the remaining final corrections · a simple flow
for me, I shd be able to do any further edits … a save button with a on screen saved is a must everywhere"* · *"available for
Shavez and myself also as a fallback"*. To be live before 1-Nov.

**What it does.**
1. From the 1st, reception's *Aaj ka kaam* opens the **Attendance correction sheet** (A4): one block per staff member, every day of
   the month just ended with no machine punch, Sundays included; *Date · Day · Present · Leave · Absent*; a signature under each
   block; reception, Shavez and Dr Manoj at the foot. No reason column, no in-time.
2. Each staff member ticks and signs on paper.
3. Reception enters the ticks (one tap per day, *Sheet par … ka sign hai* per person) and **Saves** → *✓ Saved — date · time · N din*.
   Shavez and the owner have the same screen as a fallback.
4. Shavez's line appears; he corrects against the signed sheet and **Saves**. Nothing goes back. His own days are the owner's.
5. The owner's console says *Attendance correction: October ready — approve & save*; his page (English) lets him change any day;
   **Approve & save** writes the month.

**Nothing counts until Approve & save.** The ticks live in `attcorr_day / attcorr_sign / attcorr_month`. Approval writes the records
the register already has — so no salary reader changes:
- **Present** → an already-approved `present_request` in the D338 shape, in-time = the duty start (no late mark).
- **Leave** → the day grid's own sanctioned-leave row (`daily_register`, as `save_maker` writes it; *festival* on a listed festival).
- **Absent** → nothing new; a leave the grid held for that day becomes *absent*.
- On an **off-duty Sunday** nothing is written for Leave/Absent (the salary never reads off days, and a leave row there would add a
  charged day — found by the whole-file read of the three register files this session). "Off" is decided by the SALARY's roster
  (`att_month_report.duty_shift`), not the register's own.
- A changed tick after approval is undone and rewritten at the next Approve & save (each write keeps what it replaced).

**The salary lock waits** (from October 2026): `/register/salary/lock` refuses while the month has listed days and they are not
approved, or changed after approval. The view is wrapped, not edited. A locked month cannot be changed here.

**The manual way stays**: the Step 0 sheet, the fix-absents desk, the day page's D338 door — untouched. A day corrected there is not
listed here.

## Files
| live path | from → to | |
|---|---|---|
| `/root/staff_register/att_correction.py` | NEW `448de63a` | the module |
| `/root/staff_register/staff_register.py` | `0a098cfa` → `7e92bc20` | 1 counted edit: the hook before `__main__` |
| `/root/finance/aaj_duties.json` | `1c49af35` → `90219853` | 1 counted edit: 3 fetch lines (`aaj_duties.json.kit`) |
| `/root/finance/aaj_seed.py` | `98f63364` → `64d9a607` | 2 counted edits: reception's 2 lines, Shavez's 1 |
| `/root/finance/owner_console.py` | `a6315bfd` → `e414e7ad` | 1 counted edit: the console line |

Built by `make_s650.py` from the pinned live bytes (the 25-Oct bundle; `aaj_seed.py` from S647's kit = the live pin).

## Proven
- `walk_s650.py` **43 of 43** on made-up staff (five invented people, an invented October): the day list (Sundays, the holiday,
  a D338 day left out, the salary's roster), the sheet, the three screens and their Saves, nothing counting before approval,
  Approve & save writing present requests and leave rows exactly as the register's own readers and the salary engine read them,
  re-approval undoing and rewriting, the lock waiting (and its own button refusing), a locked month, an unreadable punch feed,
  who may open what, the lines' door. `--old` on the live register: **36 S650 red · 0 older red · 7 green**.
- `walk_s650_lists.py` **8 of 8** on the 25-Oct finance database copy (read-only): the three lines are fetch lines on the
  register's door in the first sections, no unread line, every other line of every list unchanged; the console line before /
  after reception saves / after approval (made-up register). `--old`: **4 S650 red · 0 older red · 4 green**.

## Install (on the server)
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s650kit && cp -rp /root/deploy/repo/deploy_kits/S650_ATTCORR /tmp/s650kit && bash /tmp/s650kit/install_S650_ATTCORR.sh
```
## Undo
```
\cp -p /root/staff_register/staff_register.py.bak_S650 /root/staff_register/staff_register.py; \cp -p /root/finance/aaj_duties.json.bak_S650 /root/finance/aaj_duties.json; \cp -p /root/finance/aaj_seed.py.bak_S650 /root/finance/aaj_seed.py; \cp -p /root/finance/owner_console.py.bak_S650 /root/finance/owner_console.py; mv /root/staff_register/att_correction.py /root/staff_register/att_correction.py.removed_S650; systemctl restart staff-register clinic-finance
```
