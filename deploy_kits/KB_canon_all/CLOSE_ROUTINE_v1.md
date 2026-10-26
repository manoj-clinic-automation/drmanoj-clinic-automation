# CLOSE ROUTINE — v1 — one close for every project (adopted at S357, 26-Oct-2026; the owner's word of 07:19 IST: "your session close takes lot of time, check and optimise it as much as safely possible")

**Supersedes `END_OF_SESSION_PROMPT_v18` as the routine.** v18's RULES stand whole and are not repeated here — A0 (evidence), A0.3 (the numbers), the Archive's and the Fault Register's append-and-prove, the Register's four lines, the manifest's four surfaces, the pin list, `MD5SUMS_ALL.txt`, the brief in three places, `OWNER_TODO_LIVE`, the publish gates, A10c (the board's one batch), A11c (kits built outside the publish folder), **A17 — the close report in which silence is never DONE**. What changes is HOW: the facts are written ONCE, as parts, and one tool builds and verifies every document and does every mechanical step.

**Why it was slow.** Eight documents were written as prose every close, each restating the same facts; every append, prefix proof, manifest row, pin list, sums rewrite, copy and hash was done by hand and re-checked by hand. 25–40 minutes, most of it the same work. The S352 close (the Scan App chat) proved the alternative on one close; this makes it the routine.

---

## 1 · Numbers first

D, F and A-D numbers from `board/_numbers` by a pinned write BEFORE the first part is written (F-920); the kit numbers were taken when the kits were built. Read the other chats' newest lines: a CLOSING without READY means canon is moving — wait.

## 2 · The parts — the session's prose, written once

Folder: `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S###\close_parts\`. LF, UTF-8. Each part is only what is NEW this session:

| part | what it is | budget |
|---|---|---|
| `archive.md` | the Archive's `## §S### CLOSE` section — what happened, in order, with the figures measured | ≤ 60 lines |
| `fault.md` | the Fault Register's `## §7.### — S### CLOSE` section — F minted / closed / open, F-513 (pending), the drift and dead counts, "next free" mirror | ≤ 40 lines |
| `reg_h1.md` | the Register's new first line (`# KB REGISTER — v5.NNN (...) — **S### CLOSE** (...)`) | 1 paragraph |
| `reg_sections.md` | `## CURRENT LIVE FILE VERSIONS — §S### CLOSE (...)` — the pin table (every `/root` file this close changed, FROM → TO, CONFIRMED by which bundle or DECLARED-PENDING), the kit gates (`{{S###SUMS}}` is filled by the tool), the D and F lines, the changelog line | the table |
| `rb_section.md` | this project's Runbook section, whole (§2A / §2B / §2C / NK), rewritten — the backlog in order | ≤ 80 lines |
| `start_here.md` | the next session's entry point for this project | ≤ 130 lines |
| `brief.md` | the owner's one paper — plain language, what changed for him, what waits on him | ≤ 40 lines |
| `close_report.md` | A17's table — rows 0–16, one line each; the tool appends its build log | the table |
| `todo.md` | this project's `OWNER_TODO_LIVE` sections: ⭐0 (his, only what is open and only what is his), ⭐1 (mine), ✅ DONE AT THIS CLOSE | as needed |
| `man_narr.md` | the manifest's narrative blockquote for this close (`> **S### CLOSE (...)**` + the Decisions / Faults / Kits / Files lines) | ≤ 8 lines |
| `book.md` | (Sanjeevni, Scan App) the Book's new section, when the app changed | as needed |

And `close.json` beside them — the facts the tool needs (session, project, the section markers, the new How-to-use line, END lines, STATUS line, the manifest rows' descriptions, kits, extra canon files, supersedes). The tool's docstring is the schema; copy the previous close's `close.json` and change what changed.

**One fact, one place.** A figure appears in the part that owns it and is referred to from the others; the board line and `_claude_status` are written from `_summary.json`, not retyped.

## 3 · The build — one run

```
python D:\Downloads\_kbtools\close_build.py D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S###\close_parts\close.json
```

It reads the CURRENT names from the manifest (the manifest WINS), builds every TO file in `close_build\`, proves the Archive's and the Fault Register's prefix by hash, fills the kit SUMS, replaces each anchor exactly once (or STOPS before writing a byte into canon), generates the pin list from the new Register against the new manifest (`register_pin_verified: yes` or STOP), counts this project's DECLARED-PENDING against the newest bundle, runs the `.gitignore` test (last match wins) and the number gate exactly as `PUBLISH_ALL.bat` runs it, and prints the table. **Read the table.** Fix a STOP in the parts, re-run. Then:

```
python D:\Downloads\_kbtools\close_build.py D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S###\close_parts\close.json --place
```

Places into `KB_canon_all` (never over an existing file), reads every placed file back by hash, rewrites `MD5SUMS_ALL.txt` (`canon_sums.py --fix`), runs the gate from inside the folder, copies the papers into `03_WORKING_PAPERS\S###\` with their `MANIFEST.md5` rows, puts the brief loose on the SSD, and writes `_summary.json` (every name, md5 and size).

## 4 · The board — ONE batch

As A10c: `_numbers` (the close line — from `_summary.json` — and the claims), `_page` (this project's `yours[]` / `tell[]` / `told[]`, every waiting note and message answered, pinned to the version read), `_claude_status` (this project's keys overwritten), the messages marked read. Weigh `_numbers` and `_claude_status` (F-703): trim the claims to the last 40 before ~200 KB, the whole document archived byte-exact first.

## 5 · Project knowledge — by file, never by content

Stage the placed files from `03_WORKING_PAPERS\S###\` into the cloud workspace and write each with `project_write(local_path=...)`: the entry point, the brief, the close report, the Runbook, the pin list, `OWNER_TODO_LIVE.md` (and the Book). No document's text passes through the chat. Then the tranche: the superseded copies of the same families out of project knowledge — their survivors are in canon, proven by the gate the tool just ran. The measure (`project_info`) is the OPEN's, once a day (OPEN_ROUTINE_v1 §3), not the close's.

## 6 · The publish — named, not asked

```
D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat
```

One line to the owner: the file, the machine, and that nothing follows it (or the one server line that does). The next open verifies it landed (`day_open.py`).

## 7 · EOS-light

The same routine with fewer parts (no `reg_sections.md` pin table beyond the documents themselves, no kits). The tool does not care.

---

**Retired here, with v18's blessing (it had already moved them to the open):** the Notion session log · the Drive upload of Tier-0 files · the per-close canon snapshot folder · the close's own re-run of the nightly's checks. **Not retired, ever:** a hash for every byte placed; the prefix proof; the gate from inside the folder; one board batch; the brief for the owner in three places; A17 with silence never DONE.

**Standard across the four projects.** Each project's `close.json` differs only in its markers (the Runbook section, the `OWNER_TODO_LIVE` section, the Book) and its pending prefixes (`/root/finance`, `/root/portal`, `/root/staff_register`, `/root/wa` the parent · `/root/finance` and `/root/marg_ingest` Sanjeevni · `/root/assetapp`, `/root/shared` the Scan App · `/root/labdata`, `/root/finance/lab_door.py` NK Pathology). The first `close.json` of each project is written by that project's next close from the parent's S357 one.

*CLOSE_ROUTINE_v1 · S357 · 26-Oct-2026 · lineage: END_OF_SESSION_PROMPT v18 (S297) ← v17 (S294) ← … ← v4 (D247). The next version is written when the routine changes, by whichever project changes it.*
