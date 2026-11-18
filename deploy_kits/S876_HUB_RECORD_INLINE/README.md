# S876_HUB_RECORD_INLINE — the patient's record inside the Hub (D1007)

**Session 483 (the Sanjeevni chat), 18-Nov-2026.** His OK 15:25 IST on the mock-up
https://claude.ai/artifact/Q9RmY4keBZFa9H3p9ebgBc and "proceed" 15:30.

## What he sees
On his Hub (https://followup.dr-manoj.in/finance/approvals), in a day panel, the clinic ID on every bill and every sale
return becomes a tap (`#ID ▸`). The Returns card's detail gets the same tap ("the patient's record #ID ▸"). The record
opens right under the row; a second tap closes it. No page change, no dialog (F-1464).

The record: one line per event, newest first, in words — consulted · free revisit · X-ray (the study from the slip) ·
procedure · blood test (report received) · hospital/surgery · bought medicines · returned · exchanged — with the money
and the paper one tap under each (the slip, the films, the lab report, the bill's lines, the credit note's lines).
A return shows once, on its own date, naming the bill it returns; the bill notes "5 tablets returned 18-Nov".
Bought, gave back and took another medicine on one day = one "Exchanged" line. A bill with the same medicines and
quantities as this patient's bill of the same or the day before is flagged amber ("Billed twice?"), grey when a return
takes it back. Quantities in words ("1 strip 5 tablets", "3 injections", "1 bottle"), never "1:5". The first five
visit days open; the rest behind "earlier". "Open the full record ↗" goes to /finance/records/p/<ID>.
A walk-in (WALK-IN, or an ID beginning WA) has no record and no tap. An exchange is one line only when the return takes the whole first bill back; a part given back is a plain "Returned".

## Files
| file | from | to |
|---|---|---|
| /root/finance/patient_events.py | NEW | 4ad64172 |
| /root/finance/sanjeevni_day.py | db30da9f | 69c2921e (init mounts patient_events, as hub_cash) |
| /root/finance/finance_ui/finance_approvals.html | 254c0bbf | f045686d (4 anchors) |

Read only: /root/finance/records.py (THE PARENT's) — the same tables, the same pharmacy SURE rule (checked by a person or
matched >= 0.95, no open identity dispute). **patient_events.events() is the one reader of a patient's story; the
parent's F-1466 page fix is to read it rather than build a second.** Nothing is written to any table.

Doors (checker only): `GET /finance/sanjeevni/api/patient/<cid>/record`, `GET /finance/sanjeevni/api/patient-events/healthz`.
Settings (setting table): `patient_events.same_bill_days` (1), `patient_events.recent_days` (5).

## Install (his one line, after his publish)
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s876kit && cp -rp /root/deploy/repo/deploy_kits/S876_HUB_RECORD_INLINE /tmp/s876kit && bash /tmp/s876kit/install_S876_HUB_RECORD_INLINE.sh
```
The installer: kit gates; live FROM pins; rebuilt on the box from the live bytes (make_s876.py) to the TO pins; the proof
(synth_s876.py: made-up database + every clinic ID on a copy of the live database) green; the control on the live files
red; S874's proof not worse; place, read back, restart; the door must answer (200 or the login gate's 302 = mounted).

## Undo
```
bash /root/deploy/repo/deploy_kits/S876_HUB_RECORD_INLINE/undo_s876.sh
```
