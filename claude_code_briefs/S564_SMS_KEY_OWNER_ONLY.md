# S564_SMS_KEY_OWNER_ONLY — brief for the build runner (Agent SDK, the API credits)

*Written 15-Oct-2026 ~16:45 IST by the parent (session 317). Kit **S564** is claimed on the board `_numbers` (v436) with its PLANNED line. Run by `D:\Downloads\_kbtools\agent_build\run_build.py S564_SMS_KEY_OWNER_ONLY`. Read `BUILD_NORM_v1.md` and `CLAUDE.md` first; they bind. A small kit: keep it small.*

## 0 · For the owner (2 plain lines on top of the report)
The phone's secret key on the bank-SMS page is now shown to your login only. Shavez, Dr Bhawna and any other login that can open the page no longer see it; the rest of the page is unchanged.

## 1 · The owner's word
- 15-Oct 16:35 IST: *"for the phone's key part also give a line to paste in for the Claude API … using the Claude API credits only."*
- The finding (REPORT_S562, "Outside the brief"): the ledger page's *Phone setup — MacroDroid* fold prints the phone's door key (`/root/finance/bank_sms.key`) to every login the page admits — the clinic and medical checkers — not only the owner.

## 2 · What was read
- `/root/finance/bank_sms.py` — `page()` admits `_require("checker", unit="medical")` or `unit="clinic"`; near its end, `key = _key()` and the `<details class="card"><summary><b>Phone setup — MacroDroid</b> …` block prints `_esc(key)`.
- `/root/finance/bank_standin.py` — `is_owner(con, u)` / `owner_login(con)` (setting `bank_standin.owner`, default `manoj`). S562 already uses it on this page for the switch and the difference column; use the same test.

## 3 · Pins — read each live file, check its md5 = the pin, a different byte = STOP that file and report
- Edited: `/root/finance/bank_sms.py` `053d4ccb85d64403daf9918a0ba6f46c` (S562's TO).
- Read only, unchanged at install: `/root/finance/bank_standin.py` `fd635862c75e1ab44f770a6ffd79511a`.

## 4 · The change
- In `page()`: draw the *Phone setup — MacroDroid* fold (and call `_key()` at all) **only when the login is the owner** (`bank_standin.is_owner(con, u)`, fail-soft: if it cannot be read, treat as NOT the owner). For anyone else the fold is simply absent — no placeholder, no hint that a key exists.
- The fold's own text: correct its step 4 to what the phone really sends today (the owner's macro, as he set it on 15-Oct): the SMS in a query parameter, plus a field named `from` carrying the SMS number. Keep the S439 note that the door reads any of its listed field names. No other wording changes.
- Nothing else on the page or in the door (`POST /finance/api/bank-sms`) changes. The key file is not touched or rotated.

## 5 · Walk — a made-up root, a made-up key file
- **(a)** as `manoj`: the fold and the key are present; the rest of the page is byte-for-byte the old file's except the fold's step-4 text.
- **(b)** as a clinic checker and as a medical checker (made-up logins with those roles): the page renders 200, contains no fold, no key text, no `bank_sms.key` path; otherwise identical to the old page for that login with the fold removed.
- **(c)** a login the page refuses is still refused (403), as today.
- **(d)** the door: a POST with the right key → 200 stored; wrong key → 401 — unchanged.
- **(e)** `is_owner` raising → no fold for anyone but the page still renders.
- **Negative control:** the old file shows the key to a checker ((b) red).
- Installer: gates → pin → compile (both pythons) → counted anchored edits on the live bytes (`make_s564.py`, in memory first) → walk + control → backup `.bak_S564_053d4ccb` → place → read-back md5 → restart only the service that serves `/finance/bank-sms` (S562 found `clinic-finance`) → `/finance/healthz` 200 → look as `manoj`. Rehearsed on a made-up root. `SUMS.md5`; no `.json` in the kit. Number gate: `python3 -B deploy_kits/NO_PHONE_NUMBERS.py --files-from <list> <repo>`. Hold the server build lock per `CLAUDE.md`.
- **Housekeeping:** remove S562's scratch `/tmp/s562kit` and `/tmp/s562probe` after checking each holds no secret and no number. Use a command the permission list allows (one folder per command; if `rm -rf` is refused, try `find <dir> -delete`); if still refused, say so in the report.

## 6 · Install, publish, report
- Install, then look at the page as `manoj` (fold present) — report the look as counts/yes-no only; **never print the key**.
- Publish with `D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat` (CLAUDE.md).
- Write `claude_code_briefs/REPORT_S564.md`: the 2 plain lines (§0), then pins FROM → TO with full md5s, walk counts, the control's red count, the service restarted, the one undo line, the cost, and any decision made where this brief is silent.

**NEVER:** print, log or report the key or any SMS text; rotate or rewrite the key file; change the door; touch any other file.
