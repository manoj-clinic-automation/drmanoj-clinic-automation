# S180 — Marg ERP Live Data Folder Reconnaissance

**Session:** 180 (follow-on to S179 — Sanjeevni finance module daily pharmacy-sale feed)
**Date of survey:** 2026-08-15, ~13:55–14:05 IST
**Machine:** Windows device `medical` (win32 x64), accessed read-only via the Claude desktop device bridge
**Target:** `D:\MARGERP` (Marg ERP live installation + live data)
**Company in data:** `SANJEEVNI MEDICOS`

**Compliance note:** Nothing under `D:\MARGERP` was created, renamed, moved, modified or deleted. All work was done on read-only copies staged into an isolated cloud container. No patient names, no full phone numbers, no passwords and no licence keys appear anywhere in this document. Files known to hold credentials (`System\margsqlconnection.ini`, `System\licenceinfo.ini`, `System\licence.ini`, `System\mysqlflp.ini`) were deliberately **not** copied or opened.

---

## 0. Headline result — read this first

**The live Marg data files are NOT directly readable.** They are Visual FoxPro DBF tables wrapped in Marg's proprietary byte-obfuscation. `dbfread` and every other standard DBF reader fails on the first byte.

Consequences for the S179 plan:

| Recon task | Outcome |
|---|---|
| 1. Map folder / find DATA dir | ✅ Done — see §2, §3 |
| 2. Identify format (DBF or not) | ✅ Done — **encrypted DBF**, see §4 |
| 3. Read ACGROUP fields + rows; SALETYPE/DIS field lists | ❌ **Blocked by encryption** — see §5 |
| 4. Identify daily sale-bill table + fields + date range | ❌ **Blocked by encryption**; strong inference recorded in §6 |
| 5. Sidecars / config / Marg version | ✅ Done — see §7, §8 |
| 6. Write-up | ✅ This document |

**Recommended pivot:** Marg's own **Tally XML export is plaintext and already in use on this machine** (`D:\MARGERP\daybook.xml`, 791 vouchers, bill numbers, dates, amounts, party ledgers). That, or Marg's SQL-sync feature, is a far cheaper and far more supportable feed than breaking the file encryption. See §9 and §10.

---

## 1. Method and read/lock behaviour (important — Marg was RUNNING)

Marg was **live and actively writing** throughout the survey. `probat.c18`, `glmonth.c18`, `pro.c18`, `support.c18`, `mewsale.c18` all had mtimes inside the survey window (14:00 IST), and `serverlog.fpt` / root `company.ini` were being appended to in real time.

Observed behaviour:

- **Reads succeeded on a live, running Marg.** 18 of 19 requested table copies succeeded first time, including the two largest live tables (`dis.c18` 12.6 MB, `mdis.c18` 6.7 MB). VFP does not take an exclusive whole-file lock on shared tables.
- **One transient failure:** `Data\mewsale.c18` failed with `upload failed` on the first attempt at 13:59 IST (Marg wrote to it at that exact second), and **succeeded on retry** ~2 minutes later. So: expect occasional transient failures on hot tables; retry-with-backoff is sufficient, an exclusive lock is not the failure mode.
- **Copy-before-read is still the right discipline** for any future parser: snapshot to a scratch directory, parse the snapshot, never hold a handle on the live file.
- One file listed in the directory could not be requested at all: `Data\mewslast.c18` does not exist in the C18 set (it exists for C13–C17 and D01). Not an error — a genuine absence.

---

## 2. Folder map — `D:\MARGERP` (root)

37 subdirectories, ~250 files in the root itself. This is a standard Marg ERP 9/10-series VFP9 runtime directory (`VFP9R.DLL`, `VFP9T.DLL`, `VFP9RENU.DLL` present).

**Subdirectories:**
`&reportpath`, `awacs`, `awacsfiles`, `backtemp`, `checkcarbpath`, `CONTENT`, **`Data`**, `ebusiness`, `Ede`, `emailpend`, `emailserver`, `export`, `files`, `Fonts`, `graphtool`, `GSTRETURN`, `IMAGES`, `ims`, `imsfiles`, `marghelp`, `Method`, `myscreen`, `netorder`, `offlineorder`, `operator`, `Others`, `payment`, `photo`, `Reports`, `serverbackup`, `System`, `Temp`, `users`, `usertemp`, `VAT`, `x64`, `x86`

Spot-checked and **empty**: `export`, `ims`, `Reports`.
`Others` = 24 chart GIFs only. `ebusiness` = `39548`, `39548photo`, `community` subfolders.

**Root file groups of interest:**

