# S349_WATCHER_FRESHNESS — the watcher row that can go red, and the freshness table on a page

*Session 276 (parent) · 20-Sep-2026 · kit S349 claimed on the System Board before this folder was named (F-515). Both items ticked by the owner on 20-Sep-2026.*

## The one line on the VPS

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S349_WATCHER_FRESHNESS/install_S349_WATCHER_FRESHNESS.sh
```

## 1 · The watcher rule (D554 / F-547)

The health card's *Medical PC capture* row went red only when the posted status said `alive: false`. The realistic
failure — the medical PC down or unreachable in the middle of the clinic day — leaves the heartbeat file unchanged,
still saying alive, and the row said **info**: the S202 false-green shape, named at S269 as F-547 and never fixed.

Now, in the stale-heartbeat branch only: **during the clinic day → bad** ("DURING THE CLINIC DAY: the machine is down
or unreachable"); **outside it → info**, as before. The clinic day is the same two settings the pull check already
reads — `pipeline.clinic_hour_from` / `pipeline.clinic_hour_to` (defaults 9 and 21) — on the server's IST clock;
**Sunday counts as out of hours unless `pipeline.clinic_sunday` is `1`** (a setting, not code, if he wants Sundays
watched). The `alive is False` red branch, the `alive is True` ok branch and the stale-hours window setting are
untouched.

## 2 · The freshness page (F-540)

`freshness.py` writes `/root/finance/freshness.html` every morning at 08:05 — the one surface that dates every job's
last success — and nothing served it: S310's installer printed `https://followup.dr-manoj.in/finance/freshness` and
the owner got 404. `freshness_page.py` (NEW) mounts exactly that route and returns the collector's file byte-for-byte
with one line on top saying **when it was written and how old that is** (red past 30 h: the collector has not run).
Nothing is computed, run or written. Gate = the health page's own (`require("checker")` on the medical unit). The
health page's help box gains one link to it. The HTML path is resolved the way `freshness.py` does (`HTML_OUT=` in
`/root/finance/freshness.conf`, else `freshness.html` beside it); `FRESHNESS_HTML` in the environment overrides for
the walk.

## The change — one anchored patch, one new file

| file | from | to |
|---|---|---|
| `/root/finance/finance_app.py` | `7866b1ee` (S342) | read back at install; the same patch offline gives `29819879dec3f057b7690e004e4e87cb` — three edits: the `elif _hbstale:` branch, one line in the help box, one guarded mount after the S332 block |
| `/root/finance/freshness_page.py` | — | NEW `dc60a4c6fc0033bda1cc9548db1efa5d` |

**Read whole first (the drift rule).** finance_app.py stood at drift 4 after S273; before this patch it was read WHOLE
this session from its live bytes, reproduced offline from the 20-Sep 01:35 bundle through the S332 and S340 patchers
(41e0ffb4 → 3a871f53 → 7866b1ee, byte-exact = the live pin) — the WHOLE_READ paper is in the session's evidence
folder. Every anchor here was copied from that text (F-472).

## Proof

- `walk_s349.py` — **28 checks** on a copy of the live file, with the service's python: the patch applies once,
  compiles, is idempotent, changes exactly 5 lines out and the named lines in, leaves the red branch byte-identical;
  **the watcher rule lifted out of the patched text by text** (the S319 technique) and driven through a fake clock and
  fake settings — Monday 11:00 stale → bad · Monday 23:00 → info · Sunday 11:00 → info · Sunday with
  `clinic_sunday=1` → bad · hours moved to 10–13 by settings: 09:30 → info, 12:30 → bad · a 5 h heartbeat under an
  8 h window → ok · `alive False` at 23:00 → bad · fresh → ok · no watcher section → info; **negative control: the
  UNPATCHED text says info at Monday 11:00 stale** (the F-547 shape). `freshness_page`: conf parsing, env override,
  503 without the file, 200 with the banner inside `<body>`, the collector's bytes returned unchanged, stale past 30 h.
  **Live shape:** a real Flask app with the module mounted through `init()` — a checker gets 200 with the banner and
  the table, a non-checker gets 403, the route is exactly `/finance/freshness`.
- Installer rehearsed on a fake root with `systemctl`/`curl`/`journalctl` faked: install (28/28, APPLIED, module
  placed, compiles, restart, probes) · re-run (25/25 on the patched file, ALREADY on both, nothing re-placed) ·
  **forced red** (healthz 500 → finance_app.py restored byte-exact to 7866b1ee, the module removed, service
  restarted) · **wrong live bytes** (refused at --apply, nothing changed).

## After the install

The next stale heartbeat inside clinic hours turns the row red on `https://followup.dr-manoj.in/finance/health`.
The freshness table is at `https://followup.dr-manoj.in/finance/freshness` (the doctor's sign-in), and from the
health page's help box. TO RECORD AT THE CLOSE: the finance_app.py pin, the new module's pin, D554 as delivered,
F-540 and F-547 closed.
