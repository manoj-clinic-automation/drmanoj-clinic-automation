> ## ⚠ SUPERSEDED — DO NOT ACT ON THIS DOCUMENT
> **Superseded on 26-Aug-2026 — this is a route survey whose verdicts are spent.** The route was
> chosen and built; what was built is described in
> **`MARG_AND_MEDICAL_PC_MASTER_REFERENCE_v3.md` §2, the chain stage by stage**
> (md5 `579ea885e440e76af73de3ecc4542d71`).
> Its **live evidence has not been retired and must not be lost**: the dormant `up_sale` / `up_saleinfo`
> tables, `MARGDEMO`, and the `serverbackup` weekday rotation survive as **unanswered vendor asks** in
> `S180_Marg_Action_Register.md` V8/Q5 (md5 `599d315625fdf3aca11fa9aa70e6f5b3`) and
> `Marg_Report_Requirement_Sanjeevni.md` (md5 `ee3cd2549948d6437ef75480d9dadec0`) — both KEEP.
> Read this for *why a route was rejected*, never for what the system does now.
> Label added at S203, 26-Aug-2026. **Retained, not deleted (F-23).**

<!-- ── PROVENANCE NOTE — added at fold-in, NOT part of the original survey ──
     Original upload: `S181_Marg_Feed_Feasibility.md`, 21,413 bytes, md5 c2086db25b39c02e8c29bc6cf4dc634c.
     The body below is that file VERBATIM, byte-for-byte, from the "# S181 —" heading down.
     Only this comment block was prepended.

     SESSION-NUMBER CORRECTION (D188 — a filename is not provenance).
     The body's header says "Session: 181". That is wrong, and so is the label on its
     stated predecessor. Derived from the artefacts, not from the labels:
       · The last close-out was S179 (Runbook v113, 15 Aug 10:50) and it named the next
         session 180 (`START_HERE_SESSION_180`, md5 b2f89f18…).
       · `claude/S180_Marg_Folder_Recon.md` was created 15 Aug 09:15 — BEFORE that close-out —
         so it is S179 work carrying a forward-guessed S180 label.
       · The survey below (15 Aug 14:30–15:20) inherited that wrong label and called itself 181.
       · No close-out has run since S179, so no session number has been consumed past 180.
     Therefore this survey is SESSION 180 work, and is filed here as S180.
     Candidate finding for the next Fault Register append: session-numbered artefacts are being
     labelled with a forward number before the session that would carry it has opened.
     ─────────────────────────────────────────────────────────────────────── -->

# S181 — Marg Daily Sale Feed: Feasibility of Supported Export Routes

**Session:** 181 (follow-on to S180 — `claude/S180_Marg_Folder_Recon.md`)
**Date of survey:** 2026-08-15, 14:30–15:20 IST
**Machine:** Windows device `medical`, `D:\MARGERP` connected read-only via the Claude desktop device bridge
**Goal:** cheapest **supported** way to get Sanjeevni's daily sale data off this PC to the clinic

**Carried over from S180, settled, not re-surveyed:** the live Marg tables in `D:\MARGERP\Data` are Visual FoxPro DBFs behind Marg's proprietary 16-byte-prefix obfuscation. Breaking that is the last resort, not a route.

**Compliance:** read-only throughout; nothing created, renamed, moved or deleted. Files matching *licence*, *sqlconnection*, *mysqlflp*, *password* were **never opened** — only their directory metadata (name, size, mtime) is reported, which is what the ranking turns on. No patient names and no full phone numbers appear below; the one sample row is masked.

---

## 0. Verdict table

| # | Route | Verdict | One-line reason |
|---|---|---|---|
| **4** | **Export folder / daily sale XLS** | **SUPPORTED-AND-AUTOMATABLE** | The report already lands at a fixed path as a real `.xls` with exactly the right columns; only the *trigger* is manual. |
| **3b** | **Marg's own internal scheduler** | **POSSIBLE-WITH-A-SETTING** | Proven to run unattended daily (7-day rotating backup, all seven weekdays current). An empty `report\auto\` folder exists per user. |
| **3c** | **e-business cloud uploader** | **POSSIBLE-WITH-A-SETTING** | Already uploading masters every few minutes today; has dormant `up_sale` / `up_saleinfo` slots. |
| **1** | **Auto-email a daily report** | **NEEDS-MARG-SUPPORT** | Mail subsystem present but has *never* sent anything; both mail queues empty; config is encrypted and unreadable. |
| **3a** | **Windows Task Scheduler / CLI switch** | **NOT-DETERMINABLE FROM HERE** | Cannot be checked — no shell on this device bridge, and `C:\Windows\System32\Tasks` is not grantable. Command supplied below. |
| **3d** | **Tally XML export on a schedule** | **NOT-AVAILABLE** | Regenerated only when a human clicks; mtimes are irregular and months apart. |
| **2** | **MySQL / SQL sync** | **NOT-AVAILABLE as configured** | `margsqlconnection.ini` untouched since the Sept-2025 install; the live `syncdata.*` traffic belongs to the cloud uploader, not to SQL. |