| File | Size | mtime (IST) | Note |
|---|---|---|---|
| `margwin.exe` | 13,921,280 | 2025-09-24 12:27 | Main VFP9 executable. No VERSIONINFO resource (PE timestamp is a stale 2007 VFP stub) — version not readable from properties. |
| `server.exe` | 793,600 | 2025-09-24 12:27 | Marg background server |
| `CONFIG.FPW` | 156 | 2025-09-30 | **Plaintext** — see §7 |
| `company.ini` | 2,062 | 2026-08-15 13:59 | **Encrypted** table (live) |
| `customerinfo.ini` | 5,283 | 2026-08-15 | Encrypted table |
| `marguser.csv` | 3,017 | 2026-04-21 | **PLAIN, UNENCRYPTED DBF** — see §7 |
| `marguser.fpt` | 27,392 | 2026-08-15 | Memo file for the above |
| `serverlog.fpt` / `serverlog.ini` | 768,569,536 / 94,617 | 2026-08-15 13:59 | Live server log table + memo. 768 MB memo file — worth flagging to the user separately. |
| `margexit.fpt` / `.ini` | 68,591,232 / 39,569 | 2026-08-15 | Exit-screen ad cache |
| `up_margtemp.dbf` + `.fpt` | 472 / 512 | 2026-08-15 14:01 | Encrypted despite the `.dbf` extension |
| `daybook.xml` | 1,205,131 | **2026-07-12 12:32** | **PLAINTEXT Tally daybook export** — see §9 |
| `master.xml` | 1,661,807 | 2026-07-28 20:39 | Plaintext Tally master export |
| `transactions.xml` | 10,435,250 | 2026-07-28 20:39 | Plaintext Tally transaction export |
| `master 2025 26.xml` | 562,472 | 2026-07-09 12:50 | |
| `TALLY APR MAY 26.xml` | 8,054,405 | 2026-06-11 20:30 | |
| `TALLY MARCH 26.xml` | 4,672,733 | 2026-06-11 20:38 | |
| `TALLY APRIL MAY.xml`, `TALLY MARCH.xml` | 1.6 MB / 3.2 MB | 2026-06-11 | |
| `pfapi443.dll`, `pfapi445.dll`, `pfdapi500.dll`, `pfdapi540.dll`, `pfdapi570.dll`, `pfdapi584.dll` | 77–82 KB | latest 2026-08-15 13:56 | Marg's data-access/obfuscation layer. Numeric suffixes look like build numbers; `pfdapi584` is the newest and was touched today. **This DLL family is almost certainly what implements the file encryption.** |

**Key naming convention discovered:** Marg stores DBF tables under *non-DBF extensions*. A `.ini` file paired with a same-named `.fpt` (and often a `.cdx`/`.idx`) is a **table, not a config file** — e.g. `serverlog.ini` + `serverlog.fpt`, `margerror.ini` + `margerror.fpt`, `System\marg0007.ini` + `.fpt` + `.cdx`. Do not assume `.ini` means text.

---

## 3. The DATA directory — `D:\MARGERP\Data`

**946 entries, 1 subdirectory (`Backup`).** This is the live data directory. **There are no `.dbf` files and no `.mbk` files here.**

### 3.1 Extension scheme = company / financial-year code

Every table is stored as `<tablename>.<companycode>`. The extension is the company/FY slot, not a file type.

| Ext | Files | Total bytes | Newest mtime (IST) | Interpretation |
|---|---|---|---|---|
| **`.c18`** | **32** | **34,831,187** | **2026-08-15 14:00 (live)** | **CURRENT financial year — FY 2026-27. This is the live set.** |
| `.c17` | 32 | 71,034,843 | 2026-08-15 10:06 | Previous FY (2025-26), still being touched |
| `.c16` | 30 | 66,012,622 | 2026-08-02 13:02 | FY 2024-25 |
| `.c15` | 33 | 64,757,314 | 2026-08-02 13:03 | FY 2023-24 |
| `.c14` | 30 | 47,238,963 | 2025-03-30 | |
| `.c13` | 29 | 41,591,720 | 2023-05-20 | |
| `.c12` / `.c11` | 49 / 48 | 44.3 / 45.6 MB | 2023-02-23 | |
| `.c10` | 47 | 61,506,864 | 2022-05-31 | |
| `.c09`/`.c08`/`.c07`/`.c06`/`.c05` | 51/51/51/51/47 | 33.8 / 17.8 / 47.3 / 48.7 / 41.1 MB | 2020–2022 | Older years |
| `.d01` | 30 | 1,255,165 | 2026-08-15 13:57 | **Second live company/book** (small; `support.d01` and `malter.d01` written today) |
| `.a01` / `.b01` / `.j01` | 47 / 48 / 48 | 0.6 / 0.6 / 38.6 MB | 2023-04-29 | Archived/secondary books |
| `.c00` / `.d00` | 2 / 1 | ~4 KB / 2.5 KB | 2025-09-30 / 2017 | `histdis`, `histdis2` history stubs |
| `.cdx` | 186 | 47,421,440 | 2026-08-15 13:57 | Compound indexes (see §7.2) |
| `.idx` | 2 | 3,072 | 2026-08-15 13:47 | `mew1_slmaa1.idx`, `new1_slnaa1.idx` |

