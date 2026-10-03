# S457_DOCTERZ_SERVER_PATH — session 292, 03-Oct-2026 (F-697)

**The owner, 03-Oct:** *"added live folder, also need the exports from reception pc docterz for this, server path seems better than the google drive one."*

**The fault it ends (F-697).** Reception downloads two files from Docterz every evening — the **consultation report** (Day Revenue) and the **follow-up log** (the follow-up tracker's list and the Callback Tracker's follow-up list). Since S449 the reception PC posts both straight to the server. But the tracker that processes them runs on the owner's PC and reads `D:\Downloads`, so a day reached his portal only after the two files were copied across by hand.

**What it changes.**

| where | file | from → to | what |
|---|---|---|---|
| server | `/root/finance/reception_door.py` | `be5ec171` (S456) → `built/reception_door.py` | two read doors: `POST /finance/api/reception/exports/list` (the current exports of the last days — md5, kind, day, rows, bytes, when downloaded; counts and dates only) and `…/exports/get` (one export's bytes, md5-checked before sending). Each needs a fresh Ed25519 signature from a key in `reception_job_keys.txt`, over that door's own words; a job signature or a job's read token opens neither. Superseded, quarantined and out-of-store rows are never listed or sent. |
| server | `/root/finance/finance_app.py` | `a92baae4` → `40aef4df` | the two paths join `PUBLIC_PATHS` (`apply_s457.py`, one anchored edit). |
| owner's PC | `C:\followup_tracker_local_test_kit\local_test_kit\followup_tracker\docterz_fetch.py` | NEW (`pc/docterz_fetch.py`) | asks at most every 10 minutes, compares by md5 with the Docterz files already in `D:\Downloads` and with what it fetched before, downloads what is missing, checks it, saves it as `<prefix>_<day>_reception_<6 hex>.csv` with reception's download time. Never raises, never overwrites, never deletes; logs counts and dates only. |
| owner's PC | `…\followup_tracker\DOCTERZ_PICKUP.bat` | `90f45531` → `pc/DOCTERZ_PICKUP.bat` | one line: the fetch runs before the pickup. |

**Not touched:** `docterz_pickup.py` on either machine, `processor.py`, the tracker's ledgers, the server's `docterz_export` rows, the Drive folder (it stays; it is simply no longer needed for this).

**The owner's line (one line; it runs S456 first):**

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S456_WINDOWS_CURRENCY/install_S456_WINDOWS_CURRENCY.sh && bash /root/deploy/repo/deploy_kits/S457_DOCTERZ_SERVER_PATH/install_S457_DOCTERZ_SERVER_PATH.sh
```

**Then the PC's side — placed by the assistant through the connected live folder,** the old `.bat` kept beside it as `.bak_S457_90f45531`. Proof: `D:\Downloads\DocterzArchive\_server_fetch_last.txt` after the next five-minute pass.

**Walk (46 checks, real HTTP, made-up exports, a throwaway key):** unsigned / other key / other door's signature / a job's read token / 20 minutes stale → refused; list = the current exports only; get = the exact bytes; superseded, quarantined, tampered, out-of-store → not sent; the fetcher: dry run writes nothing, fetches only what is missing, sets the file's time, leaves no half file, asks at most every 10 minutes, one log line for an idle evening, honours its switch, refuses wrong bytes, survives a wrong key and a dead server, always ends 0.

**Switch (owner's PC):** a file `D:\Downloads\DocterzArchive\_server_fetch_OFF.txt` (or the PC-wide `D:\Downloads\margsync\_off\ALL_OFF.txt`).

**Undo.** Server: `\cp -p /root/finance/finance_app.py.bak_S457_a92baae4 /root/finance/finance_app.py && \cp -p /root/finance/reception_door.py.bak_S457_be5ec171 /root/finance/reception_door.py && systemctl restart clinic-finance`. PC: put the `.bak_S457_90f45531` bat back (or just make the switch file).

**The manual way stays:** a download in Chrome on the owner's PC, or the files copied into `D:\Downloads`, is taken exactly as before.