**Bottom line:** the cheapest supported feed is **#4 — pick the daily sale `.xls` up off disk**, and the cheapest *upgrade* is to ask Marg to turn on their auto-report scheduler so no one has to click. Do not build a decryptor and do not stand up MySQL.

---

## 1. AUTO-EMAIL — **NEEDS-MARG-SUPPORT**

### Evidence

**Both mail directories are completely empty:**

| Path | Contents |
|---|---|
| `D:\MARGERP\emailserver\` | `{"entries":[]}` — **zero files** |
| `D:\MARGERP\emailpend\` | `{"entries":[]}` — **zero files** |

Nothing queued, nothing pending, nothing sent-and-left-behind. On a mail subsystem that had ever run, `emailpend\` would normally hold at least stale spool entries.

**No plaintext mail config exists.** Every mail-related config file carries the S180 encryption prefix `19 a3 95 78 …` and is therefore an obfuscated table, not text:

| File | Size | mtime (IST) | State |
|---|---|---|---|
| `margmail.ini` | 2,085 | 2026-05-16 | **encrypted** |
| `margmailp.ini` | 952 | 2024-12-06 | **encrypted** |
| `margsmsp.ini` | 1,033 | 2026-08-14 14:02 | **encrypted** |
| `margserb1.ini` | 5,553 | 2026-08-15 15:16 | **encrypted** (live) |
| `margmail.fpt` / `margmailp.fpt` | 1,536 / 512 | 2026-05-16 / 2025-09-30 | memo sidecars, near-empty |

`margmail.fpt` at 1,536 bytes and `margmailp.fpt` at 512 bytes (a bare FPT header) are consistent with **no message bodies ever stored**.

### The messaging subsystem *does* work — just not by email

`D:\MARGERP\margsms.txt` is **plaintext** and is a live outbound-message log:

- 28 timestamped entries, **30/06/2026 11:37:38 → 14/08/2026 14:02:46**
- Sporadic: 1–4 messages on a given day, most days none
- Sender/template ID on every line: **`MARGDEMO`** — a demo sender, i.e. not a provisioned commercial sender ID
- Payload is JSON with keys `fieldcustcode, fieldCode, fieldName, fieldBala, fieldPdc, field2…field101` — a **customer outstanding-balance** template, not a sales summary
- Sample line, phone masked: `30/06/2026 11:37:38 | ,******4568 | MARGDEMO | {…}`

Marg also ships `whatsapp.exe` (189,952 B) and `whatsapp.dll` (238,592 B) in the root, plus `System\margmsgwap01.jpg` and related WhatsApp message templates.

### Reading

The plumbing for automated outbound messaging exists and fires. **Email specifically shows no evidence of ever having been configured or used**, and the settings live in encrypted tables that cannot be inspected from outside the application. This is a UI/support question, not a filesystem question.

**Ask Marg support / check in the UI:** whether a *scheduled* report can be attached to email (Marg's "Auto Mail" / "Report Scheduler" area), and what SMTP settings the install expects. If email is turned on, note the sender is currently `MARGDEMO` and would need a real sender configured.

---

## 2. SQL SYNC — **NOT-AVAILABLE as configured** (with one check I could not perform)

### What I could not do, stated plainly

**I cannot run `netstat`, `sc query`, `services.msc` or any command on this PC.** The device bridge for this Windows machine exposes file tools only (`device_list_dir`, `device_stage_files`, `device_commit_files`) — there is no shell tool, confirmed by tool lookup. So the direct question "is a MySQL service running and is 3306 listening" is **not answerable from this session**.

**Two commands to settle it in 30 seconds** (Command Prompt on the Marg PC):

```
netstat -ano | findstr ":3306"
sc query type= service state= all | findstr /i "mysql maria sql"
```

Empty output from both = no SQL server on the machine.

### File evidence, which points strongly to "not in use"

I did **not** open `margsqlconnection.ini` or `mysqlflp.ini`. Metadata only:

| File | Size | mtime (IST) | Reading |
|---|---|---|---|
| `System\margsqlconnection.ini` | 525 | **2025-09-30 16:37** | **Untouched for ~10.5 months.** This timestamp sits in the same cluster as `marg0001.ini`–`marg0012.ini` and `menutable.ini` (all `2025-09-30`), which is the install/update stamp. This file appears to be **the shipped default, never configured.** |
| `System\mysqlflp.ini` | 7,033 | 2026-08-15 11:01 | Recent — but it shares its timestamp with `serverinfo.ini` (11:01), `authorisestatus.ini`, `backupstatus.ini`, `servicesstatus.ini` (10:20). This is **Marg startup housekeeping**, rewritten on every launch whether or not SQL is used. |
| `System\serverlastrun.ini` | **0 bytes** | 2016-09-11 | Never written |
| `System\serverstatus.ini` | **0 bytes** | 2017-06-27 | Never written |

### Correction to an S180 speculation

S180 flagged `System\syncdata.ini/.cdx`, `Data\margsync.c18` and the SQL config files together as "an active SQL sync layer". **That was wrong, and this session corrects it.** Current mtimes:

| File | mtime (IST) |
|---|---|
| `System\syncdata.ini` / `syncdata.cdx` | 2026-08-15 **14:42** |
| `Data\margsync.c18` | 2026-08-15 **14:42** |
| `ebusiness\39548\up_party.ini`, `up_os.ini`, `up_pro.ini`, `up_group.ini`, `up_stype.ini`, `up_payid.ini`, `up_users.ini` | 2026-08-15 **14:42** |

All seven move **in the same second**. `syncdata.*` and `margsync.c18` are the bookkeeping for the **e-business cloud uploader** described in §3c — not for a database mirror. The SQL config files sit still while all of this churns.

**Verdict: NOT-AVAILABLE as currently configured.** Standing up MySQL sync would mean a new Marg module, new licensing and a new service to keep alive — the opposite of "cheapest supported". Run the two commands above to close it out, then drop this route.

---

## 3. SCHEDULED / CLI EXPORT

### 3a. Windows Task Scheduler — **NOT-DETERMINABLE FROM HERE**

```
device_list_dir "C:\Windows\System32\Tasks"
→ Error: C:\Windows\System32\Tasks is not inside a folder connected to Cowork on this device.
```

It is also a protected system location that cannot be granted through the folder-access prompt. **Command to settle it on the PC:**

```
schtasks /query /fo LIST /v | findstr /i "marg"
```

### 3b. Marg's own scheduler — **POSSIBLE-WITH-A-SETTING** (and it demonstrably works)

`D:\MARGERP\serverbackup\` contains a **rotating day-of-week backup set, all seven files current**:

| File | Size | mtime (IST) |
|---|---|---|
| `sunday.mst` | 11,319 | 2026-08-09 09:16 |
| `monday.mst` | 11,328 | 2026-08-10 08:16 |
| `tuesday.mst` | 11,304 | 2026-08-11 10:28 |
| `wednesday.mst` | 11,319 | 2026-08-12 11:09 |
| `thursday.mst` | 11,319 | 2026-08-13 08:59 |
| `friday.mst` | 11,323 | 2026-08-14 13:56 |
| `saturday.mst` | 11,318 | 2026-08-15 11:16 |

Alongside them, dated data backups written the same day, e.g. `55484_c18_d_hkbmj.lpojm_24354` (2,200,281 B, 2026-08-15 11:16) and `76861_d01_retail_dgfih.hifgd_38062` (44,730 B, 2026-08-15 11:16). `Data\Backup\` carries the same weekday rotation.

**This is proof that Marg runs an unattended daily job with no human clicking anything.** Note the trigger is *event-based, not clock-based* — fire times range 08:16 to 13:56, so it hangs off first-launch or exit-of-day, not a fixed wall-clock time. For a pharmacy open every day that is acceptable, but a feed built on it must not assume "arrives by 21:00".

**The relevant hook:** each Marg user folder contains an **`auto` sub-folder under `report`**:

```
D:\MARGERP\users\50018\report\auto\      (empty)
D:\MARGERP\users\61376\report\auto\      (empty)
```

Both exist and both are empty. The name, the placement next to the manual report output, and the existence of a working scheduler together make "Marg has an auto-report feature that writes here" the obvious reading — but **it has never produced a file on this install**, so this is inference, not proof.

Related live artefact: `D:\MARGERP\operator\work_c18_autoebill.tmp` (0 B, 2026-08-15 14:40) — an "auto e-bill" working file, touched today.

**Action:** ask Marg support how to enable a scheduled/auto report and confirm it writes into `users\<userid>\report\auto\`. If yes, this is the whole solution.

### 3c. e-business cloud uploader — **POSSIBLE-WITH-A-SETTING** (strongest single lead)

`D:\MARGERP\ebusiness\39548\` is a live upload/download staging area, **actively running today**. Files prefixed `up_` (upload to cloud) and `dwn_` (download from cloud), each an encrypted table with a `_lvl.cdx` index.

**Currently syncing** — all rewritten 2026-08-15 **14:42 IST**, i.e. minutes before this survey, and repeatedly through the day:

| Table | Size | What it is |
|---|---|---|
| `up_party.ini` | 221,489 | Customer/party master |
| `up_pro.ini` | 399,585 | Product master |
| `up_proadd.ini` | 196,610 | Product additional |
| `up_stype.ini` | 116,530 | Sale types |
| `up_os.ini` | 61,485 | Outstanding balances |
| `up_group.ini` | 10,062 | Account groups |
| `up_payid.ini` | 9,525 | Payment IDs |
| `up_users.ini` | 1,164 | Users |

**Dormant** — all frozen at 2026-08-01 09:14 IST, the same instant, i.e. written once at schema init and never since:

| Table | Size |
|---|---|
| **`up_sale.ini`** | **984** |
| **`up_saleinfo.ini`** | **600** |
| `up_calling.ini`, `up_disc.ini`, `up_ledger.ini`, `up_pdc.ini`, `up_po.ini`, `up_purord.ini`, `up_sms.ini`, `up_prostore.ini`, `up_partytran.ini`, `up_spldisc.ini`, `up_tagmain.ini`, `up_pcm*.ini` | 440–984 each |
| `dwn_ordmain.ini`, `dwn_ordsub.ini`, `dwn_tagsub.ini` | 664–1,496 |

**Reading:** Sanjeevni already has a working, supported, automatic uploader pushing masters to Marg's cloud several times an hour — and it has **`up_sale` and `up_saleinfo` slots that are switched off**. If those can be enabled (a Marg cloud/e-business subscription setting), daily sale data leaves this PC automatically with **zero new infrastructure on the clinic side** — the clinic then reads it from Marg's cloud rather than from this machine.

**Action:** ask Marg what enables `up_sale` / `up_saleinfo`, and what the clinic-side read path is (Marg Books portal, an API, or a cloud export).

### 3d. Tally XML export on a schedule — **NOT-AVAILABLE**

Confirmed manual. The XML exports in the Marg root have irregular mtimes, months apart, in human-sized chunks:

| File | Size | mtime (IST) |
|---|---|---|
| `daybook.xml` | 1,205,131 | 2026-07-12 12:32 |
| `master.xml` | 1,661,807 | 2026-07-28 20:39 |
| `transactions.xml` | 10,435,250 | 2026-07-28 20:39 |
| `master 2025 26.xml` | 562,472 | 2026-07-09 12:50 |
| `TALLY MARCH 26.xml` | 4,672,733 | 2026-06-11 20:38 |
| `TALLY APR MAY 26.xml` | 8,054,405 | 2026-06-11 20:30 |

Nothing has regenerated since 28 July — including during today's heavy Marg activity. **These are produced by a human clicking Export.** Excellent format (S180 §9 documents the fields), useless as an automatic trigger.

### 3e. Every other candidate export directory is empty

Checked and returned zero entries: `export\`, `&reportpath\`, `netorder\`, `offlineorder\`, `Ede\`, `ims\`, `Reports\`, `files\`, `awacs\`, `emailserver\`, `emailpend\`, `ebusiness\community\`, `usertemp\`, `Temp\server\sync\`.

`backtemp\` holds one file from 2013. `GSTRETURN\` holds quarterly GST returns (`…_GST_CMP08_Q1_2026.xls`, 2026-04-07) and has `EXPORT\` and `ERROR\` sub-folders — GST-cycle only, not daily sale.

---

## 4. EXPORT FOLDER / THE DAILY SALE XLS — **SUPPORTED-AND-AUTOMATABLE**

### Where the staff report actually lands

**`D:\MARGERP\users\<userid>\report\REPORT_1.XLS`**

Found today at `D:\MARGERP\users\61376\report\REPORT_1.XLS` — **90,112 bytes, written 2026-08-15 09:59 IST**. It is a genuine OLE2/BIFF Excel file (magic `D0 CF 11 E0 A1 B1 1A E1`), **not encrypted**, opens cleanly with a standard reader.

Two user folders exist, both with the same structure:

```
D:\MARGERP\users\50018\  → margstart.csv, report\, report\auto\, temp\
D:\MARGERP\users\61376\  → margstart.csv, report\, report\auto\, temp\, report\REPORT_1.XLS
```

### What is in it — this is exactly the S179 target

Sheet name: **`MARG ERP 9+ Excel Report`** *(this also settles the S180 open question about the Marg version: **Marg ERP 9+**)*

426 rows × 9 columns. Report title: **`BILL WISE SALES STATEMENT FROM 01-08-2026`**, covering **01-08-2026 → 14-08-2026** (14 daily sections).

| Column | Header |
|---|---|
| A | `BILL NO.` |
| B | `DESCRIPTION` — phone + customer name (**PII**) |
| C | `D.R.` — payment mode |
| D | `GROSS AMT.` |
| E | `DISCOUNT` |
| F | `TAX` |
| G | `DR/CR` |
| H | `NET AMT.` |
| I | `CASH` |

Structure: company header block repeated per page (`SANJEEVNI MEDICOS` / address / phone), a date row per day (`01-08-2026` …), bill rows, a `DAY TOTAL :` row per day, and a final `GRAND TOTAL :` row.

**Content statistics:**

- **345 bill rows**
- Bill numbers **`A002660` … `A002986`** (327 rows) plus **`CN00167`, `CN00168`** credit notes (18 `CN` rows total) — the exact series the S179 brief named
- Payment modes in `D.R.`: `.CASH` (260 rows) and `.UPI` (85 rows), some suffixed `#`
- `GRAND TOTAL :` row — Gross 285,273.40 / Discount 7,298.86 / Tax 0.00 / DR-CR −888.00 / **Net 277,083.00** / **Cash 193,412.00**
- Footer: `Total No. of Bills: 345`

