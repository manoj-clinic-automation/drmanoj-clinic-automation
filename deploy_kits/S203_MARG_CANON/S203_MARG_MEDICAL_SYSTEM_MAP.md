> ## ⚠ SUPERSEDED — DO NOT ACT ON THIS DOCUMENT
> **Superseded on 26-Aug-2026 by `MARG_AND_MEDICAL_PC_MASTER_REFERENCE_v3.md`**
> (md5 `579ea885e440e76af73de3ecc4542d71`), which **corrects three of this document's statements**:
> AF-1 "still armed" (master §3.1 — the file it is armed on is not on the machine); the backup
> "configured Oct-2025 and never once run" (master §4.2 — **nothing in Task Scheduler and nothing at
> startup runs a backup at all**; it was never scheduled); and the "four-copy `marg_report.py`
> problem" (master §9 #2 — the `28b47d44` copy runs on **manojz**, and the file is absent from the
> medical PC).
> **This map was written from the record; the master was written from the machine.** Its §5 D350 gap
> tables are not carried by the master and remain the unique content here.
> Label added at S203, 26-Aug-2026. **Retained, not deleted (F-23).**

# S203 — THE MARG PIPELINE AND THE MEDICAL PC: THE COMPLETE MAP FROM THE RECORD

**Session 203 · 26-Aug-2026 · built by reading the canonical record, not the live code.**
A parallel pass read the live code; this document is the documentary half.

**Sources, each read in full:** `CANONICAL_MANIFEST.md` (S202 close) · `MARG_PIPELINE_REFERENCE_v1`
· `MARG_PIPELINE_MAINTENANCE_FLOW_v1` · `MARG_INGESTION_REFERENCE_v1` ·
`S202_Marg_Transport_Resilience_D350_CONTRACT` · `S195_Medical_Watcher_LIVE_Reference` ·
`S201_Marg_Pipeline_Rebuild_Plan` · `S201_Part0_Rescan_Record` · `S201_Part1_Capture_And_Agent_Record`
· `S201_Parts2_3_4_Record` · `S201_Marg_Outbox_Never_Drained_Finding` ·
`S201_Medical_Pipeline_Completion_Audit` · `S201_Month_vs_Marg_Explained` · `S201_PARKED_BACKLOG` ·
`S202_PENDENCY_AUDIT` · `OWNER_TODO_LIVE` · `AUDIT_RUN_2026-08-24_slice1` ·
`Clinic_Source_Data_Retention_Policy_v1` · `KB_Register_v5_54_S202` · `Fault_Action_Register_v2_41` ·
`KB_History_Archive_v1_49_S202` §S195 / §S201 / §S202.

**Every hash in this document was either transcribed from the file that carries it or computed this
session and labelled as such. Nothing is invented. Where a value could not be established it says
"not established" and says where it was looked for.**

---

## 0 · VERIFICATION DONE BEFORE WRITING

