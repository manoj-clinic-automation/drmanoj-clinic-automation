# S722_ALARMS_REACH_OWNER — the alarms reach you

*Sanjeevni session 393 · 06-Nov-2026 · F-1134 · the owner's word 14:22 IST "alarms first"; the wording approved 14:34 IST ("Ok").*

## For the owner
Your **clinic app** now carries every alarm about the Marg reports. Before, the morning-report alarms went only to the old ntfy topic.
- **Morning reports** — the 10:00 *not in* / *wrong twice* / *the reader could not read it* alarms come to the clinic app. The words are the same, e.g. *"Sanjeevni · Morning reports 05-11 — Closing stock of 05-11 has not come by 10:00. The sale report is right."* ntfy is used only when no device of your login has allowed the app.
- **Medical PC offline** — after 20 minutes of silence from the medical PC between 09:00 and 20:00 (Sunday 09:00–14:00); a PC not heard at all that day is said at 11:00 (it is usually switched on between 09:15 and 10:50): *"Nothing from the medical PC since 05-11 20:29. Reports made on it now wait there until it is back. Check that it is switched on and its internet works."* Once per silence.
- **Medical PC back ✓** — once what was waiting on it has arrived: *"Back at 11:49 after 15 h 20 min. 2 reports delivered since: Sale report, Closing stock."*

Tapping a message opens your command console. The install sends you **one test message** by the new road.

## How the server knows the medical PC is there
Until now the server heard from the medical PC only when a report was sent, so a quiet PC and a dead network looked the same. Now the medical PC's sender (`marg_push.py`, a thread inside the watcher) asks the server *"are you there?"* **every 5 minutes**, adding one header: `X-Marg-Beat: MEDICAL waiting=<n>`. The header carries no file, no content and no new key. The Marg door writes the time, the waiting count and the first beat after a gap to `/root/marg_ingest/medical_seen.json`. **Only a beat writes it** — a pushed file never does, so the PC's present sender cannot start the messages. `owner_notice.py` (the five-minute tick) reads that note. **Nothing is said about the medical PC before its first beat**, so the server half can go live first, harmlessly. The medical PC's off switch (`D:\SendToClinic\_off\ALL_OFF.txt` or `MARG_PUSH_OFF.txt`) stops the beat too.

## What changes — five files, two machines (`make_s722.py`: every anchor exactly once, every FROM pin exact, else REFUSED)
| file | FROM → TO | what |
|---|---|---|
| `/root/finance/owner_notice.py` | `ca5cd443` → `7adbfc24` | `_part_medical`: *Medical PC offline* (key `medical_off:<last beat>`) / *back* (`medical_back:<same>`); six settings `owner_notice.medical_*` (quiet 20 min, 09:00–20:00, Sunday to 14:00, not heard today → 11:00, *back* when nothing waits or 15 min after its first beat back); *delivered since* counts the PC's pushed reports, never a refusal note |
| `/root/finance/reports_watch.py` | `adbb21be` → `3b6fb83d` | `_send` goes by `owner_notice.deliver` (the clinic app; ntfy when no device); the old ntfy POST stays the fallback if owner_notice cannot be imported; the title loses its second "Sanjeevni"; the test message's words |
| `/root/finance/marg_door.py` | `dc5c1e36` → `565ad9c8` | a GET carrying `X-Marg-Beat` writes the note (a temp file per worker, then an atomic rename; the count read only as plain digits; a fault never fails a request); the answers are unchanged |
| medical `D:\SendToClinic\marg_push.py` | `566e189e` → `3f5ed144` | the beat, after each pass, every 300 s; logged only when the state changes; its selftest 13 ok |
| medical `D:\SendToClinic\marg_watch.py` | `a009d2fd` → `df7736e9` | **the start line only** (`marg_watch S679+S722 starting …`): the agent restarts the watcher only for a `marg_watch.py` change (`RESTART_FOR`), which is what loads the new sender |