### 3.2 Table inventory — the live `.c18` set (exact, with sizes and mtimes)

All paths are `D:\MARGERP\Data\<name>`. Times are IST.

| File | Bytes | mtime |
|---|---|---|
| `acgroup.c18` | 20,227 | 2026-08-15 13:46 |
| `billserial.c18` | 809 | 2026-08-15 13:57 |
| `chiller.c18` | 984 | 2026-04-01 08:43 |
| **`dis.c18`** | **12,595,033** | **2026-08-15 13:46** |
| `distran.c18` | 2,584 | 2026-04-01 08:43 |
| `distran2.c18` | 2,584 | 2026-04-01 08:43 |
| `distran3.c18` | 2,584 | 2026-04-02 08:56 |
| `ggmonth.c18` | 139,715 | 2026-08-15 13:46 |
| `gledger.c18` | 4,367,248 | 2026-08-15 13:46 |
| `gledger2.c18` | 1,464 | 2026-04-01 08:43 |
| `glmonth.c18` | 837,714 | 2026-08-15 13:59 |
| `grefro.c18` | 79,647 | 2026-06-20 19:12 |
| `malter.c18` | 78,525 | 2026-08-15 11:16 |
| `maorder.c18` | 632,561 | 2026-08-15 13:46 |
| `margsync.c18` | 513,745 | 2026-08-15 13:51 |
| **`mdis.c18`** | **6,710,733** | **2026-08-15 13:46** |
| `mdoc.c18` | 329,239 | 2026-06-20 19:23 |
| `mewsale.c18` | 10,535 | 2026-08-15 13:59 |
| `mewslastsub.c18` | 920 | 2026-04-01 08:43 |
| `newsale.c18` | 6,008 | 2026-08-15 13:47 |
| `order.c18` | 251,840 | 2026-08-15 13:46 |
| `pend.c18` | 103,201 | 2026-08-13 09:07 |
| `pendings.c18` | 313,227 | 2026-08-13 20:14 |
| `pro.c18` | 565,033 | 2026-08-15 14:00 |
| `probat.c18` | 1,808,053 | 2026-08-15 14:00 |
| `rate.c18` | 1,066 | 2026-04-01 08:43 |
| `saletype.c18` | 566,102 | 2026-08-01 09:12 |
| `sborder.c18` | 9,465 | 2026-04-01 08:43 |
| `slipno.c18` | 22,825 | 2026-08-15 13:58 |
| `subdis.c18` | 2,857,491 | 2026-08-15 13:46 |
| `support.c18` | 1,999,585 | 2026-08-15 14:00 |
| `unisupp.c18` | 440 | 2026-04-01 08:43 |

Tables present in older FY sets but **absent from C18**: `mewsale1..9`, `mewsal9`, `mewsal10`, `newsale1..9`, `newsal9`, `newsal10`, `mewslast`, `distran2/3` variants differ by year. Older sets (`.a01`, `.b01`, `.j01`, `.c05`–`.c12`) carry the full `mewsale1..9` / `newsale1..9` fan-out; the current year does not.

### 3.3 `D:\MARGERP\Data\Backup`

131 files. Marg's own rolling backups, all with scrambled extensions, e.g.:

- `85139_c18_3554.nlpoj_83319` — 2,184,375 bytes, 2026-08-13 (newest C18 backup)
- `24354_c17_1768.jmbkh_13531` — 4,497,616 bytes, 2026-08-13
- `d-sanjeevni-20150401-20160331.mbk` — 1,752,358 bytes, 2015 (the classic `.mbk` form)
- Day-of-week snapshots: `monday.mst`, `tuesday.mst` … `sunday.mst` (~11 KB each), plus `580_Tuesday.404_mst`, `851_tuesday.554_mst`
- Legacy weekly sets `c04.w3`–`c08.w5.1`

The `<n>_<companycode>_<n>.<5letters>_<n>` naming embeds the company code (`c18`, `c17`, `d01`…). These are the same encrypted-backup family as the unusable `.mbk` from S179 — **do not expect these to be any more readable than the live files.**

---

## 4. Format identification — **encrypted DBF, definitively**

### 4.1 Raw hex, first 64 bytes