The five Marg/medical documents in the canon were hash-checked against their `CANONICAL_MANIFEST.md`
Tier-1 rows, computed this session in
`D:\dr-manoj-git\drmanoj-clinic-automation\deploy_kits\KB_canon_all\` **on manojz**:

| document | manifest pin | measured | verdict |
|---|---|---|---|
| `MARG_PIPELINE_REFERENCE_v1.md` | `97b3cf73f7f83c0860bde2d911596ff7` | same | ✅ |
| `MARG_PIPELINE_MAINTENANCE_FLOW_v1.md` | `c2b5251f55762490ad219b8855a18dd8` | same | ✅ |
| `MARG_INGESTION_REFERENCE_v1.md` | `4d603b727a91a7c782992f092fc949e3` | same | ✅ |
| `S195_Medical_Watcher_LIVE_Reference.md` | `885090ab946b61e7b5a990a14a190a15` | same | ✅ |
| `Clinic_Source_Data_Retention_Policy_v1.md` | `90831162f985359b69725b1dc874e679` | same | ✅ |
| `KB_Register_v5_54_S202.md` | `8fede84d7126e13fca17418e449f9d0a` | same | ✅ |
| `Fault_Action_Register_v2_41.md` | `4883e3bdf08cba92da7597448e00f2da` | same | ✅ |
| `KB_History_Archive_v1_49_S202.md` | `06c6670a8a1155959e4f0961ad58e7c5` | same | ✅ |

**The documents this map rests on are the canonical bytes.** (`CANONICAL_MANIFEST.md` itself measures
`3ff86788c5da3e1d10a16d72be060bf4`; the manifest pins itself as *"self — recomputed last, each EOS"*,
so there is no row to compare it against. That is by design, not drift.)

---

# 1 · THE MACHINES

Five things carry pharmacy revenue. **Every path below names the machine it is on.** The owner has
asked twice for this and been given bare paths; that is corrected here.

---

## 1.1 · THE MEDICAL PC — hostname `MEDICAL`, Tailscale address `100.119.151.40`

**What it is.** The pharmacy counter machine. **Marg ERP 9+ runs here and only here.** It is the
origin of every rupee of Sanjeevni pharmacy revenue in the books.

**Windows.** Windows 10 Pro (`MARG_PIPELINE_REFERENCE_v1` §1). Two accounts are named in the record:
`MEDICAL\SET`, which **has** a password, and `MEDICAL\user`, which **has none** — and *"Windows
refuses network logins for accounts without one"* (`MARG_PIPELINE_MAINTENANCE_FLOW_v1` §2, the
guest-access block).

**What runs on it**

| what | full path ON THE MEDICAL PC | how it starts |
|---|---|---|
| **Marg ERP 9+** | `D:\MARGERP\margwin.exe` | by hand. **Must be launched with `D:\MARGERP` as the working directory** (`MARG_PIPELINE_REFERENCE_v1` §8a) |
| **`medical_agent.py`** — the supervisor | `D:\SendToClinic\medical_agent.py` | `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\MargAgent.cmd` — **at LOGON** |
| **`marg_watch.py`** — the resident capture watcher | `D:\SendToClinic\marg_watch.py` | a **child process of the agent**, restarted within 60s if it dies |
| **bundled portable Python 3.11.9** | `D:\SendToClinic\pyportable\python.exe` | called by full path, always |
| **the scoped upload token** | `D:\SendToClinic\token.txt` | plain text **by design** (scoped, stage-only) |
| **the manual fallback sender** | `SEND_TO_CLINIC.bat` + `GUARD_AND_SEND.bat` (in `D:\SendToClinic\`) | double-click, by a human |
| **Google Drive for Desktop** | mounts as **`F:\My Drive\`** on this machine | resident |
| **Tailscale** | — | resident |

**The two Marg output trees.** This is the single most operationally important fact about this
machine, found at S201 and recorded in `KB_History_Archive_v1_49_S202` §S201 and in D347:

```
D:\MARGERP\users\<uid>\report\REPORT_n.XLS      <- known since S180
C:\Users\Public\MARG\<id>\all\REPORT.PDF        <- found 25-Aug-2026, S201
```

Both are **fixed slots, overwritten on every export** — which is why capture must be local and
instant, not a 10-minute pull (`S201_Medical_Pipeline_Completion_Audit` §4).

**Watch roots.** The agent watches **three** roots as of S201.7:
`D:\MARGERP\users` · `D:\MARG REPORTS` (where Dr Manoj saves by hand) · `C:\Users\Public\MARG`
(`S201_Medical_Pipeline_Completion_Audit` §2: *"watcher `aa55cdb5` watching **three** roots"*).

**Local spool.** `D:\SendToClinic\_captured\` — files renamed `<stamp>__<slot>__<md5>` and deduped by
md5. `D:\SendToClinic\heartbeat.txt` and `agent.log` sit beside it.

**What it can reach.** Google Drive (both directions). The clinic server over HTTPS (the manual
sender). It does **not** reach manojz — the relationship is one-way.

**What it cannot reach / what cannot reach it.** *"manojz reads medical READ-ONLY. manojz CANNOT
write to medical"* (`MARG_PIPELINE_REFERENCE_v1` §1). The SMB write returns **ERROR 5** — this is
**F-168**, still OPEN: *"Every 'push to medical' feature assumed a write the OS forbids"*
(`S202_PENDENCY_AUDIT` §5). Delivery **to** medical therefore travels only by Google Drive.

**Single point of failure for:**
- **Every Marg report in existence.** Nothing else generates one.
- **The only place Marg's live pharmacy data exists** — see §6.
- Capture. If the watcher is not running, an export can still be pulled from `D:\MARGERP\users` by
  manojz within 10 minutes **but only from D:** — Marg's `C:` PDF tree is invisible to manojz
  (Tailscale shares `DDrive` only), so a PDF exported while the watcher is down is **lost when the
  slot is overwritten.**
- **The watcher starts at LOGON.** *"A machine left at the login screen after a reboot captures
  nothing"* (`MARG_PIPELINE_MAINTENANCE_FLOW_v1` §6).

---

## 1.2 · manojz — the owner's own PC

**What it is.** The hub. Puller, router, archive, sender, offsite mirror, publisher and (as of S202)
the pipeline's reporter to the VPS. `AUDIT_RUN_2026-08-24_slice1` §Surface B names the concentration
plainly: *"manojz is still publisher+puller+mirror+offsite in one box."*

**What runs on it**

| what | full path ON manojz | trigger |
|---|---|---|
| scheduled task **"Marg pull from medical"** | runs `D:\Downloads\margsync\MargPull\PULL_FROM_MEDICAL.bat` via `PULL_HIDDEN.vbs` | **every 10 minutes** |
| the live tooling folder | `D:\Downloads\margsync\MargPull\` | — |
| the archive | `D:\Downloads\margsync\MargArchive\` | written by the router |
| medical mirrors | `D:\Downloads\margsync\medical_SendToClinic\` · `D:\Downloads\margsync\marg_reports_mirror\` | robocopy, each cycle |
| manual-upload surface | `D:\Downloads\margsync\_UPLOAD_NOW\` | refreshed each cycle |
| the token **cache** | `D:\Downloads\margsync\SendToClinic\token.txt` | refreshed from medical at send time |
| Google Drive for Desktop | mounts as **`H:\My Drive\`** on this machine | resident |
| the git repo | `D:\dr-manoj-git\drmanoj-clinic-automation\` | `PUBLISH_ALL.bat` |
| cold kits | `D:\dr-manoj-git\cold_kits\` | at close, when due |
| PHI quarantine (S202) | `D:\dr-manoj-git\_PHI_QUARANTINE_S202\` | S202, one-off |
| vendor bank data, outside git | `D:\dr-manoj-git\NEFT_Vendor_Master\` | S198 |

**Note the drive letters are different on the two machines.** Google Drive is **`H:` on manojz** and
**`F:` on the medical PC** — the same folder, two letters. `S201_Part1_Capture_And_Agent_Record` §2
states it explicitly, and `pipeline_status.py` was deliberately built to discover the heartbeat
*"across H:, F: and the local mirror, newest-that-exists winning… so a moved drive letter degrades to
'could not read it' and never to a silent green"* (`KB_Register_v5_54_S202` v5.51).

**Live tooling — pins verified against the box this session** (computed in
`D:\Downloads\margsync\MargPull\`):

| file | record pin | measured 26-Aug | verdict |
|---|---|---|---|
| `marg_router.py` | `bbc50f9172211925755eeaa25920d1cf` (S201 records) | same | ✅ |
| `marg_watch.py` | `2076fe1d8d145524be16ae857b3d838d` (S201 records) | same | ✅ |
| `marg_gate.py` | `af2c3ca507136f3f82ec7cf64e8aae34` (Register v5.54 CURRENT) | same | ✅ |
| `marg_rescan.py` | `ae92e3316efa07360c884c7c67379957` (S201 records) | same | ✅ |
| `pipeline_status.py` | `51cf10c9f2543fcd48a61ee7f8faf51a` (Register v5.54 CURRENT) | same | ✅ |
| `xlsx_stdlib.py` | `bbe11a8953f66c27126c48e773cfbe35` (S201 records) | same | ✅ |
| `medical_inventory.py` | `3ee927f023f68dd4a0c5c8b28b0037b4` (S201 records) | same | ✅ |
| `signatures.json` | `3e9cbba02ffb4e0f131738eee7a465f7` (Register v5.54 CURRENT) | same | ✅ |
| **`PULL_FROM_MEDICAL.bat`** | **`3c5389d54241f234e94dc62b82d046e1`** (Register v5.54 CURRENT) | **`92f03999d0a14d00b7f552dbb4d44c05`** | ❌ **DRIFT** |
| `marg_report.py` (a manojz copy) | not pinned for manojz anywhere | `28b47d447cfd966411742055717a5c56` | see §3, the **fourth** parser copy |

**`PULL_FROM_MEDICAL.bat` on the box does not match its Register pin.** A backup named
`PULL_FROM_MEDICAL.bat.bak_before_diag` sits beside it, which is consistent with the S202 change the
maintenance flow describes (*"The pull now diagnoses this itself (S202) — read what it prints"*), but
**the cause is not established from the record** and the pin was never moved. The Register row itself
anticipates this: *"This is the owner's own script and he may edit it — the pin records the as-wired
state for provenance, and it is BLIND to `verify_live_pins.py` in any case (PC-side, F-186)."***This
is a live, currently unrecorded instance of F-186.**

**What manojz can reach.** The medical PC's `D:` **read-only, over Tailscale**, as
`\\100.119.151.40\DDrive` — and, since 26-Aug, only with a stored credential. Google Drive. The
clinic server. GitHub.

**What it cannot reach.** The medical PC's **`C:` drive** — the Tailscale share is `DDrive`, D: only.
*"manojz cannot see C: at all, and never could"* (`S201_Medical_Pipeline_Completion_Audit` §4). And it
cannot **write** anything to the medical PC.

**Single point of failure for:** routing · verification · archiving · the **only** automatic upload
to the clinic server · the offsite copy · the daily picture · publishing the canon to GitHub · the
cold kits. If manojz is off, reports accumulate on the medical PC and nothing reaches the books; the
only fallback is a human double-clicking `GUARD_AND_SEND.bat` on the medical PC, which carries **AF-1**
(§3).

---

## 1.3 · THE VPS — `clinic-finance`, `followup.dr-manoj.in`

**What it is.** The books. Everything downstream of the POST.

**Relevant paths ON THE VPS (Linux):** `/root/finance/` (`finance_app.py`, `finance_ingest.py`,
`marg_report.py`, `finance_returns.py`, `finance_identity.py`, `finance.db`) ·
`/etc/systemd/system/clinic-finance.service` (carries `FINANCE_MARG_TOKEN`) · `/root/deploy/`
(`verify_live_pins.py`, `live_pins.txt`) · `/root/staff_ledger/` · port 8106, served at `/finance` on
the portal origin.

**Current live pin:** `/root/finance/finance_app.py` = **`50ac4c86a3985bf82269d650d5e46f0f`**,
live smoke **719/719** (`KB_Register_v5_54_S202`, live-file table). For VPS python the project rule is
`/root/wa/venv/bin/python3`.

**What it can reach.** Nothing on the owner's machines. **This is the defining constraint of the whole
system.** `S201_Marg_Pipeline_Rebuild_Plan` §1: *"every server-side check watches arrival at the VPS.
It cannot see the medical PC, manojz, the archive, or Drive. Four of seven failures are on the blind
side of that line, and no amount of server-side work will fix that — the pipeline must report in."*
B2 (S202) partially closed this by having manojz **push** a status; the VPS still initiates nothing.

**What it deliberately does not keep.** *"The uploaded file is parsed and deleted inside the same
request (S186). The VPS keeps no export file — so a report can never be 're-read from the server'"*
(`MARG_PIPELINE_REFERENCE_v1` §3). An applied push has its `parsed_json` set to NULL — *"no PHI at
rest"* (`Clinic_Source_Data_Retention_Policy_v1` §2).

**Single point of failure for:** the books themselves. **Not** for the source exports — those live on
manojz and Drive, by design.

---

## 1.4 · GOOGLE DRIVE — `drmka.ortho@gmail.com`

**Same folder, two drive letters:** `H:\My Drive\Clinic Data Archive\` **on manojz**;
`F:\My Drive\Clinic Data Archive\` **on the medical PC**.

| folder | direction | contents |
|---|---|---|
| `Clinic Data Archive\MargArchive\` | manojz → Drive | the **offsite archive copy**, `robocopy /E`, append-only, no purge |
| `Clinic Data Archive\FromMedical\` | medical → Drive → Claude | `heartbeat.txt` (every 5 min), survey files, crash tracebacks |
| `Clinic Data Archive\ToMedical\` | Claude → Drive → medical | the `_kit` update channel, `INSTALL_AGENT.bat`, `CLEANUP_MEDICAL.bat` |

**What Drive is load-bearing for.** The heartbeat, and the only working delivery channel *to* the
medical PC (D347). **It carried the heartbeat unbroken through the entire 8h40m outage of 26-Aug**
(`S202_..._D350_CONTRACT` §0) — which is exactly why D350 §1 proposed it as a fallback transport, and
exactly why the owner could park that proposal without losing visibility.

**What it does NOT carry.** `_spool` and `_outbox` are **excluded** from the offsite copy, so
**the pending-send queue has no offsite copy** (`MARG_PIPELINE_REFERENCE_v1` §6;
`S201_PARKED_BACKLOG` B5). And it does not carry reports in the pull direction — see §1.5.

---

## 1.5 · TAILSCALE — and the correction that matters

**What it does.** Gives manojz a **read-only, D:-only** view of the medical PC at
`\\100.119.151.40\DDrive`. Every Marg report that reaches the books travels this way.

**THE CONFLICT IN THE RECORD, NAMED.**

- **D347 (S201, in `KB_Register_v5_54_S202` §decisions and `CANONICAL_MANIFEST.md` §S201):**
  *"Tailscale is a **read-only D:-only view and is NOT load-bearing**."*
- **`MARG_PIPELINE_REFERENCE_v1` §1 and `MARG_PIPELINE_MAINTENANCE_FLOW_v1` §2a (both CORRECTED at
  S202, and both newer):** *"**AND IT IS LOAD-BEARING. D347 calls Tailscale 'NOT load-bearing'; that
  is WRONG and 26-Aug-2026 proved it** — the whole pull leg runs over this share, and when it closed
  the feed stopped for 8h40m."*

**The newer documents are right and the decision record is wrong.** `S202_..._D350_CONTRACT` §5 lists
the D347 correction as owed *"in the decision record"* — the two reference documents were corrected at
the S202 close, **but D347's own text in the KB Register decisions index still says "NOT
load-bearing"** (verified this session in `KB_Register_v5_54_S202` line 738). **This correction is
still outstanding in the one place a future session will read the ruling from.**

**Single point of failure for:** the entire automatic report path. There is no second transport —
the owner parked D350 §1.

---

# 2 · THE CHAIN, STAGE BY STAGE

From *"Dr Manoj clicks a report in Marg"* to *"the figure appears on the clinic server."*

---

### STAGE 1 — the export is generated · MEDICAL PC · **manual, by design**

Marg → **BILL WISE SALES, *With Item Deta. = Yes*, single date**
(`MARG_PIPELINE_MAINTENANCE_FLOW_v1` §2). Marg writes to a **fixed, overwritten slot**:
`D:\MARGERP\users\<uid>\report\REPORT_n.XLS`, or `C:\Users\Public\MARG\<id>\all\REPORT.PDF` for
print/PDF output. Dr Manoj may also save by hand into `D:\MARG REPORTS`.

**Proof it ran:** the file's presence in the slot; `MEDICAL_RECENT.bat` on manojz (D: only).
**`MARG_PIPELINE_REFERENCE_v1` §1: "Automatic … Manual by design: running the report in Marg."**

### STAGE 2 — capture · MEDICAL PC · `marg_watch.py`, resident, event-driven

Started and supervised by `medical_agent.py`. Event-driven `ReadDirectoryChangesW` + a 5-second safety
poll (`S195_Medical_Watcher_LIVE_Reference`). Takes `.xls`/`.xlsx`/`.pdf` (PDF added at S201 Part 1),
**magic bytes checked per extension**, copies into `D:\SendToClinic\_captured\` renamed
`<stamp>__<slot>__<md5>`, deduped by md5.

**Proof it ran:** a new file in `_captured`; `CAPTURES: n` and `WATCHER : ALIVE` in
`heartbeat.txt`.

### STAGE 3 — the agent reports in · MEDICAL PC · `medical_agent.py`, every 5 minutes

Writes `F:\My Drive\Clinic Data Archive\FromMedical\heartbeat.txt` (arrives on manojz as `H:\…`).
Contents (`S201_Part1_Capture_And_Agent_Record` §4): watcher alive / pid / restart count · what it is
**actually** watching, read from the running configuration · captures today · **the installed
watcher's own md5** · the kit folder's status · Marg's report slots · disk free · **`IGNORED`** —
files in the watched folders the watcher cannot take, by name · and, since S201.11 (F-180), **the
agent's own md5 compared against the Drive copy, with the fix path** — because *"the agent never
updates itself; it REPORTS on itself."*

**Proof it ran:** the file's mtime. Healthy = **written within the last 10 minutes**
(`MARG_PIPELINE_MAINTENANCE_FLOW_v1` §1).

### STAGE 4 — the pull · manojz · scheduled task "Marg pull from medical", every 10 minutes

`PULL_FROM_MEDICAL.bat`, launched via `PULL_HIDDEN.vbs` so no console appears. Sequence
(`MARG_PIPELINE_REFERENCE_v1` §1, confirmed by `S201_Parts2_3_4_Record`):

```
stamp START -> _last_pull.txt
marg_watch.py --once --route   over 4 medical folders -> MargArchive\_spool
marg_router.py                 classify · verify · name by the date INSIDE the file
marg_rescan.py --if-signatures-changed   re-judge quarantine IF the registry changed
marg_gate.py send              drain _outbox to the clinic server
robocopy medical SendToClinic  -> margsync\medical_SendToClinic
robocopy medical MARG REPORTS  -> margsync\marg_reports_mirror
robocopy MargArchive           -> H:\My Drive\Clinic Data Archive\MargArchive   (offsite)
marg_gate.py status            refresh MARG_PICTURE.txt + _UPLOAD_NOW
stamp END -> _last_pull.txt
pipeline_status.py             POST manojz's view to the VPS   (S202 B2B)
```

**`pipeline_status.py` is called from EVERY exit path via a `:report` subroutine** — the first wiring
put it below the early exit and so *"ran only when the pull SUCCEEDED"*, which is **F-191(a)**,
corrected in `S202_B2C` (`KB_Register_v5_54_S202` v5.52).

**Proof it ran:** `D:\Downloads\margsync\MargPull\_last_pull.txt` — a `START` and an `END … ok`.
Healthy = **within the last 15 minutes**. Observed on the box this session: `START 26-08-2026
11:50:01.19 / END 26-08-2026 11:50:17.70 -- ok`.

### STAGE 5 — routing and verification · manojz · `marg_router.py`

Classifies by **`signatures.json`** — five report types self-classify: `SALE_BILLWISE` ·
`STOCK_CLOSING` · `STOCK_EXPIRY` · `PURCHASE_SUPPLIERWISE` · `PURCHASE_BILLWISE`, plus PDFs to
`DOCUMENT_PDF`. Each signature carries `title_regex`, `header` (exact prefix match on non-empty
cells), `uploadable`, `dating`, `deep_verify`, and **`end_marker`** — *"the row that proves the export
finished. **Derive a marker from a real sample; never guess one**"* (`MARG_PIPELINE_REFERENCE_v1` §7).

Names every file **by the business date INSIDE it**, and records `date_from`/`date_to` (what the title
claims) **separately from** `data_from`/`data_to` (what the rows carry) — S201 Part 0. Arithmetic
verification is real **for sale reports only**: day totals, grand total, bill count, truncation
marker, money parsed as integer paise.

**Proof it ran:** a new row in `D:\Downloads\margsync\MargArchive\index.csv` (15 columns) and the file
filed under `MargArchive\<TYPE>\<YYYY-MM>\`.

### STAGE 6 — the send · manojz · `marg_gate.py send`

Drains `MargArchive\_outbox` to the clinic server. Reads the live token **off the medical share at
send time**, caching it locally and falling back to the cache only when medical is unreachable.
Delivery state lives in `MargArchive\_outbox_state.json` — **not** in the folder contents, because
*"delivered files are deliberately KEPT there"* (`KB_Register_v5_54_S202` v5.51). Supersedes by
`span_key` across batches; a report is sent unless **every** day it covers already has a delivery at
least as new (`S201_Parts2_3_4_Record`, Part 3). Since `S202_PICTURE` the upload carries the
**archived filename** — before that *"every report ever pushed arrived at the server called
`REPORT_1.XLS`"* (v5.53).

**Proof it ran:** `MargArchive\_outbox_send_log.txt`; `_outbox_state.json`; `index.csv`
`uploaded` column; `MARG_PICTURE.txt` line *"exports NOT on server : 0"*.

### STAGE 7 — the POST · the wire

```
POST https://followup.dr-manoj.in/finance/api/marg-push
Header:  X-Finance-Marg: <FINANCE_MARG_TOKEN>
Body:    multipart/form-data, field name "file"
```

| response | meaning |
|---|---|
| `200` + `{"ok":true,"verdict":"ACCEPTED-FOR-REVIEW","days":[…],"bills":n,"item_lines":n,"id":n}` | staged; **nothing has entered the books** |
| `200` + already-received | same content already staged |
| `401` `{"error":"not_signed_in"}` | **the token was wrong or absent** — the request fell through to the session gate. *"This is what a stale token looks like; it does not say 'bad token'"* |
| `422` `column_map_mismatch` | the parser's columns do not match `ingest_column_map` |
| `503` | `FINANCE_MARG_TOKEN` absent server-side — fail-closed by design (F-84) |

**Two rules that bite:** *"The endpoint does **NOT** dedupe by content. Sending the same bytes twice
stages twice"* — and *"**Never** decide success from a response *file* that a failed request leaves
untouched — that is audit finding **AF-1**"* (`MARG_PIPELINE_REFERENCE_v1` §3). The claim that the
server dedupes was an assistant error at S201, *"made from expectation, not from reading the ingest
path"* (Archive §S201 §1).

### STAGE 8 — staging · VPS · `marg_push_staging`

The file is **parsed and DELETED inside the same request**. One entry per day in `parsed_json`:

```python
days_payload.append(dict(date=iso_d,
                         business_date=iso_d,     # added S201_A1FIX
                         net_p=d["net_p"],        # added S201_A1FIX
                         expect=nonzero.get(iso_d, 0),
                         lines_csv=…, items_csv=…))