`reports_tile.status`, `supplier_msg`, `porders`, `expiry_watch` are not touched; no name the parent's console reads changes meaning. The parent's `finance_app.py` is not touched (the door's path is already token-gated).

## The proof
- `walk_s722.py` — **39 of 39 green** on made-up rows (its own temp folder, stubs for the phone, never the box's ntfy conf): no beat ever → nothing; 19 / 20 minutes; overnight → 09:20 with the day named; 20:00 and night quiet; Sunday 13:00 / 14:30; the tick sends once; back not yet with 2 waiting, back after 15 minutes, back at once with nothing waiting (only pushed files, not the drive copy, not yesterday's), sent once; a new silence → a new message; back with nothing pushed; a spoiled note; the switch; the report alarm through owner_notice's road, its title, stamped sent; the fallback when owner_notice cannot be imported; a walk's push stub; no message from a database that is not the live one; not heard today → nothing at 09:30 / 10:59, said at 11:00 (a beat after midnight or before 09:00 is not "today"); a count stuck above 0 → back after 15 minutes saying what still waits; a refusal note never counted as delivered; the door: a wrong key, a plain GET with no beat, the beat with its count, the first beat kept across beats, a non-ASCII count (200, no count), another sender's file and **a MEDICAL__ push write no note**, the count read only as digits. **Control on the live files: 22 red (21 of them S722 checks).**
- **The proof on real data** (`proof_s722.py`, read only): on the 05-Nov database copy in the device VM, what owner_notice would say at every hour 08:00–23:00 of 02-Nov … 06-Nov, by the live file and the rebuilt one — **CLEAN, 80 moments, old = new (83 message lines)**; the database's md5 unchanged by the read. The installer runs it again on the box's own database.
- The medical pair: `marg_watch.py --selftest` **72 OK, 0 FAIL, old and new identical** (beside `marg_txt.py` aa7baee5); `marg_push.py --selftest` 13 ok.
- **An independent cold review** found one BLOCKER, fixed: a MEDICAL__ push wrote the note, so the PC's present sender would have started *offline / back* several times a day before the medical half was placed — now only a beat writes it. Also fixed from it: *back* with a stuck waiting count; *delivered since* counted refusal notes; a non-ASCII digit could fail a beat request; one temp name shared by the workers; the proof's new side now the live folder by links (not a partial copy); the morning (not heard today → 11:00, from the agent's start times 09:16–10:51). A second cold review: SAFE; its three lesser points fixed (a beat after midnight or before 09:00 counted as "today"; the wording with a stuck count). Left as named below: the switch reads as silence.
- Rehearsed on a made-up root: DRY · install · ALREADY INSTALLED · a forced red at [7/8] (three files back) · a changed live file refused at [2/8] · **F-1135**: the stopping master's `--- Logging error --- / reentrant call` lines are left out (its PID taken before the restart), a new worker's Traceback still restores. The lock released every time.

## Install
**Server** (your one line, after the publish):
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s722kit && cp -rp /root/deploy/repo/deploy_kits/S722_ALARMS_REACH_OWNER /tmp/s722kit && bash /tmp/s722kit/install_S722_ALARMS_REACH_OWNER.sh
```
**Medical PC** (the chat, through the file tools, F-764): Drive `ToMedical\_kit`: the two FROM files read first and kept beside as `marg_push_S259.py.superseded` / `marg_watch_S679.py.superseded`; the two files and their two `KIT_MANIFEST.txt` md5s (CRLF) placed and read back. The agent installs at its next kit check and restarts the watcher. Read on the heartbeat: `marg_watch.py df7736e9`, `marg_push.py 3f5ed144`; in the log *"marg_watch S679+S722 starting"* and *"beat: the server answers"*; on the server, `/root/marg_ingest/medical_seen.json` dated within 5 minutes.

## Undo
Server: the installer prints the one line (the three `*.bak_S722_*` back, finance restarted). Medical PC: the two `.superseded` files back as `_kit\marg_push.py` / `marg_watch.py`, the manifest's two lines back to 566e189e / a009d2fd.

## Named, not done
- `export_watch.py --notify` (10:45 next day, a red Amir day) still uses ntfy and runs under the system python. Its news already reaches the app the evening before, as owner_notice's *Amir's work — not complete* (23:40).
- The parent's health page (`freshness.py --shout`, the *Medical PC capture / reachable* lines) is the parent's. Its legs are not moved here; *Medical PC offline* now covers the medical PC.
- The message cannot tell "switched off" from "no internet" — or from the medical PC's own off switch (`ALL_OFF.txt` / `MARG_PUSH_OFF.txt`), which stops the beat too. The server only sees that the beat stopped.
- The beat's "are you there?" can hold the next push pass by up to 30 s when the network is bad (capture is a separate thread and never waits).
