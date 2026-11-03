# S702_OWNER_REPORT_NOTICES — you are told when the Marg work is done

*Sanjeevni session 380 · 03-Nov-2026 · the owner's word 10:10 IST "build it now", on the plan of 10:04–10:08 (his rulings: Shavez's pair as soon as it is done; Amir's visit when he does it; Darpan's order sheet the same; Sundays not silent).*

## For the owner
Your clinic app (and ntfy, while no device of your login has allowed the app) now tells you, once each, every day of the week:
- **Morning reports ✓** — the moment Shavez's (or Shivani's) sale report and closing stock are both in and checked.
- **Stock Valuation ✓** — 1st to 7th; if it is not in, one reminder each evening at 20:00.
- **Amir's work ✓** — when his item-wise, bill-wise and Batch Stock are all in, with the batch fixes done and left; at 23:40 on a day he punched in, what is still missing.
- **Darpan's order sheet ✓** — every sheet taken (suppliers, medicines), or refused with the reason.
- **Your three lists** — at 09:00, two days before each is due and on the due day; and **"Salt list received ✓ — 412 items"** within about five minutes of your export (or refused / failed, with the reason).
- **Reception phone silent** — when it has not asked the server for an hour inside 09:00–20:00 (Sunday 09:00–14:00), once per silence; **refused** when it asks and is turned away (F-1089).
- **A list overdue** — on the install's day and then once a week until it comes.

Also: the morning alarms (a report wrong twice, or not right by 10:00) now run on **Sundays**; a **Monday asks for Sunday's own** sale report and closing (the counter sold on 20-Sep, 18-Oct, 25-Oct; on 12-Oct and 02-Nov Sunday's was never exported); **Stock Expiry** leaves Shavez's month rows (F-1090); the order page's greyed WhatsApp button now says **why** ("silent since 02-11 20:18 — unlock it, screen on, mobile data on").
Tapping a message opens your command console. Nothing that happened before the install is announced.

## What changes — four files and one cron line
| file | from → to | what |
|---|---|---|
| `/root/finance/reports_tile.py` | `03902a5d` → `0598072c` | `_due_day` = yesterday, every day; Stock Expiry out of `_month_rows`; its selftest |
| `/root/finance/reports_watch.py` | `428c389c` → `adbb21be` | the two Sunday-quiet returns out; its selftest |
| `/root/finance/porders_s454.py` | `438714b8` → `5de2a4b8` | `_s702_waoff` — the disabled WhatsApp line, and the WhatsApp confirm screen, say why |
| `/root/finance/owner_notice.py` | new → `2bc96912` | the messages (table `owner_notice`, 11 settings `owner_notice.*`) |
| crontab | + 1 line | `*/5 * * * * … owner_notice.py tick` (the venv python) |

`make_s702.py` builds the three changed files from the box's own bytes by anchored edits (each anchor exactly once, the FROM pin exact, else REFUSED). The parent's `/root/portal/ring_common.py` (Web Push) is only called, never changed. `reports_tile.status` keeps its meaning for the parent's console (its Stock Expiry row was already filtered there).

## The proof
- `walk_s702.py`: **46 of 46 green** on made-up rows (2099, own scratch database, a stub instead of a phone): the since gate; the pair (and not with one report); Monday → Sunday, Sunday → Saturday; a Sunday alarm; the valuation reminder and tick; Amir missing at 23:40 and complete with the fixes; the order sheet taken / not yet / refused; the list reminders before and at 09:00, on the due day, not before it is read, read with its count, refused; the phone at 09:59 / 10:00 / Sunday 14:30 / 20:05; the button's three wordings and the confirm screen; a refused phone; today's pair exported at 22:40 said that evening; an overdue list a week later and not between; the ntfy title plain ASCII; one tick at a time; once per key; no message from a database that is not the live one; the switch file; fail-soft. **Control on the live files: 32 S702 check(s) red · 14 green.**
- **The proof on a copy of the database (the 03-Nov copy in the device VM), old against new, the last 36 days:** CLEAN — 26 weekdays identical (rows and alarms), 5 Mondays moved to Sunday, 8 days without the Stock Expiry row, 5 Sundays now told; nothing else differs. The installer re-runs it on the box's own copy.
- On the real data (the VM copy): 01-Nov 10:30 *Morning reports ✓ 31-10, in by 09:43*; 29-Oct 23:45 *Amir — not in: Batch Stock* (before S690 he was not asked); 31-Oct *Darpan's order sheet ✓ 14 suppliers, 38 medicines*; 31-Oct *salt list due today*; 02-Nov 20:30 *Stock Valuation not in yet* (true — November's has not come).
- Both files' own selftests on the rebuilt files: reports_tile 54 checks, 0 failures; reports_watch 0 failures.
- Rehearsed on a made-up root (the VM): DRY · install · ALREADY INSTALLED · a forced red at [7/8] restores (three files back, the new one moved aside, no cron line) · a changed live file refused at [2/8]; the lock released every time.
- **An independent cold review** (built from the live bytes, `collect` run on the copy) found one BLOCKER, fixed: a title with "✓" or "—" raised in the ntfy header, so every ntfy message would have been given up — titles now go as plain ASCII, the body stays as written. Also fixed from it: the installer's test pattern; one tick at a time (a lock); an evening export said that evening, not at midnight; a refused phone said (not taken for alive); an overdue list said on the install's day and weekly; the WhatsApp confirm screen's line; one commit per part (no write lock held across a tick); `since` reset on every install. Left as named below: Shavez's page shows no banner on a Sunday.

## Install (the server)
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s702kit && cp -rp /root/deploy/repo/deploy_kits/S702_OWNER_REPORT_NOTICES /tmp/s702kit && bash /tmp/s702kit/install_S702_OWNER_REPORT_NOTICES.sh
```
At [8/8] it sends you **one test message** ("Messages are on ✓") and says whether it went by the clinic app or by ntfy.
**Undo:** the installer prints the one line (the three backups `*.bak_S702_*` back, `owner_notice.py` aside, the cron line out, finance restarted).

## Named, not done
- The export watch's own ntfy line at 10:45 next day for a red Amir day stays as it was (it also checks the closing stock).
- Shavez's page banner is still not shown on a Sunday (staff screen unchanged).
- The phone message cannot tell "locked" from "no internet" — the server only sees that it stopped asking.