```

Any day with no `day_entry` gets `data_flag MARG_DAY_NOT_FILED` (F-113).

**Proof it ran:** a row in `marg_push_staging`; the pushed-reports card at `/finance/approvals#margCard`.

### STAGE 9 — apply · VPS · **two doors, one guarded path**

(a) the **checker** presses Apply (`/finance/api/marg-push/apply`, `require("checker")`);
(b) **auto-replay** — the maker files a day that already has a pending push (S194).

Per day: **no `day_entry` → skipped** and recorded in `still_not_filed`, the export **not consumed**;
`rows_read != expect` → **`con.rollback()` and the whole day aborts** — *"A half-loaded day is never
left behind."* **Supersede first:** every earlier batch for the day has its `sale_item` and
`sale_item_review` rows **deleted** and is marked `superseded`.

> **The owner's own ruling on this, S202:** told to press Apply on a 12-June report, he asked why he
> should risk disturbing financial data. **He was right.** *"Apply supersedes, and would have DELETED
> 26 attributed rows and 26 RESOLVED review rows on a closed month, to arrive at the same number"*
> (Archive §S202). **Re-applying an old day is destructive to settled review work.**

### STAGE 10 — attribution · VPS · `finance_ingest.ingest_day()` · **the confidence gate**

```python
low_conf   = conf < min_conf                     # ingest.min_confidence, default 0.70
anonymous  = not cid and not name
structured = adapter != "sarvam_ocr"             # marg_export -> True
if low_conf or (anonymous and not (anon_to_walkin and structured)):
    -> sale_item_review
else:
    -> sale_item, patient resolved (WALK-IN if no id)
```

| the name field holds | confidence | outcome |
|---|---|---|
| `marg_report` supplied a clinic_id | 0.99 | attributed |
| an ID **and** a name | 0.95 | attributed |
| an ID, no name | **0.60** | **parked** ← backwards; **F-183** |
| a name, no ID | **0.50** | **parked** |
| nothing at all | 0.99 (the re-parse never runs) | attributed to **WALK-IN** |

### STAGE 11 — **THE ONE RULE THAT EXPLAINS EVERYTHING**

> **The Marg import never touches the money.** `finance_ingest.py` *"contains no reference to
> `day_line` at all. It cannot change a rupee of recorded revenue. This is **D313**"*
> (`MARG_INGESTION_REFERENCE_v1` §0).

- **Money** = `day_line` — what the maker types when filing the day.
- **Attribution** = `sale_item` — which patient bought what.