Every table in `Data\` — and every `.ini` table in the root and `System\` — begins with the **same 16-byte constant prefix**.

`Data\acgroup.c18`:
```
0000  19 a3 95 78 63 44 f1 98  55 93 67 a1 be c0 2d da   ...xcD.. U.g...-.
0010  14 95 a1 66 f5 24 d0 78  cc d1 03 f7 38 3a 6d f8   ...f.$.x ....8:m.
0020  f4 90 22 68 42 34 e0 88  44 92 45 c7 58 5c 5d 79   .."hB4.. D.E.X\]y
0030  53 c1 67 c6 38 44 f0 98  54 93 47 92 7a 7a 4d f9   S.g.8D.. T.G.zzM.
```

`Data\saletype.c18`:
```
0000  19 a3 95 78 63 44 f1 98  55 93 67 a1 be c0 2d da
0010  14 95 a1 59 50 26 d0 78  2c 12 e0 f1 38 3a 6d f8
0020  f4 90 22 68 42 34 e0 88  44 92 45 c7 58 5c 5d 79
0030  47 40 67 bd 43 44 f0 98  54 93 47 92 7a 7a 4d f9
```

`Data\dis.c18`:
```
0000  19 a3 95 78 63 44 f1 98  55 93 67 a1 be c0 2d da
0010  14 95 a1 66 3f 69 d0 78  4c 32 5b f1 38 3a 6d f8
0020  f4 90 22 68 42 34 e0 88  44 92 45 c7 58 5c 5d 79
0030  57 3b e7 bd 77 98 f0 98  54 93 47 92 7a 7a 4d f9
```

**Answer to "DBF or not": it is a DBF underneath, but not as stored.** Byte 0 is `0x19`, not a DBF version byte. The file cannot be opened by any DBF reader as-is.

### 4.2 Proof that it is a DBF under a 16-byte prefix

Comparing byte-by-byte across 23 encrypted files (all 16 `.c18` tables copied, plus `customerinfo.ini`, `logsetup.ini`, `snmpd.ini`, `margmyno.ini`, `up_margtemp.dbf`, root `company.ini`) gives a constant/varying map that maps **exactly** onto a standard DBF header displaced by 16 bytes:

| File offset | Constant? | DBF field at (offset − 16) | Verdict |
|---|---|---|---|
| `0x00–0x0f` | CONSTANT (only `0x04` has 2 values) | — | 16-byte Marg prefix / magic. Byte `0x04` is `0x63` for data tables and `0x53` for several `System`/root `.ini` tables — a file-class flag. |
| `0x10` | 3 values | version byte | ✓ |
| `0x11`, `0x12`, `0x13` | 3 / 4 / 6 values | last-update YY, MM, DD | ✓ |
| `0x14`, `0x15` | 18 / 11 values (highest variety) | record count, low 2 bytes | ✓ |
| `0x16`, `0x17` | **CONSTANT** | record count, high 2 bytes | ✓ — every table has < 65 536 records |
| `0x18`, `0x19` | 10 / 13 values | header length | ✓ |
| `0x1a`, `0x1b` | 21 / 9 values | record length | ✓ |
| `0x1c–0x2b` | **CONSTANT, 16 bytes** | reserved bytes 12–27 (all zero) | ✓ exact length match |
| `0x2c`, `0x2d` | 2 values each | table flags, code page | ✓ |
| `0x2e`, `0x2f` | **CONSTANT** | reserved bytes 30–31 (zero) | ✓ |
| `0x30–0x35` | varying | field-1 name chars 0–5 | ✓ |
| `0x36–0x3a` | **CONSTANT** | field-1 name chars 6–10 (zero pad) | ✓ all first field names ≤ 6 chars |
| `0x3b` | 3 values | field-1 type byte | ✓ |
| `0x3c–0x3f` | **CONSTANT** | field-1 displacement (= 1,0,0,0) | ✓ |

**Layout: `[16-byte Marg prefix][encrypted standard VFP DBF: 32-byte header + 32-byte field descriptors + 0x0D + fixed-length records]`.**

### 4.3 Nature of the obfuscation

Established properties:

1. **Deterministic and position-keyed with period 256.** Plaintext `0x00` at file offset *i* always produces the same ciphertext byte, determined by `i mod 256`. Proved directly: in `acgroup.c18`, `dis.c18` and `saletype.c18` the header's known-zero run at `0x22–0x2b` is **byte-identical** to the 8th field descriptor's known-zero run at `0x122–0x12b` (`22 68 42 34 e0 88 44 92 45 c7`), and likewise `0x42–0x4f` ≡ `0x142–0x14f` (`24 88 44 54 80 a8 24 94 49 a7 98 9a 3d 7a`).
2. **No per-file key, no salt, no IV.** The prefix and all zero-derived key bytes are identical across every table, every financial year, and even across the `System`/root `.ini` tables. One key serves the whole installation — and, by implication, probably every Marg installation.
3. **Not a plain XOR or plain ADD keystream.** Reconstructing the 256-byte key from known-zero regions and XOR-decrypting (or subtract-decrypting) the record area yields ~46 % / ~41 % printable — not plaintext.
4. **The residual is a bit-rotation.** After XOR-stripping the key, the dominant plaintext byte in each column appears as `0x02`, `0x04`, `0x20`, `0x40`, `0x80`, `0x01` — i.e. *rotations of ASCII space (`0x20`)*. Applying a per-column rotation correction lifts printability to **95.5 %**, with recognisable fragments (`CUR`, digit runs, space padding).
5. **Partial real decrypt achieved.** A constrained solve recovered the DBF header's leading bytes for `dis.c18` correctly: **version byte `0x30`** (Visual FoxPro table *with* memo field — consistent with the `.fpt` memo files elsewhere in the install) and **last-update date `26-08-14`** (2026-08-14, matching the file's mtime). The remaining header words (`nrec`, `hdrlen`, `reclen`) and the field names did **not** resolve, so the exact transform is not a uniform rotate-then-add either.

**Working conclusion:** a position-indexed substitution of period 256 — most plausibly a 256-entry table of (rotation, offset) pairs, or a 256×256 S-box, implemented in the `pfdapi*.dll` family. It is *obfuscation, not cryptography*: no key derivation, no per-file variation, and it already leaks 95 % of plaintext structure under a naive model. **It is very likely fully breakable in a focused session** — but doing so is a deliberate decision with support/warranty implications and should not be the default path (see §10).

---

## 5. Task 3 — ACGROUP / SALETYPE / DIS field lists: **BLOCKED**

`pip install dbfread` succeeded (dbfread installed cleanly). Reading the tables fails immediately:

```
>>> DBF('acgroup.c18', ignore_missing_memofile=True)
UnicodeDecodeError: 'ascii' codec can't decode byte 0xf4 in position 0: ordinal not in range(128)

