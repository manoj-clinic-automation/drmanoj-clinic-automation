# S420_WA_STAFF_REPLY — WhatsApp in the current Google tracker, the VPS half · session 284 · 27-Sep-2026

**The owner's item 2 (D630, 26-Sep):** Reply for every staff member with *sent by*; the sender's number in the WhatsApp alert; a failed alert retried instead of lost.

## This kit (the VPS)
| file | from | to | what changed |
|---|---|---|---|
| `/root/wa/notifier_wa.py` | `08219ae8` | full file | **the sender's number** in every alert body (`<name> · <number>` / `<number>` then the text — full number, the topic reaches only his and the staff's own phones); **a failed push no longer advances the processed row**: it is retried every cycle, up to 5, then logged *GIVEN UP* and skipped (AF-20). The batch fallback (no message column) gets the same rule. |
| `/root/wa/wa_send_api.py` | `a3ed3708` | full file | `/wa-send` accepts an optional `by`; the outbound row written into `WA_Inbox` carries it in the **`sent by`** column (header-driven, like every other field; blank when absent). |
| `WA_Inbox` tab | 8 columns | 9 | the installer adds the header **`sent by`** once, as the next free column; the receiver writes by header too, so its rows are unaffected. |

Restarts `wa-notifier` and `wa-send-api`. Backups `notifier_wa.py.bak_S420_08219ae8`, `wa_send_api.py.bak_S420_a3ed3708`. RED after placing → restored.

## The Apps Script half (placed in the owner's browser, D577; recorded in `GAS_CURRENT/ClinicCallbackTracker/`, D583)
`WebApp.gs`: `checkWindow` / `sendReply` open to every signed-in role (`dashRole_ !== 'none'`); `sendReply` sends `by` = the login's roster name (`agentInfoForKey_`, 'Doctor' for the master key); `getThread` returns `by` from the `sent by` column. `Dashboard.html`: the four `DASH_ROLE==='full'` gates on Reply / thread compose opened; *we → <name>* in the thread and the recent list. A new version of the EXISTING deployment, never a new deployment.

## Proof
`walk_s420.py` — 14 checks, no network: number in the body, own outbound skipped, ntfy down → nothing lost, retried, both waiting messages delivered when it returns, given up after 5; the relay 403 gate, 8-column row today, 9 with the column, blank without `by`. The installer runs it on the box with the venv, adds the header (one cell), then places, restarts and probes (403 without key; the notifier's baseline line; the journal since its own restart).

## Install — one line on the VPS (after the publish)
```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S420_WA_STAFF_REPLY/install_S420_WA_STAFF_REPLY.sh
```