**One masked sample row:** `A002661 | ******6445 <name withheld> | .CASH # | 852.07 | 2.07 | 0.0 | 0.0 | 850.0 | 850.0`

### Assessment

Everything the finance module needs — bill number, date, payment mode, gross, discount, net, cash — is already produced, in a clean unencrypted format, at a **predictable path**. The encryption problem from S180 is entirely bypassed.

**The gap is the trigger, not the data.** Two caveats a design must handle:

1. **Fixed filename.** `REPORT_1.XLS` is overwritten on each run — no date in the name. A watcher must copy-on-change and stamp it, or it will lose yesterday's file.
2. **Per-user folder.** The path contains a Marg user ID (`61376`, `50018`). Whoever runs the report determines where it lands, so a watcher should watch `users\*\report\` rather than one hard-coded folder.
3. **Human-triggered today.** Today's file covers 01–14 Aug and was generated at 09:59 — a month-to-date run, not a single-day run. Whether staff run it daily and with what date range needs confirming with them.

`export\` itself is empty and appears unused by this install — the report path is the `users\<id>\report\` one, not `export\`.

---

## 5. Recommended order of attack

1. **Confirm with the pharmacy staff** how often they run the BILL WISE report and for what date range. If it is already daily, a folder watcher on `D:\MARGERP\users\*\report\REPORT_1.XLS` (copy-on-change, stamp with date, ship to the clinic) is a working feed **today, with no Marg changes and no encryption work**. This is the cheapest thing that can possibly work.
2. **Ask Marg support two questions in one call:**
   a. How to enable a scheduled/auto report so it writes to `users\<userid>\report\auto\` without a human clicking. *(Their scheduler demonstrably works — it runs the daily backup.)*
   b. What enables `up_sale` / `up_saleinfo` in the e-business cloud sync, and how the clinic would read that data. *(This channel is already running for masters.)*
   Either answer removes the human from the loop; (b) also removes the clinic's dependency on this PC being reachable.
3. **Run the three verification commands** on the Marg PC (30 seconds total) to close out the routes I could not check from here:
   ```
   netstat -ano | findstr ":3306"
   sc query type= service state= all | findstr /i "mysql maria sql"
   schtasks /query /fo LIST /v | findstr /i "marg"
   ```
4. **Only if 1–3 all fail:** revisit the S180 decryption route. It remains tractable but is unsupported and would break on any Marg update.

**Do not pursue:** MySQL sync (§2), Tally XML as an automatic trigger (§3d), or the `export\` folder (§4).

---

## Appendix A — every directory checked this session

| Path | Result |
|---|---|
| `emailserver\` | **empty** |
| `emailpend\` | **empty** |
| `export\` | **empty** |
| `&reportpath\` | **empty** |
| `netorder\` | **empty** |
| `offlineorder\` | **empty** |
| `Ede\` (recursive) | **empty** |
| `ims\` | **empty** |
| `Reports\` | **empty** |
| `files\` | **empty** |
| `awacs\` | **empty** |
| `usertemp\` | **empty** |
| `ebusiness\community\` | **empty** |
| `Temp\` | 1 subdir: `server\` |
| `Temp\server\` | 2 subdirs: `backtemp\`, `sync\` |
| `Temp\server\sync\` | **empty** |
| `backtemp\` | 1 file, `D--20120401-20130331.W02` (9.5 MB, 2013-03-09) |
| `serverbackup\` | 67 entries — live rotating daily backups, all 7 weekday `.mst` files current |
| `operator\` | ~220 entries — `user_N.prn`/`.txt` scratch, `margu1–6.ini` (encrypted), `hold_<company>_data.tmp`, `work_c18_autoebill.tmp` |
| `users\` (recursive) | `50018\`, `61376\`, `a\`; each with `margstart.csv`, `report\`, `report\auto\`, `temp\` |
| `users\61376\report\` | **`REPORT_1.XLS` (90,112 B, 2026-08-15 09:59 IST)** + empty `auto\` |
| `users\50018\report\` | empty `auto\` only |
| `ebusiness\39548\` | 70 entries — live `up_*` / `dwn_*` cloud sync staging |
| `payment\` | **empty** |
| `GSTRETURN\` | quarterly GST `.xls` + `EXPORT\`, `ERROR\` subdirs |
| `System\` | ~250 entries — see §2 for the SQL/status files |
| `C:\Windows\System32\Tasks` | **not reachable** — outside connected folders, not grantable |

## Appendix B — facts a future session can rely on

- Daily sale report path: `D:\MARGERP\users\<margUserId>\report\REPORT_1.XLS` — plain BIFF `.xls`, fixed filename, overwritten each run. User IDs seen: `61376`, `50018`.
- Report columns: `BILL NO. | DESCRIPTION | D.R. | GROSS AMT. | DISCOUNT | TAX | DR/CR | NET AMT. | CASH`; day sections headed `DD-MM-YYYY`; `DAY TOTAL :` and `GRAND TOTAL :` rows in column C.
- Payment modes appear in `D.R.` as `.CASH` / `.UPI`, sometimes with a trailing `#`.
- Bill series: `A00nnnn` for sales, `CN00nnn` for credit notes.
- Marg version string, from the report sheet name: **`MARG ERP 9+ Excel Report`**.
- Marg runs an unattended daily job (backup) with an **event-based, not clock-based** trigger — observed fire times 08:16–13:56 IST over the last 7 days.
- `users\<id>\report\auto\` exists on every user and is empty — presumed auto-report output folder, unconfirmed.
- e-business cloud sync writes `ebusiness\39548\up_*.ini` plus `System\syncdata.*` and `Data\margsync.c18` **in the same second**, several times an hour. `up_sale.ini` / `up_saleinfo.ini` exist but are dormant since 2026-08-01 09:14.
- `System\margsqlconnection.ini` last modified 2025-09-30, in the install-timestamp cluster — never configured. Not opened.
- Mail: `emailserver\` and `emailpend\` both empty; all mail config encrypted; `margsms.txt` shows 28 outbound SMS 30/06–14/08/2026 under sender ID `MARGDEMO`.
- No shell is available on this device through the Cowork bridge — service/port/task-scheduler questions must be answered by someone at the PC.

*Nothing under `D:\MARGERP` was written, renamed, moved or deleted during this session. No file matching licence / sqlconnection / mysqlflp / password was opened.*