>>> DBF('saletype.c18', ...)   →  same error
>>> DBF('dis.c18', ...)        →  same error
```

Stripping the 16-byte prefix and retrying also fails (`0xc1 in position 1`), because the DBF header beneath is itself encrypted.

**No field names, no field types, no record counts, and no rows could be produced for ACGROUP, SALETYPE or DIS.** This is the single blocking finding of the session.

*(Positive side effect: because nothing decodes, there was no risk of patient data being read or printed at any point.)*

---

## 6. Task 4 — which table holds the daily sale bills: **inference only, NOT verified**

Cannot be confirmed without decryption. The following is an inference from Marg's table naming, from file sizes/mtimes, and from the CDX index names — **treat as a hypothesis for the next session to test, not as fact.**

| Table | Live size | Written when Marg is used | Hypothesis |
|---|---|---|---|
| **`dis.c18`** (12.6 MB, largest in the set) | ✅ every save | **Sale bill HEADER** — one row per bill. `dis` = the sale/issue register. Bill no. (`A002660` / `CN00167` form), date, party, net/cash amounts, payment mode most likely live here. |
| **`mdis.c18`** (6.7 MB) | ✅ every save | **Sale bill ITEM lines** — `m`-prefixed = detail/child of `dis`. |
| `subdis.c18` (2.9 MB) | ✅ | Sub-detail of the sale bill (batch/GST split). |
| `slipno.c18` (22.8 KB) | ✅ 13:58 | Bill/slip number allocation counters — probably where the next `A00xxxx` comes from. |
| `billserial.c18` (809 B) | ✅ 13:57 | Bill series definitions (`A`, `CN`, …). Present only in `.c12`, `.c15`, `.c18`. |
| `saletype.c18` (566 KB) | 2026-08-01 | Sale-type / rate-category master (not per-bill). |
| `gledger.c18` (4.4 MB) + `glmonth.c18`, `ggmonth.c18` | ✅ | General ledger postings + monthly summaries — the accounting side of each bill. |
| `acgroup.c18` (20 KB) | ✅ | Account groups master — small, no patient data, was the intended safe smoke-test table. |
| `pro.c18` / `probat.c18` | ✅ 14:00 | Product master / product batch (stock), not bills. |
| `mewsale.c18`, `newsale.c18` (6–10 KB) | ✅ | Small "current/last sale" scratch tables used during billing. |

Corroborating evidence from the CDX names (§7.2): `c18dis.cdx`, `c18mdis.cdx`, `c18sbdis.cdx` (subdis), `c18sal.cdx` (saletype), `c18gle.cdx` (gledger), `c18acg.cdx` (acgroup), `c18pro.cdx`, `c18batn.cdx` (probat). The index set mirrors the table set one-to-one.

**Independent confirmation of the bill-number format** — from the plaintext `daybook.xml` (§9), which came out of this same data: sale bill numbers for March 2026 run `A00591`, `A00592`, `A00593` …, alongside `T-000493` and numeric `1008`, `25`. So the `A00nnnn` series in the S179 brief is correct and lives in a single continuous series.

---

## 7. Task 5 — sidecars, config, version

### 7.1 Memo (FPT) files

**There are NO `.fpt` files in `D:\MARGERP\Data`.** Not one, for any company code. The DBF version byte recovered in §4.3 is `0x30` (VFP *with* memo), so either the memo blocks are stored inline in this variant, or the recovered version byte is one of the residual mis-decodes. **Flagging as an open question** — a parser must handle the possibility that memo content lives elsewhere or is absent for these tables.

`.fpt` files *are* abundant outside `Data\`, always paired with a same-named `.ini` table:
`marguser.fpt` (27,392) + `marguser.csv`; `serverlog.fpt` (**768,569,536**) + `serverlog.ini`; `margerror.fpt` (2,011,648) + `margerror.ini`; `margexit.fpt` (68,591,232) + `margexit.ini`; `margependings.fpt`, `margsmsp.fpt`, `margmail.fpt`, `up_margtemp.fpt`, `snmcal1.fpt`, `DEFACAL.FPT`, `DEFASMS.FPT`, `USER1.FPT`, `WINUSER.FPT`, `tempda1.fpt`, `tpa1.fpt`; and in `System\`: `marg0007.fpt`, `marg0010.fpt`, `marg0011.fpt`, `marg0012.fpt`, `askme_chat.fpt`.

### 7.2 CDX / IDX indexes

**186 `.cdx` files in `Data\`, 47.4 MB total.** Naming is `<companycode><shortname>.cdx`, 26 per active company code, for C13–C18 and D01 only (older years have no indexes retained):

`c18acg`, `c18batn`, `c18chill`, `c18dis`, `c18distran`, `c18distran2`, `c18ggm`, `c18gle`, `c18gle2`, `c18glm`, `c18gref`, `c18malter`, `c18mao`, `c18mdis`, `c18mdoc`, `c18msync`, `c18ord`, `c18pen`, `c18pend`, `c18pro`, `c18rate`, `c18sal`, `c18sbdis`, `c18sord`, `c18supp`, `c18unisupp` — and the identical set prefixed `c13`–`c17` and `d01`. Plus `chist.cdx`.

Two loose `.idx`: `mew1_slmaa1.idx` (2,048 B), `new1_slnaa1.idx` (1,024 B), both written today.

Note the index file names do **not** match the table file names (`c18dis.cdx` indexes `dis.c18`), so a parser must map them explicitly. Whether the CDX files are themselves encrypted was not tested.

### 7.3 Config files naming the data path

**`D:\MARGERP\CONFIG.FPW` — plaintext, 156 bytes, full contents:**

```
catman=off
title=MARG ERP LIMITED
icon="MARG.ICO"
files=250
mvcount=75000
stacksize=1024
screen=off
escape=off
resource=marguser.csv
codepage=437
```

Two things of real value here:

1. **`codepage=437`** — the VFP session code page. Any future parser should decode character fields as **CP437**, not UTF-8 or Latin-1.
2. **`resource=marguser.csv`** — and `D:\MARGERP\marguser.csv` turns out to be a **plain, unencrypted VFP DBF**: it begins `30 1a 06 15 34 00 00 00 08 02 30 00 …` = version `0x30`, last update 2026-06-21, **52 records**, header length **520**, record length **48**, first field `TYPE` type `C` length 12. This proves the VFP runtime reads *both* plain and obfuscated tables — encryption is applied selectively by Marg's own code, not by the file system or the VFP engine.

`CONFIG.FPW` does **not** contain a data-path directive; Marg locates `Data\` relative to its own directory. No `.ini` in the root or `System\` could be checked for a data path because they are all encrypted tables, not text.

Other config-shaped files, all **encrypted** (verified by the identical 16-byte prefix): root `company.ini`, `customerinfo.ini`, `logsetup.ini`, `snmpd.ini`, `margmyno.ini`, `up_margtemp.dbf`.

Plaintext exceptions found: `CONFIG.FPW`, `CONFIGW.STP`, `marguser.csv` (DBF), `margsms.txt`, `System\country.txt`, `System\india_mobile_series.txt`, and all the `.xml` / `.xls*` files.

### 7.4 Marg version

**Not determinable from file properties.** `margwin.exe` (13,921,280 bytes, 2025-09-24 12:27 IST) carries no `VERSIONINFO` resource — its PE `TimeDateStamp` is a stale 2007 VFP-linker value, and a string scan turned up no product-version string.

Best available indicators:

- The `pfdapi*.dll` build ladder present in the root: `pfapi443` → `pfapi445` → `pfdapi500` → `pfdapi540` → `pfdapi570` → **`pfdapi584`** (newest, touched 2026-08-15 13:56). Reads as data-layer build **5.84**.
- `System\autoupdate.ini` (47,285 B, written 2026-08-15 14:03) and `System\licenceinfo.ini` hold the real version/licence data — **not opened, by rule**.
- `System\` contains `oldmargwin.exe` (14,787,584 B, 2024-09) and `oldmargwin_2.exe` (14,557,696 B, 2023-04), i.e. this install auto-updates and is roughly one year into the current build.

**To get the exact version:** open Marg → Help → About (or read `System\aboutmarg.pfo`, which is also encrypted). One line in the UI, no file access needed.

---

## 8. Other things worth knowing before designing anything

- **Two live books.** `.c18` (main, 34.8 MB) *and* `.d01` (1.3 MB) are both being written today. `.d01` is small and was created 2022-08-19; it may be a second company, a counter-sale book, or a test book. Any feed must be explicit about which company code it reads.
- **`System\margsqlconnection.ini` (525 B) and `System\mysqlflp.ini` (7,033 B, written 2026-08-15 13:51) exist**, alongside `System\syncdata.ini` (774,459 B) + `syncdata.cdx` (130,560 B) — both updated *seconds* before this survey — and `Data\margsync.c18` (513,745 B, 13:51). **Marg on this machine appears to have an active SQL/sync layer.** These files were not opened because they will contain credentials. **This is the highest-value thing to investigate next** (see §10).
- `System\` also holds `erptoerpitem.ini/.idx` and `erptoerpsupp.ini/.idx`, both written in the last week — Marg's ERP-to-ERP interchange, another possible sanctioned export path.
- `serverlog.fpt` is **768 MB** and growing daily. Unrelated to this project, but worth mentioning to the user as a disk-hygiene item.

---

## 9. The plaintext escape hatch — Marg's Tally XML export

`D:\MARGERP\daybook.xml`, 1,205,131 bytes, written **2026-07-12 12:32 IST**. **Fully plaintext UTF-8 XML.** It is a Tally `Import Data` envelope:

```xml
<ENVELOPE>
<HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER>
<BODY><IMPORTDATA><REQUESTDESC>
<REPORTNAME>All Masters</REPORTNAME>
<STATICVARIABLES><SVCURRENTCOMPANY>SANJEEVNI MEDICOS</SVCURRENTCOMPANY></STATICVARIABLES>
</REQUESTDESC><REQUESTDATA>
```

**Contents:** 791 `<VOUCHER>` elements + 10 `<VOUCHERTYPE>` masters.

| Voucher type | Count |
|---|---|
| Sales | 636 |
| Purchase | 89 |
| Sale Return | 34 |
| Receipt | 25 |
| Payment | 5 |
| Contra | 2 |

**Date range in this file: `20260301` – `20260331`** (March 2026 — a one-month manual export).

**Per-voucher fields** (structure exactly as needed for the finance feed):

```
<VOUCHER VCHTYPE="Sales" ACTION="Alter">
  <DATE>20260302</DATE>
  <NARRATION>…</NARRATION>                    ← may carry customer text; treat as PII
  <VOUCHERTYPENAME>Sales</VOUCHERTYPENAME>
  <VOUCHERNUMBER>A00592</VOUCHERNUMBER>       ← the bill number
  <REFERENCE>A00592</REFERENCE>
  <PARTYLEDGERNAME>…</PARTYLEDGERNAME>        ← customer/party; treat as PII
  <EFFECTIVEDATE>20260302</EFFECTIVEDATE>
  <ALTERID> 1</ALTERID>
  <ALLLEDGERENTRIES.LIST>
    <LEDGERNAME>…</LEDGERNAME>                ← the contra account = effectively the payment mode
    <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
    <ISPARTYLEDGER>Yes</ISPARTYLEDGER>
    <AMOUNT>-320.00</AMOUNT>                  ← signed net amount
  </ALLLEDGERENTRIES.LIST>
  <ALLLEDGERENTRIES.LIST> … <AMOUNT>320.00</AMOUNT> … </ALLLEDGERENTRIES.LIST>
