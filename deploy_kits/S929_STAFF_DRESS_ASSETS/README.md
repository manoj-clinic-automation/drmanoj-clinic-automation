# S929_STAFF_DRESS_ASSETS — dress / i-card "paused", the current dress set, mobiles and cycle

*The parent · S498 · 22-Nov-2026.*

**Why "paused".** A lost or damaged uniform opens a *pause* (the dress fine is off while it is open). It ends only when someone approves the re-issue *and* separately closes the pause. Neither was done: Alisha (pauses 20-Aug, 07-Oct), Shivani (19-Oct), Vikki (07-Oct, twice). I-cards were all fine.

| part | what changes |
|---|---|
| `staff_register/staff_register.py` 18973ca9 → TO | Approving a re-issue **closes that item's open pause by itself** (to the day before the issue; a pause that began after the issue is left). An issue records **size** and **what was given**. The old 01-01-2000 seed rows read *before the register*; an entry marked *superseded* has no Approve. |
| one-off `s929_load.py` (one transaction, audited, the register's database backed up first) | Shavez's sheet: the **JAN 2027 tab = the current set** of Ranjeet, Sukhveer, Surendra, Vikki, Sandip, Awdhesh, Shivani, Darpan, Shavez, Alisha — approved, dated 22-Nov (hand-over date not recorded); the 2025 and 2026 tabs as earlier issues with their dates. The three open pauses close to 21-Nov (the dress fine resumes 22-Nov). Three old pending entries → *superseded*. **Mobiles** with Shavez, Darpan, Surendra, Ranjeet; **cycle** with Sandip — on each staff page under *Issued assets* (number / IMEI and date to be filled). Staff who have left (Pravesh, Aditya, Jaspal) are not loaded. |

## Proof
- `walk_s929.py` on a made-up register: **23/23** (the three paused before; the load; everyone OK after; the pauses still cover their own past days; the new rule closes a pause on approval and leaves an older issue alone; the page shows size, what was given, *before the register*, *superseded*, the mobile). The live file red. The register's own `--selftest` OK on the new file.
- On the box the installer also runs the load on a **copy** of the live register first.

## Install (his one server line)
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s929kit && cp -rp /root/deploy/repo/deploy_kits/S929_STAFF_DRESS_ASSETS /tmp/s929kit && bash /tmp/s929kit/install_S929_STAFF_DRESS_ASSETS.sh
```
`DRY=1` before `bash`: every gate, the walk and the load on a copy, nothing changed. `--undo`: the file back (the loaded records stay).
