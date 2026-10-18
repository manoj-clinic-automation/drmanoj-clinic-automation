# S576_PARCHI_DOCTERZ_NAME — the parchi shows Docterz's newest name (kit S576, session S319, 18-Oct-2026)

**Why.** The owner, 17-Oct-2026 20:47 IST: on the parchi, a clinic ID showed one patient's name while Docterz shows another for
that ID. Docterz had renamed the ID after its first visit. The patient master (the tracker's Patient_Master_Join, refreshed into
`patient_ref` by `finance_patient_sync`) keeps the first name it saw, and the sync rewrites it every run, so a data fix would not
last. **Docterz is the record:** its newest day line for an ID names the person.

**What changes.** `/root/finance/slip_log.py` `87f07d57` → `2419c536`, two counted edits (`make_s576.py`):
1. two helpers, `_s576_norm` and `_docterz_newest_name`;
2. `patient()` returns Docterz's newest name when it differs from the master's (ignoring case and spaces), and keeps the master's last-4.

Unchanged: an ID only in Docterz, an ID only in the master, merged rows, and any box without the Docterz table.

On the 16-Oct data, 11 of 8,148 IDs show a different name. One is a real rename; ten are Docterz's corrected spellings.
A lookup takes 0.43 ms.

**No data step.** One restart of `clinic-finance`.

## Install (on the server)
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s576kit && cp -rp /root/deploy/repo/deploy_kits/S576_PARCHI_DOCTERZ_NAME /tmp/s576kit && bash /tmp/s576kit/install_S576_PARCHI_DOCTERZ_NAME.sh
```
`DRY=1` before `bash` runs every gate and the walk, and writes nothing.

## The walk (`walk_s576.py`, 8 checks)
The functions are taken out of the file by the parser and run on a made-up database with made-up names. On the old live file,
`--old` turns exactly the S576 check red and nothing else.

## Undo
```
\cp -p /root/finance/slip_log.py.bak_S576_87f07d57 /root/finance/slip_log.py && systemctl restart clinic-finance
```