</VOUCHER>
```

2,004 `<ALLLEDGERENTRIES.LIST>` blocks across 791 vouchers — the double-entry pairs. Cash vs credit vs card is derivable from which ledger the non-party leg posts to.

**Sample voucher, PII masked:** `VCHTYPE="Sales"`, `DATE=20260302`, `VOUCHERNUMBER=A00592`, `PARTYLEDGERNAME=<MASKED>`, two ledger legs of `-320.00` and `+320.00`.

Sibling exports in the root confirm this is a habit, not a one-off: `master.xml` (1.66 MB), `transactions.xml` (10.4 MB) — both 2026-07-28 20:39 — plus `master 2025 26.xml`, `TALLY MARCH 26.xml`, `TALLY APR MAY 26.xml`, `TALLY MARCH.xml`, `TALLY APRIL MAY.xml`.

**Caveats:** these were produced by a *human clicking export* in Marg's Tally-export screen (irregular mtimes, month-sized chunks, last one 2026-07-12). Nothing here is automatic yet. Whether Marg can be driven to emit this daily unattended — via a command-line switch, a scheduled task, or the `ede`/`margconnect` modules — is **the key unknown** for the S179 plan.

---

## 10. Recommended next steps, in priority order

1. **Ask Marg support (or check the UI) whether the Tally XML export can be scheduled or command-line driven.** If yes, the whole project becomes a plaintext-XML parser and the encryption is irrelevant. `daybook.xml` already proves the output format carries bill no., date, amount, party and payment leg. *(Cheapest path, fully supported, zero warranty risk.)*
2. **Investigate the SQL sync layer.** `System\margsqlconnection.ini`, `System\mysqlflp.ini`, `System\syncdata.ini`/`.cdx` and `Data\margsync.c18` are all live and were written minutes before this survey. If Marg is already mirroring to MySQL, the finance module can read the mirror directly and this becomes a solved problem. **Handle those files carefully — they contain credentials.** Check the Marg UI (Utilities → SQL/Sync settings) rather than opening the files.
3. **Check the `ede` / `margconnect` / `ebusiness` modules** (`ede.pfo` 4.6 MB updated 2026-08-15, `margconnect.pfo` 605 KB updated 2026-08-01) for a documented export or API surface.
4. **Only if 1–3 all fail:** finish the obfuscation analysis. It is tractable — the transform is a 256-period position-keyed substitution with no per-file key, and a naive model already recovers the DBF version byte, the last-update date and ~95 % of plaintext structure. Budget one focused session. Then: `dis.c18` → bill headers, `mdis.c18` → line items, decode text as **CP437**, snapshot-then-parse, retry on transient read failure.
5. **Do not pursue the `.mbk` / `Data\Backup` files.** They are the same encrypted family as the S179 backup that already failed.

---

## Appendix A — exact facts a future session can rely on without re-scanning

- Live data directory: `D:\MARGERP\Data` — 946 entries, 1 subdir (`Backup`), no `.dbf`, no `.fpt`, no `.mbk`.
- Current financial-year company code: **`c18`** (32 tables, 34,831,187 bytes). Previous: `c17`. Second live book: `d01`.
- File layout of every table: `[16-byte constant prefix][encrypted 32-byte DBF header][encrypted 32-byte field descriptors][0x0D][fixed-length records]`.
- Universal 16-byte prefix: `19 a3 95 78 <63|53> 44 f1 98 55 93 67 a1 be c0 2d da` (byte 4 = `0x63` data tables, `0x53` some config tables).
- Key bytes where plaintext is zero (identical in every file, offsets are file offsets): `0x1c–0x2b` = `38 3a 6d f8 f4 90 22 68 42 34 e0 88 44 92 45 c7`; `0x2e–0x2f` = `5d 79`; `0x42–0x4f` = `24 88 44 54 80 a8 24 94 49 a7 98 9a 3d 7a`.
- Obfuscation period: **256 bytes**, deterministic, no per-file key.
- Session code page: **CP437** (from `CONFIG.FPW`).
- `D:\MARGERP\marguser.csv` is a **plain unencrypted DBF** (52 records, reclen 48, first field `TYPE C(12)`) — useful as a control when testing any parser.
- Reads of live tables succeed while Marg is running; expect rare transient failures on hot tables, resolved by retry.
- Company name in data: `SANJEEVNI MEDICOS`. Sale bill series confirmed as `A00nnn` (plus `T-nnnnnn` and bare numeric series).

## Appendix B — read errors encountered, verbatim

| Operation | Result |
|---|---|
| `device_stage_files D:\MARGERP\Data\mewslast.c18` | `D:\MARGERP\Data\mewslast.c18 does not exist.` (genuine absence in the C18 set) |
| `device_stage_files D:\MARGERP\Data\mewsale.c18` @ 13:59 IST | `upload failed` — Marg was writing the file that second. **Succeeded on retry at 14:01.** |
| `DBF('acgroup.c18', ignore_missing_memofile=True)` | `UnicodeDecodeError: 'ascii' codec can't decode byte 0xf4 in position 0: ordinal not in range(128)` |
| `DBF('saletype.c18', …)` | same |
| `DBF('dis.c18', …)` | same |
| `DBF(<acgroup.c18 with first 16 bytes stripped>)` | `UnicodeDecodeError: 'ascii' codec can't decode byte 0xc1 in position 1: ordinal not in range(128)` |

*Nothing under `D:\MARGERP` was written, renamed, moved or deleted during this session.*