**Therefore a "books vs Marg" difference is never missing money.** It is the portion of the day not
yet attributed to a patient — **D348**, the owner's own naming: *"sale bills where the salesman did
not enter a clinic ID at the till."* Measured: 49 bills, **₹51,868** (`S201_Month_vs_Marg_Explained`),
matching the health-page difference **to the rupee on every one of six days**.

### STAGE 12 — reading the money out · **one expression, every reader**

```python
marg_net_sql(a) = SUM(CASE WHEN a.service LIKE '%return%' THEN -a.amount_p ELSE a.amount_p END)
```

`sale_item.amount_p` is non-negative, so a credit note is a magnitude plus a `_return` service; a
plain `SUM` **adds** a refund. On 18-08-2026 the true net was **20,599** and a second reader showed
**23,879** — out by exactly 2 × ₹1,640. **Rule: never write a second way of summing Marg rows.**

---

# 3 · EVERY KNOWN FAILURE MODE

Ordered by (money at risk × silence). **"Detected?" means: would anything tell the owner today.**

| # | failure | symptom the owner sees | detected today? |
|---|---|---|---|
| **F-179** *(CLOSED S201)* | **A queue with no consumer.** `marg_router.py` stamped every verified report *"queued for upload"* into `_outbox` and **nothing ever read `_outbox`**. Eleven verified reports (2 purchase · 6 closing stock · 2 expiry · 1 scrap) sat correct, hashed and undelivered for three days *"while capture, routing and archiving all reported success."* The only uploader was a manual double-click on the medical PC, last pressed 22-Aug. | *"A page that stayed empty."* | **Now yes** — `marg_gate.py` drains it each cycle; B2 reports the **drain state**, not the enqueue (F-179's own rule) |
| **F-180** *(CLOSED S201)* | **The supervisor could drift silently, and did.** Agent S201.10 sat on Drive from 19:30 while **S201.9 kept running**; the heartbeat printed the running version *"with nothing to compare it to."* | none | **Yes** — each heartbeat now hashes the running file against the Drive copy and prints the fix path. **By md5, never by the version string a file claims about itself** (D188) |
| **F-184** *(repaired S202)* | `deploy_kits/KB_canon_all/` — the one folder Phase 0 verifies — *"has never been maintained by any numbered step."* `MD5SUMS_ALL.txt` four sessions stale with 24 unlisted files; `KIT_ID.txt` nine sessions stale; **twelve manifest-pinned canonical documents absent from the folder entirely.** | Phase 0 reporting OK on a subset | **Yes now** — `A8b` exists in `END_OF_SESSION_PROMPT_v7` and was followed; `OWNER_TODO_LIVE` records *"F-184 was a failure to follow it, not a gap in it"* |
| **F-186** *(record corrected; STRUCTURAL GAP OPEN)* | **The live-pin discipline reaches only the VPS.** `margpull/signatures.json` on manojz was `3e9cbba0…` against a Register pin of `1b21f3bf…`, changed during S201, never recorded. Diffed rather than assumed — **the live file was strictly better than the record**; corrected FROM the box. | none | **NO.** `verify_live_pins.py` runs on the VPS and cannot reach either PC. It **classifies these rows BLIND** and prints *"These are blind spots, not passes. Nothing here was verified"* — it was right to say so. **See §4: a live instance exists right now.** |
| **F-187** *(CLOSED S202)* | **A custody fact recorded in prose.** The ₹20,000 that left Darpan's drawer on 17-Aug was itemised in `cash_count.explanation` in words and never entered. Books 63,903, drawer 43,903. | a drawer figure carrying money the drawer did not hold | Only by **physical count**. The count's first service was to **kill a plausible wrong theory** (*20,003 with 3 written off*, which was a running balance) |
| **F-188** *(CLOSED S202)* | **F-106 recurring** — three D330 ceiling checks built their fixture from the live store; F-187's legitimate correction put August over the ceiling and the test posted a negative rupee amount. **The books were correct and the TEST was wrong.** | a kit refused by its own gate at 698/701 | the gate itself — and the gate was right |
| **F-189** *(CLOSED S202 · assistant fault ×3)* | **Gates that do not gate.** (a) a smoke gate matching the bare word `OK`, **verified to accept 642/693**; (b) a preflight demanding a `sqlite3` binary the kit never invokes — a false refusal of a correct kit; (c) the pin-list generator run with `2>/dev/null`, so **its correct refusal was silenced.** | a degraded suite passing | caught an hour later by a **different** kit's exact-count gate |
| **F-190** *(CLOSED S202)* | **`.gitattributes` never pinned `*.md`** — 192 of 208 canon files free to change hash on a default Windows checkout (`core.autocrlf=true`). **Phase 0 would go RED on all 192 at once.** It never bit only because manojz happens to have `autocrlf=false` — *"one machine-local setting nothing records or checks."* | nothing, until a restore | **This is the disaster-recovery case** — it would fire the day the cold kit is restored onto a fresh machine |
| **F-191** *(two CLOSED · one is the OWNER'S)* | **Monitors born dead.** (a) `pipeline_status.py` wired **below** the pull's early exit → *"the monitor ran only when the pull SUCCEEDED"* — AF-2's shape, wired past the never-fired witness built hours earlier to catch exactly that. (b) B2A's own smoke gate (= F-189). **(c) `E:\auto` and `E:\MARGBCKUP\auto` on the medical PC have been EMPTY for eleven months** — automatic Marg backups configured ~02-Oct-2025 and **never once run.** | none — a human filled the gap by hand every 2–4 days | (a),(b) fixed. **(c) is OPEN and is §6 of this document** |
| **F-192** *(CLOSED S202)* | **A stale reading reported as a live state — the false green.** (a) B2A's watcher check read `alive` straight from a **heartbeat FILE that stops changing when the PC is switched off** — *"a green light for a machine that was off, and would have every night."* (b) `MARG_PICTURE.txt` measured coverage from the earliest report **ever seen**, so one 12-June report made it claim **56 MISSING DAYS** where the day before it read 0. | a green light, then 56 false alarms | **Yes now** — the watcher check is gated on heartbeat **AGE**; the picture is **told** its start date in `MargArchive\_coverage_from.txt` (**2026-08-17**, read from the box this session). *"56 false alarms became one real one."* |
| **F-193** *(CLOSED S202, documented by symptom)* | **Error messages naming the wrong cause — three in one day, ~1 hour.** (a) the pull printed *"Is it switched on and Tailscale connected?"* while both were demonstrably true; (b) Windows blamed *"unsafe or malicious devices"* for a credential problem; (c) Marg said *"Few important files not found in SYSTEM / Please RE-INSTALL software!"* for a wrong working directory — *"an instruction to reinstall an ERP on a live pharmacy system, for a `cd`."* | wasted hours chasing innocent causes | the pull now **pings first and says WHICH**; the other two are in `MARG_PIPELINE_MAINTENANCE_FLOW_v1` §2 by symptom |
| **THE 26-AUG GUEST-ACCESS BLOCK** *(the F-193/F-191 spine; fixed, not numbered separately)* | **From 23:08 IST 25-Aug to 07:33 26-Aug the pull failed every ten minutes and nothing said so.** Everything was healthy: the PC on with the owner in an RDP session, Tailscale `active; direct 192.168.1.37:41641`, agent running, watcher alive, Drive syncing. **Windows on manojz applied its default policy against unauthenticated guest access to SMB shares.** Fixed by AUTHENTICATING: `cmdkey /add:100.119.151.40 /user:MEDICAL\SET /pass`. **The forums' remedy — re-enabling insecure guest access on a PC holding patient records — was declined and recorded as declined.** **Credentials are stored PER WINDOWS USER**, so the scheduled task's Run-As account must be the one holding it. | *"a report I generated has not arrived"* — **found only because the owner asked** | **Now partly.** B2 reports pull liveness and medical reachability; the pull diagnoses guest-access itself. **But this is precisely what D350 §2/§3 exist to finish** |
| **AF-1** *(HIGH · still ARMED, deliberately)* | **The medical sender can report ACCEPTED for a report that never left, then permanently refuse to resend it.** `SEND_TO_CLINIC.bat` writes the reply via `curl -o` then greps it — **curl does not touch the output file when the connection fails**, so the file still holds the *previous* run's reply. It then prints ACCEPTED, logs ACCEPTED, and **appends the md5 to `sent_hashes.txt`**, after which every future run skips that report as "ALREADY SENT". Reproduced empirically (curl 8.5.0, exit 56, `last_response.txt` unchanged). | *"ACCEPTED"* on screen; the day never appears | Partially — the S198 health door goes warn at 26h / bad at 36h **if the owner opens the portal**. **The cure — deleting one line from `sent_hashes.txt` on the medical PC — is written nowhere.** Kept armed **on purpose**: it is the only medical-side fallback (D347; `S202_PENDENCY_AUDIT` X3) |
| **AF-2** *(CLOSED S201_A1FIX)* | **The save-time "does your total match Marg?" check had never fired once — born dead at S195.** The reader wanted `business_date`/`net_p`; the writer stored `date`/`expect`/`lines_csv`/`items_csv`. *"Indistinguishable from 'all days matched'."* The push-path test stub **fabricated the reader's key shape** — the fixture mirrored the reader, not the writer. | none, for five sessions | **Yes now** — plus the **never-fired witness**: any check that has not once left `ok` in 14+ days is named out loud |
| **AF-5** *(LOW · UNACCOUNTED FOR in any register)* | **The medical guard runs a different parser than the server while claiming byte-identity.** PC `28b47d44…` (S180) vs server `6411a57d…` (S193) — two builds apart. Failure direction is **closed**: an `.xlsx` the server accepts is REFUSED locally with *"file poori/theek nahi hai"* and reception re-exports fruitlessly. | a report refused locally with a misleading message | no. **`S202_PENDENCY_AUDIT` N2: "AF-5 is unaccounted for in any document I can reach."** See §4 — it is now a **four**-copy problem |
| **Fault A** *(CLOSED S201)* | `D:\MARG REPORTS` believed unwatched; **the sole reference doc was wrong on its own diagram.** An S201 code audit read `START_MARG_WATCHER.bat` (one folder) instead of the actual autostart `MargWatcher.cmd` (two). *"Trust the running process, not a script that may not be the one running."* | — | — |
| **Fault B** *(CLOSED S201 Part 0)* | **A signature added never rescued an already-indexed file.** `marg_router.py` blacklists by content md5 at line 249 *before* `open_sheet()` and `identify()`; `append_index()` opens in `"a"` mode with no update path. **Every signature added stranded whatever it should have rescued** — 11 reports frozen. | reports stuck in `_UNKNOWN`/`_REFUSED` | **Yes** — `marg_rescan.py --if-signatures-changed` runs in the 10-minute task, comparing `signatures.json` against `MargArchive\_signatures_seen.md5` |
| **Fault C** *(CLOSED)* | One header variant killed a whole report family permanently — six closing-stock exports refused for `['S.No.','Description','Total Stock','Unit']` | — | fixed by the `STOCK_CLOSING / TOTALS` signature |
| **Fault D** *(CLOSED S201 Part 1)* | **PDF/CSV structurally invisible, and silently so** — `EXTS = (".xls",".xlsx")` and `capture()` returned `False` **with no output**. Five real Marg PDFs sat in the mirror. | nothing at all | **Yes** — PDFs captured to `DOCUMENT_PDF` with `%PDF`/`%%EOF` checks, plus the heartbeat's **IGNORED** counter |
| **Fault E** *(CLOSED S201 Part 3)* | **Truncation checked only for sale reports** — `ends_with()` returns `True` when no `end_marker` is declared, and only `SALE_BILLWISE/DETAIL` declared one. *"A partial stock count is worse than none."* | a half-printed report filed `VERIFIED "structural"` | **Yes** — markers derived from real samples for all types, tested against 16 archived files before applying (16 pass, 0 refused), then all 26 re-verified |
| **Fault F** *(open by design)* | **Only `SALE_BILLWISE` is `uploadable`.** No purchase or stock report can reach the server at all — *"'reached the archive' ≠ 'reached the clinic'."* | — | by design until the Purchase Portal (D335) lands |
| **Fault G** *(CLOSED S201 Part 3)* | **A multi-day range export credited to `date_to` only** — a 01→15 Aug catch-up would count as 15-Aug with the other fourteen days reading MISSING, and if a newer single-day export existed the range would be marked superseded and **its earlier days never sent at all.** *"my code, my bug"*; it never bit only because the one range export spans a Sunday. | phantom missing days | fixed by `covered_days()`/`span_key()`; **the DATA range wins over the title range** |
| **Fault H** *(OPEN — B5)* | **The spool doubles as the dedupe memory and nothing is ever cleaned.** *"Emptying `_spool` re-imports everything."* And `_spool`/`_outbox` are excluded from the offsite. | a tidy-up silently re-imports the whole history | **NO** — nothing warns before someone empties it |
| **Fault I** *(CLOSED S201 Part 4)* | **Routing ran only if that run captured something** (`if do_route and new:`) — a routing run that died left files no later run would touch. | reports sitting unrouted indefinitely | fixed: route whenever the spool holds anything |
| **Fault J** *(OPEN — B4)* | **The medical guard sends anyway when Python is missing** — `GUARD_AND_SEND.bat` jumps to `:nopython` and sends with only a printed note. | — | no |
| **C5** *(OPEN, never minted)* | **The medical guard cannot run at all** — the bundled Python 3.11.9 has **neither `xlrd` nor `openpyxl`**. `xlsx_stdlib.py` would fix it and *"is not yet on that machine."* | — | no |
| **C6** *(OPEN, never minted)* | **A re-apply wipes that day's review queue** (`DELETE FROM sale_item_review WHERE ingest_batch_id=?`). *"Matters directly to the Docterz plan."* | resolutions silently discarded | **NO** |
| **C3 / C4** *(OPEN, never minted)* | C3: the approvals WALK-IN warning is **wrong twice** — it uses `marg_report`'s id count, which `finance_ingest` can overrule, and names WALK-IN when the destination is **review**. C4: **two parsers look for a clinic ID** (`marg_report` and `split_clinic_id`) — *"the same class `marg_net_sql` was created to end."* | a misleading count on the approvals page | no |
| **F-183** *(OPEN by choice)* | (a) the `0.60` tier **parks a bill that HAS a clinic ID but no name — backwards**, the ID being the strongest identifier; (b) `[A-Za-z]{0,3}\d{2,8}` needs 2+ digits, so **single-digit clinic IDs would not match** (the clinic's numbering started at 1). Neither occurs in the 192 bills measured. | — | no. Deliberately excluded: *"mixing a behaviour change into a labelling fix makes a rollback hard to reason about"* |
| **The `.xlsx` time bomb** *(manojz side OPEN)* | `xlrd 1.2.0` reads `.xlsx` only **below Python 3.9** (`ElementTree.getiterator` removed in 3.9). *"The day manojz's Python is upgraded, **every `.xlsx` Marg export becomes 'not a readable .xls'** — and it will look like a refusal, not a breakage."* Marg does emit `.xlsx`. Proven both ways in-session. | reports refused with a wrong reason | **NO — nothing watches the Python version.** `xlsx_stdlib.py` exists on manojz (`bbe11a89…`, verified) and `marg_router.open_sheet()` routes to it — but **a bundled `xlrd` folder still sits in `MargPull\`** |
| **The 401 token crisis** *(S195; rotation still OPEN)* | `FINANCE_MARG_TOKEN` had lived somewhere transient and a service restart killed the sender. Fixed durably in the systemd unit. **Both tokens transited chat on 21-Aug.** A manojz hand-copy went stale and *"had been answering 401 for five days while medical's own copy worked."* | `401`, which reads as *"not_signed_in"*, **not** *"bad token"* | the send log. **Rotation is the oldest and highest-severity open item in the project** |

---

# 4 · THE BLIND SPOTS — what nothing in the system can currently see

**This is the most valuable section, and the structural fact underneath all of it is one sentence:**

> *"Every server-side check watches **arrival at the VPS**. It cannot see the medical PC, manojz, the
> archive, or Drive."* — `S201_Marg_Pipeline_Rebuild_Plan` §1

B2 (S202) inverted part of that by having manojz **push** its own status. What follows is what remains
after B2.

### 4.1 · The record's own coverage table, as it stood at S201

| failure | coverage then | latency |
|---|---|---|
| medical watcher process dead | **NONE** | unbounded |
| manojz pull task dead | **NONE** | unbounded |
| generated but never sent | Marg-push freshness, warn 26h / bad 36h | 26–36h **+ time until someone opens the portal** |
| sent but rejected (401/500) | silence only — **no reject counter** | *"rejection never identified"* |
| exported as PDF | **NONE** — and the alarm that eventually fires **names the wrong cause** | — |
| mid-month day never generated | **NONE** while later days keep arriving | — |
| Drive offsite failing | **NONE** — the VPS cannot see Drive | unbounded |

B2 closed the first, second, third and (via `_coverage_from.txt`) the sixth; the ignored-file counter
closed the fifth. **Push-rejection counting and offsite verification are still B6/B-queue items, not
built.**

### 4.2 · The blind spots that remain — enumerated

1. **NO PC-SIDE LIVE PINS. THIS IS THE LARGEST ONE.** `verify_live_pins.py` runs on the VPS and
   *"cannot reach either PC"* (`S201_Medical_Pipeline_Completion_Audit` §8; **C7**, never minted;
   F-186 structural half, OPEN). It classifies PC rows **BLIND** and says so honestly. **Consequences
   measured this session:**
   - **`PULL_FROM_MEDICAL.bat` on manojz is `92f03999d0a14d00b7f552dbb4d44c05`; the Register pins it
     `3c5389d54241f234e94dc62b82d046e1`. A live, currently unrecorded drift — F-186's second
     instance, found the same way the first was.**
   - **Six live PC files have no canonical pin at all.** The KB Register's live-file table pins only
     `signatures.json`, `marg_gate.py`, `_coverage_from.txt`, `pipeline_status.py` and
     `PULL_FROM_MEDICAL.bat`. **`marg_router.py`, `marg_watch.py`, `marg_rescan.py`,
     `xlsx_stdlib.py`, `medical_inventory.py` and `medical_agent.py` are pinned only inside S201
     session records** — documents, not the register anything checks. (Their values *do* match the box
     — verified in §1.2 — but nothing would ever notice if they stopped.)

2. **The repository mirrors of the Marg tooling are stale, and nothing compares them.** Measured this
   session in `D:\dr-manoj-git\drmanoj-clinic-automation\`:
   | repo file | repo md5 | live manojz md5 |
   |---|---|---|
   | `margpull/marg_router.py` | `e5418830134f9c354fd40da4acf25d79` | `bbc50f9172211925755eeaa25920d1cf` |
   | `margpull/marg_watch.py` | `25126388e6841ab38202811d2b940d6a` | `2076fe1d8d145524be16ae857b3d838d` |
   | `margpull/medical_watcher/marg_watch.py` | `25126388e6841ab38202811d2b940d6a` | (medical runs `aa55cdb5…`) |
   | `margpull/PULL_FROM_MEDICAL.bat` | `15da9d27a0827bc3b806417e3d74c629` | `92f03999d0a14d00b7f552dbb4d44c05` |
   | `margpull/signatures.json` | `3e9cbba02ffb4e0f131738eee7a465f7` | same ✅ (synced at S202, F-186) |

   **`25126388…` is named in `S201_Part1_Capture_And_Agent_Record` §5 as "the OLD watcher"** —
   `EXTS = (".xls", ".xlsx")`, i.e. the version that cannot see PDFs. **Both repo copies are that
   version.**

3. **Five live tools have NO copy in the repository at all.** Verified by `find` this session:
   `marg_rescan.py` · `xlsx_stdlib.py` · `medical_inventory.py` · `medical_census.py` ·
   **`medical_agent.py`** (the medical-PC supervisor, S201.11 `69e60d778ab61a8d50c79394e2951309`).
   **If manojz's disk died today, the quarantine-rescue tool, the stdlib `.xlsx` reader that replaced
   a deleted dependency, and the medical PC's entire supervisor would have to be rewritten from
   session transcripts.** This is D350 §4's central claim, and it is measurably true.

4. **AF-5 is a FOUR-copy problem, not three.** `marg_report.py` measured this session:
   `D:\Downloads\margsync\MargPull\marg_report.py` = `28b47d44…` (manojz) ·
   `repo/finance/marg_report.py` = `28b47d44…` · `repo/deploy_kits/S195_MARG/marg_report.py` =
   `28b47d44…` — **all three the S180 parser** — against the server's `6411a57d…` (S193). Plus the
   medical PC's copy. B4 ("one parser, not three") is understated.

5. **`C:\Users\Public\MARG\` appears NOWHERE in either corrected Marg reference.** Verified by
   literal grep this session: the string occurs **twice** in `KB_History_Archive_v1_49_S202.md`
   and **once** in `CANONICAL_MANIFEST.md` (both inside the D347 narrative), and **zero times** in
   `MARG_PIPELINE_REFERENCE_v1.md` and `MARG_PIPELINE_MAINTENANCE_FLOW_v1.md`. Yet the manifest's own
   Tier-1 row for the reference describes it as covering *"the two Marg output trees (D: and **C:**)"*.
   **The manifest's description of the canonical reference is false, and the second output tree — the
   one that caused the S201 blind spot — is documented only in history.** A new engineer following
   the pointers would not learn it exists.

6. **`MEDICAL_RECENT.bat` scans D: only.** *"It cannot see Marg's C: tree, which is exactly where the
   blind spot was. It needs a local variant that runs on the medical PC"* — queued as **B7**, unbuilt.
   The same is true of the census and the ignored-file counter as originally built: *"all three would
   have answered 'nothing' with complete confidence."*

7. **The pending-send queue has no offsite copy.** `_spool` and `_outbox` are excluded from the
   `robocopy` to Drive. A manojz disk failure loses whatever is queued but not yet delivered.

8. **Nothing warns before `_spool` is emptied.** It is the dedupe memory; emptying it re-imports
   everything. Tidying is *"likely"* (S201 audit, Fault H) — and `_to_delete\` exists precisely
   because the owner tidies.

9. **No push-rejection counter.** *"Sent but rejected (401/500): silence only… rejection never
   identified."* A 401 storm after a token rotation would be visible only in the send log.

10. **No offsite verification.** Nothing compares the newest archive file against the newest file in
    the Drive mirror — **B6, unbuilt.** *"Drive silently stopped"* remains invisible. The Diagnostics
    spec parked this as un-buildable.

11. **Deep verification exists only for sale reports.** Purchase and stock get structure and an
    `end_marker` but no arithmetic reconciliation — **B3, unbuilt.** The natural first check is
    already known: `PURCHASE_BILLWISE` and `PURCHASE_SUPPLIERWISE` both total **476,393** for July,
    *"two independently generated reports agreeing to the rupee."*

12. **Identifier capture is invisible unless someone goes looking.** 73% for the week; **57% on 21-Aug
    against 92% on 22-Aug** — *"staff behaviour, not a formatting fault."* ₹54,547, **28.3% of
    turnover**, unidentified. **IDCAP** (put it on the health page) is queued, unbuilt.

13. **The `.xlsx`/Python-version dependency is unmonitored.** Nothing checks manojz's Python version,
    and the failure would present as a refusal, not a breakage.

14. **AF-1's cure is undocumented.** The health door caps the silent window at ~1–1.5 days, but
    *"nothing anywhere explains that the cure is deleting the hash line from `sent_hashes.txt`"*, and
    re-running `GUARD_AND_SEND` resends nothing because the local skip fires on the same bytes.

15. **The AF-# series has no bridge to the F-# register.** *"AF-1, AF-2, AF-3, AF-4, AF-6 appear zero
    times in the Fault Register"* (`S202_PENDENCY_AUDIT` N2). **Six S201 faults — C3, C4, C5, C6, C7,
    C8 — were never minted at all** (N1). **A fault that exists only in a backlog document is not
    tracked by anything.**

16. **`SYSTEM_DOC_COVERAGE_MAP_S147` has no row for the medical PC, manojz, Marg capture, clinic-finance
    or the Lab PC.** *"The document whose job is 'where is the reference for tool X' cannot answer for
    the systems you use daily"* (N6). It predates the entire estate.

17. **Nothing watches project-knowledge headroom, and nothing watched the canon folder.** Related in
    kind: the manifest records project knowledge hitting **98% of its ceiling** at the S202 close with
    *"nothing watching the limit."*

18. **The largest blind spot of all is in §6: Marg's own data.** Everything above protects *exports*.
    Nothing protects the pharmacy database they come from.

---

# 5 · D350 AS THE OWNER SCOPED IT

**Status: contract WRITTEN, SCOPED by the owner, NOT YET BUILT.** He read it and took the
counter-argument the contract itself recorded in §8: *"verification, visibility, correct documents and
a reinstall kit — **no second transport**."* **§1, the Drive fallback, is PARKED at his ruling**
(`KB_History_Archive_v1_49_S202` §S202; `OWNER_TODO_LIVE` ⭐1 item 2).

His reasoning was recorded as better than the contract's own proposal, and the decisive risk was named
honestly: **"a standby route never exercised will not work when needed."**

The contract's build order (§7) survives the scoping: **§5 documents → §2 verification → §3 the B2
states → §4 the kits.** *"Every step before the last is observation."*

---

## 5.1 · §2 — VERIFICATION AT BOTH ENDS, MEASURED NEVER INFERRED

> The rule it comes from: *"on 26-Aug both endpoints were healthy and the link between them was dead.
> Two green lights either side of a broken wire."*

**The medical agent must report** (into the heartbeat, *"which travels by Drive and therefore survives
a Tailscale failure"*):

| item | exists today? |
|---|---|
| its own file hashes | ✅ **EXISTS** — S201.11/F-180; the agent hashes the running file against the Drive copy and prints the drift and the fix path |
| Tailscale running / logged in / **its current address** | ❌ **TO BUILD** |
| whether **`DDrive` is still shared** | ❌ **TO BUILD** — this is the exact thing that failed on 26-Aug |
| power and session state — boot time, **sleep and wake gaps**, who is logged in, since when, **and whether it is an RDP session** | ❌ **TO BUILD** |

**manojz must report** (into the B2 status):

| item | exists today? |
|---|---|
| pull liveness, outbox **drain** state, watcher, ignored files, offsite lag | ✅ **EXISTS** — `pipeline_status.py` `51cf10c9…`, 15 selftest checks, called from **every** exit path |
| its own Tailscale state and address | ❌ **TO BUILD** |
| **an actual reachability test of the share, performed, not deduced** | ⚠️ **PARTIAL** — the pull pings and diagnoses guest-access itself from S202 (F-193). Whether that result reaches the B2 payload is **not established** from the record; the S202 records describe the pull *printing* it |
| **which transport this cycle used** | ➖ **MOOT while §1 is parked** — there is one transport |
| **whether any credential for the medical host exists at all** | ❌ **TO BUILD** — and this is the highest-value single item in §2, because the 26-Aug fault was precisely a missing credential |

**Plus, called out separately in §2 and still owed:**
- ❌ **A changed Tailscale address must be visible the moment it changes, not eight hours later.**
- ❌ **`PULL_FROM_MEDICAL.bat` hardcodes the address `100.119.151.40`.** *"The durable fix is the
  Tailscale MagicDNS name, so the number can never be the fault again."* **TO BUILD.**

## 5.2 · §3 — THE B2 STATES

Three new owner-visible states on the health page:

| state | shown as | exists today? |
|---|---|---|
| **Tailscale, both ends** — address, up/down, and **when each was last confirmed** | — | ❌ **TO BUILD** (depends on §2) |
| **Which point is down** — *not "the pipeline failed" but "the PC answers, the share refuses — most likely credentials"* | — | ❌ **TO BUILD**. The pull says this on its own console; **the health page does not** |
| **Running on the FALLBACK** | **`warn`, and it stays `warn` for as long as it is true** | ➖ **MOOT while §1 is parked.** *Its reasoning is not moot and should be kept:* **"A fallback nobody notices becomes the new normal… Working by the reserve route is a degraded state, and it must read as one."** The same argument applies to running on the manual sender |

**What §3 already has to build on** — B2A/B2C, live at S202: `POST /finance/api/pipeline-status`,
**token-scoped reusing `FINANCE_MARG_TOKEN` — "no fourth secret to rotate"**; tables `pipeline_status`
+ `health_check_seen`; six checks; an **hours-aware `medical` reachability check** (bad in clinic
hours, info outside — *"alarming all night about a PC meant to be off is how a light stops being
read"*); and **the never-fired witness**. Live smoke **719/719**.

> *"This extends B2. It does not replace it."*

## 5.3 · §4 — THE REINSTALL KITS · **"the part that matters most"**

> *"**Neither PC could be rebuilt today from anything written down.** Everything that carries pharmacy
> revenue lives on two machines, and the knowledge of how to recreate them lives in session
> transcripts."*

**The owner's ordering, recorded at the S202 close: "the reinstall kits (Marg and its data first)"**
(`OWNER_TODO_LIVE` ⭐1 item 2).

**Every kit must state:** what to install and in what order · which files go where, **with their
md5s** · which credentials are needed and how to store them — **never the values, which are the
owner's alone** · the scheduled tasks and **the account each must run as** · **the checks that prove
it worked**. *"It must be rehearsed, not merely written. A recovery document nobody has followed is a
guess."*

### Kit A — the MEDICAL PC (and Marg first, per the owner)

| item | exists? |
|---|---|
| **Marg ERP itself and its data** — install, licence, the `d1-sanjeevni-*` company files, **and a restore procedure** | ❌ **NOTHING WRITTEN.** See §6 — this is ⭐0a |
| Windows account **and its password requirement** (`MEDICAL\SET` has one; `MEDICAL\user` has none) | ⚠️ facts recorded in the maintenance flow; **not assembled as a kit** |
| the `DDrive` share and its permissions | ❌ |
| Tailscale | ❌ |
| Drive for Desktop (and that it mounts as **`F:`** here) | ⚠️ recorded in S201 Part 1 §2; not in a kit |
| portable Python `D:\SendToClinic\pyportable\` (3.11.9) | ⚠️ the **standard** is canonical (*"bundled `pyportable`, called by full path, never a system install"* — F-167); **the bytes are not in the repo** |
| `marg_watch.py` | ⚠️ repo copy is the **OLD** `25126388…` |
| **`medical_agent.py`** | ❌ **NOT IN THE REPO AT ALL** |
| **`xlsx_stdlib.py`** | ❌ **NOT IN THE REPO AT ALL** |
| the scoped token `D:\SendToClinic\token.txt` | ➖ value is the owner's; the *fact* and its three copies are documented (`MARG_PIPELINE_REFERENCE_v1` §4) |
| the Startup entry `MargAgent.cmd` | ⚠️ the S195 doc gives `MargWatcher.cmd`'s exact text; the **agent** entry is described, not transcribed |
| **the checks that prove it worked** | ⚠️ the 60-second check exists and is excellent; it is not yet written as a *post-rebuild acceptance test* |

### Kit B — manojz

| item | exists? |
|---|---|
| Tailscale | ❌ |
| Drive for Desktop (mounts as **`H:`** here) | ❌ |
| the `MargPull` folder | ⚠️ **partial and stale** — repo has `marg_router.py` (stale), `marg_watch.py` (old), `PULL_FROM_MEDICAL.bat` (stale), `signatures.json` (current ✅); `marg_gate.py` and `pipeline_status.py` exist only inside `deploy_kits/S202_PICTURE/` and `deploy_kits/S202_B2B/`; **`marg_rescan.py`, `xlsx_stdlib.py`, `medical_inventory.py` are nowhere** |
| **the stored credential for the medical host** | ⚠️ the `cmdkey` command is documented by symptom (`MARG_PIPELINE_MAINTENANCE_FLOW_v1` §2); **not in a kit, and the per-user storage rule is the trap** |
| the scheduled task **and its Run-As account** | ⚠️ documented as a diagnosis step (`schtasks /query … | findstr /i "Run As User"`); not as a build step |
| the `margsync` folder layout | ✅ **DOCUMENTED WELL** — `MARG_PIPELINE_MAINTENANCE_FLOW_v1` §4 gives every folder, what it is, and whether it is safe to empty |
| **`MargArchive\_coverage_from.txt`** — the declared coverage start (`2026-08-17`) | ✅ exists on the box and in `deploy_kits/S202_PICTURE/`; **a rebuild that omits it silently falls back to a 45-day horizon** |

**One structural hazard for §4, from F-190:** the cold kit exists so the canon can be restored, and
until S202 *"restored onto a default Windows machine it would fail its own verification entirely."*
`.gitattributes` now pins `*.md`. **The reinstall kits must be tested on a machine with git's Windows
defaults, not on manojz** — manojz has `autocrlf=false`, *"one machine-local setting nothing records
or checks."*

## 5.4 · §5 — DOCUMENTS · *"done at S202 — verify, don't redo"*

| owed correction | status |
|---|---|
| D347's "Tailscale is NOT load-bearing" corrected in `MARG_PIPELINE_REFERENCE_v1` §1/§5 | ✅ **DONE** (verified: the correction is in the file, and its hash matches the manifest) |
| …and in `MARG_PIPELINE_MAINTENANCE_FLOW_v1` | ✅ **DONE** — §2a is a dedicated correction section |
| **…and in the decision record** | ❌ **NOT DONE.** `KB_Register_v5_54_S202`'s D347 entry still reads *"Tailscale is a read-only D:-only view and is NOT load-bearing"* |
| the guest-access failure and its `cmdkey` remedy added **by symptom** | ✅ **DONE** — `MARG_PIPELINE_MAINTENANCE_FLOW_v1` §2, *"The pull says unreachable but the medical PC is ON"* |
| **credentials are stored per Windows user** → the task's Run-As account | ✅ **DONE** — same section, step 4 |
| *(not in §5, but owed and outstanding)* the C: output tree in the reference | ❌ **MISSING** — see §4.5 |

---

# 6 · WHAT THE RECORD SAYS ABOUT BACKUP OF MARG AND THE MEDICAL PC

**This is the least-protected part of the entire estate, and the record says so plainly.**

## 6.1 · ⭐0a — the owner's own live to-do, quoted in full

From `OWNER_TODO_LIVE.md`, refreshed at the S202 close (26-Aug-2026):

> ## ⭐0a — THE BACKUP (F-191c) — the crown jewels, and the first job next session
>
> Everything we have built is downstream of Marg. **Marg holds the actual pharmacy.**
>
> - Backups are **manual**, every 2–4 days, to `E:\` (an HP USB 2.0 stick permanently attached to the
>   medical PC). **Last: 22-Aug.**
> - **`E:\auto` and `E:\MARGBCKUP\auto` have been EMPTY since October 2025.** Automatic backup was
>   configured and **has never once run**, while a human quietly filled the gap by hand.
> - The old financial year (`d1-sanjeevni-20250401-20260331`) was last backed up **17-July**.
> - **All 308 MB sits on one drive attached to the machine it protects** — fine against a dead disk,
>   useless against fire, theft or ransomware.
> - **No restore has ever been tested.** Eleven months of files nobody has opened.

**Note the drive letter and the machine:** `E:\` is **on the MEDICAL PC**. It is a USB 2.0 HP stick,
permanently attached.

## 6.2 · F-191(c) — the register entry, quoted

`Fault_Action_Register_v2_41.md`, F-191, status *"S202 · two instances CLOSED · **the eleven-month one
is the OWNER'S to close**"*:

> **(c) `E:\auto` and `E:\MARGBCKUP\auto` on the medical PC have been EMPTY for eleven months**:
> automatic Marg backups were configured around 02-Oct-2025 and have never once run, while a human
> filled the gap manually every 2–4 days. **RULE: a facility that is configured but never confirmed
> producing output is not configured — it is decoration.** AF-2 was the same shape and showed green
> for five sessions.

## 6.3 · The Archive's account of how it was found

`KB_History_Archive_v1_49_S202.md` §S202, *"What the owner's own questions found"*:

> Every one of the following came from him using the system, not from any test: … **and the
> eleven-month-empty `E:\auto` folder where automatic Marg backups were configured in October 2025 and
> have never once run.**

## 6.4 · The owner's action, as set at the S202 close

`OWNER_TODO_LIVE.md` ⭐0 item 9:

> **ASK MARG SUPPORT TWO THINGS**, in one message: (a) can `margwin.exe` be told to generate or export
> a specific report from the command line? **(b) why does the configured automatic backup produce
> nothing? — see F-191(c) below.**

`OWNER_TODO_LIVE.md` ⭐1 item 1 — **the first thing Claude builds next, in the owner's stated order:**

> **The pen-drive backup (⭐0a)** — find why the automatic backup produces nothing, get it to daily,
> add an offsite leg via Drive, and **test one restore**.

## 6.5 · The retention policy — what it covers, and the line where it says this is NOT it

`Clinic_Source_Data_Retention_Policy_v1.md` (S195, **still a draft for owner approval**) covers *"the
raw export files these systems produce (the source documents behind the books), not the books
themselves."* Its §6 is the load-bearing paragraph:

> ## 6. What this policy does NOT cover — and matters more
> `finance.db` **is the books**; the exports are only the source documents. Its backup is a separate
> and higher-priority concern… Worth confirming separately: that it runs, where it writes, and that a
> restore has actually been tested. **An archive of exports is no substitute for a database backup.**

**The same sentence applies one level further up, and the policy does not say it: an archive of
exports is no substitute for a backup of Marg.** The policy never mentions Marg's own database. Its
only reference to the `.dbf` layer is elsewhere — Archive §S195 §6 records *"the Marg `.dbf`
encryption finding + partial key"* as a filed document, not as a backup route.

**Its three-copy model, quoted:**

| Copy | Where | Role | Kept |
|---|---|---|---|
| Origin | medical PC `D:\SendToClinic\Sent\` | what the sender archived | current FY, then purge |
| Working | manojz `D:\MargArchive\` | content-named, inspectable, re-ingestable | current FY loose |
| Durable | Google Drive | offsite, survives both PCs | 8 years, monthly zips |

Its §4 rules: **source exports 8 years** (*"they are the only re-ingestable record — the VPS keeps
nothing, so a day can only ever be rebuilt from these or from Marg"*) · `index.csv` **permanently** ·
current FY loose · closed FYs one zip per month per source · **`_spool` purge after 7 days** ·
`_REFUSED`/`_UNKNOWN` review then purge after 90 days · medical `Sent\` purge at FY end. And its
caveat: *"**Not tax advice.** … **Confirm the retention period with your CA.**"*

**⚠ Three things in this policy no longer match reality, and it is still labelled a draft:**
1. It puts the working copy at **`D:\MargArchive\`**; the live archive is **`D:\Downloads\margsync\MargArchive\`**.
2. Its §3 mechanism — *"Put `D:\MargArchive` **inside** a Google Drive for Desktop synced folder…
   no monthly upload job to remember, no extra script to maintain. **This is the single highest-value
   step**"* — **was not what was built.** The archive is `robocopy /E`'d to `H:\My Drive\Clinic Data
   Archive\MargArchive` by the 10-minute pull. The outcome is similar; the mechanism is different, and
   `robocopy` **excludes `_spool` and `_outbox`**, which a synced folder would not have.
3. It names `D:\SendToClinic\Sent\` as the medical origin copy. The live medical spool is
   `D:\SendToClinic\_captured\`. Whether `Sent\` exists today is **not established** — it is not
   mentioned in `MARG_PIPELINE_REFERENCE_v1` or the maintenance flow's folder table, and this session
   did not read the medical PC.

## 6.6 · What IS backed up, and proven

- **The clinic canon.** Cold kit **TAKEN at the S202 close** and, per `OWNER_TODO_LIVE`
  §HOUSEKEEPING, **for the first time restore-tested**: *"extracted to a clean directory, `md5sum -c`
  exit 0, 214 OK"* —
  `D:\dr-manoj-git\cold_kits\DrManoj_Clinic_FULL_Handoff_Session202_2026-08-26.zip`.
  *(F-89 is why this cadence exists: a nine-session lapse permanently lost three canonical documents.)*
- **`finance.db`.** Archive §S195 §6: *"backups proven — cron `5 1 * * *`, verified nightly, **restore
  proven** (126 days, 3,141 items)."* `finance_backup.sh` is pinned in the Register.
- **The Marg export archive.** Continuously offsited to Drive, append-only, no purge — **except
  `_spool` and `_outbox`.**
- **The medical PC's exports.** Mirrored to manojz every 10 minutes (`medical_SendToClinic\`,
  `marg_reports_mirror\`) — **D: only.**

## 6.7 · The honest summary of the backup position

| what | protected? |
|---|---|
| the clinic canon (documents) | ✅ git + cold kit, **restore-tested once**, S202 |
| `finance.db` (the books) | ✅ nightly cron, **restore proven**, S195 |
| Marg **exports** (the source documents) | ✅ manojz + Drive offsite, append-only — **minus the pending-send queue** |
| **Marg itself — the live pharmacy database** | ❌ **manual, every 2–4 days, to one USB stick attached to the machine it protects. Automatic backup configured Oct-2025 and never once run. No restore ever tested. Last backup 22-Aug; the previous FY last backed up 17-July.** |
| the medical PC's software estate (agent, watcher, portable Python, tasks) | ❌ **partially absent from the repository entirely** — see §4.3 |
| manojz's Marg tooling | ⚠️ **partially in the repo and stale**; three tools nowhere — see §4.2/§4.3 |

**Every rupee in the books is downstream of a database whose only backup is a manual copy onto a USB
2.0 stick plugged into the same computer.** That is the record's own position, in the owner's own list,
and it is item 1 of what he asked to be built next.

---

# 7 · EVERY CONFLICT FOUND IN THE RECORD

Presented with both sides and which document is newer.

| # | conflict | newer / authoritative |
|---|---|---|
| **C-1** | **Tailscale load-bearing.** D347 (S201, in `KB_Register_v5_54_S202` and `CANONICAL_MANIFEST.md`): *"a read-only D:-only view and **NOT load-bearing**."* — `MARG_PIPELINE_REFERENCE_v1` §1 + `MARG_PIPELINE_MAINTENANCE_FLOW_v1` §2a (S202): *"**AND IT IS LOAD-BEARING… that is WRONG and 26-Aug-2026 proved it.**"* | **The S202 references are newer and correct.** D350 §5 lists the decision-record correction as owed; it is **still not made** in the Register's D347 entry |
| **C-2** | **Which document is the reference for Marg capture.** `MARG_PIPELINE_REFERENCE_v1` opens: *"Supersedes `S195_Medical_Watcher_LIVE_Reference.md` as the authoritative description."* — `CANONICAL_MANIFEST.md`'s Tier-1 row still calls S195 *"**SOLE reference for the Marg capture pipeline**."* **Both are Tier-1 CURRENT.** | The S201/S202 reference is newer. Raised as **N3** at S202 and **still unresolved at the S202 close** — verified in the manifest this session |
| **C-3** | **`ingest.min_confidence`.** `MARG_INGESTION_REFERENCE_v1` §9 item 5: *"Whether 0.70 is right here is an **owner decision**, not a code one."* — **D348**, minted hours later the same session: *"closed by **MEASUREMENT**, not owner judgement"* — 192 bills, every one 0.95+ or 0.50, *"a has-ID switch imported from OCR into a path with no OCR."* | **D348 is newer and wins.** The manifest flags it (*"filed as delivered rather than silently edited (F-23); the discrepancy is flagged for the owner's ruling"*). **`S201_PARKED_BACKLOG` A3 and `S201_Month_vs_Marg_Explained` still carry the retired question** |
| **C-4** | **The C: output tree.** `CANONICAL_MANIFEST.md`'s Tier-1 row: `MARG_PIPELINE_REFERENCE_v1` covers *"the two Marg output trees (D: and **C:**)"* — **the document contains the string `C:\Users\Public\MARG` zero times** (grep, this session). | **The manifest's description is false.** The tree exists only in Archive §S201 and the D347 narrative |
| **C-5** | **`PULL_FROM_MEDICAL.bat`.** Register v5.54 pins `3c5389d54241f234e94dc62b82d046e1` — **the box holds `92f03999d0a14d00b7f552dbb4d44c05`** (measured this session). | **The box wins** (D321(d), F-169 precedent). A live F-186 instance; cause not established |
| **C-6** | **The repo `margpull/` mirror vs the live tooling.** Repo `marg_router.py` `e5418830…`/`marg_watch.py` `25126388…` vs live `bbc50f91…`/`2076fe1d…`. `25126388…` is explicitly *"the OLD watcher"* per `S201_Part1_Capture_And_Agent_Record` §5. | **The box is live; the repo mirror is stale and unrecorded** |
| **C-7** | **Retention policy vs reality (three ways).** Working copy at `D:\MargArchive\` (live: `D:\Downloads\margsync\MargArchive\`) · the *"single highest-value step"* of putting the archive **inside** a Drive-synced folder (built instead as `robocopy`, which **excludes `_spool`/`_outbox`**) · medical origin `D:\SendToClinic\Sent\` (live spool: `_captured\`; `Sent\` existence **not established**). | The pipeline references (S201/S202) are newer. **The policy is still labelled "draft for owner approval" and has never been reconciled** |
| **C-8** | **PC-side pins across S201's own records.** `marg_router.py` reads `d63045b1…` in `S201_Part1_…`, `bbc50f91…` in `S201_Parts2_3_4_…` and the completion audit. `PULL_FROM_MEDICAL.bat` reads `d4af22f6…`, `090c553a…`, then `d64b636b…` across the same three. | **Successive within-session states, not contradictions** — but only the *last* is traceable, and **none of these files is in the KB Register's live-file table at all.** Recorded so a future reader does not mistake the sequence for drift |
| **C-9** | **F-96 / F-185 / D320.** F-96 (S181): *"7 unmasked mobiles, ≥2 names, 1 clinic ID across 48 files"*; **D320 ruled the repo may stay public on that evidence.** F-185 (S202 open): *"133 distinct mobile-shaped numbers across ~190 files"* + *"13 named patients with… DIAGNOSIS."* **F-185 CORRECTED at the S202 close: "THE CENTRAL CLAIM WAS FALSE"** — `.gitignore` had always excluded them, *"not one `.csv` is tracked"*; the scanner *"walked the FILESYSTEM instead of asking git."* Measured properly: **62 mobile-shaped numbers, no diagnoses, ever.** | **The correction is newest and authoritative.** *"F-96 was right all along, at roughly ten times its recorded count, without the category that made it alarming."* Relevant here because **three copies of `marg_report.py` carry name+mobile+clinic-ID selftest fixtures, and were deliberately left untouched** to avoid manufacturing record-vs-reality drift. **The D320 re-ruling is the owner's** |
| **C-10** | **The watcher's watch roots.** `MARG_PIPELINE_REFERENCE_v1` §1 shows **two** (`D:\MARGERP\users`, `D:\MARG REPORTS`) — `S201_Medical_Pipeline_Completion_Audit` §2 says the live watcher watches **three**, adding `C:\Users\Public\MARG`. | **Three is correct** (S201.7 added it, same day, later). The reference was written earlier that day and never updated. **A reader of the canonical reference alone would not know a whole output tree is being captured** |
| **C-11** | **AF-1's status.** `S201_Marg_Outbox_Never_Drained_Finding` §6 proposes replacing the medical sender's human click entirely — *"which is the actual defect."* D347 rules the manual sender *"stays as the fallback and is never removed"* with AF-1 *"armed on it deliberately."* | **D347 is newer and is the ruling.** Not a contradiction, but a reader of the S201 finding alone would think AF-1 was on a path to removal. **It is not** |

---

## 8 · THE SHORTEST TRUE SUMMARY

- **The medical PC generates everything and is protected by the least.**
- **manojz does everything else, alone, and half its tooling exists nowhere but on its own disk.**
- **The VPS can see nothing on either machine except what manojz chooses to tell it every ten minutes.**
- **One link — Tailscale SMB — carries every report, and there is no second one by the owner's own
  deliberate ruling.**
- **The one thing nothing protects is Marg's own data.**

---
*S203 · built from the canonical record; every canonical document hash-verified against
`CANONICAL_MANIFEST.md` before being quoted. Live md5s in §1.2 and §4 were computed read-only on
manojz this session and are labelled as such. No patient identifiers reproduced; no tokens read or
printed. Nothing was modified.*
