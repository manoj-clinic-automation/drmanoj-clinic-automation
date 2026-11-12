# S801_WA_LIST_MOBILES — the show-only list gets its mobile numbers

S798's page (`/portal/messages`) went live at 12:05 IST 12-Nov and holds **every** row for *no mobile number on record*: on
the server `finance.db patient_ref` keeps only the last four digits and a fingerprint (its `mobile` column is empty — the
installer's own line said "no mobile 27"). The full mobiles are in the Call Console's patient mirror,
`/root/wa/console.db` table `patients (phone10, patient_uid, clinic_id)`, rebuilt every 10 minutes from the tracker's list —
the same list the WhatsApp Inbox and the ring pop-up name patients from.

- `/root/portal/wa_ladder.py` 8b6bd641 → ca0334b4: when `patient_ref` has no full mobile, the mobile is taken from that list
  by clinic ID, else by patient key — **read-only**. One number → used. Two different numbers → the row is held
  (*2 different mobiles on record*). The list missing or unreadable → every patient row is held and the page says so.
- Still **SHOW ONLY**: no send code (the walk checks the file again).
- **Placed only if it helps:** the installer counts today's rows without a mobile on the live records with the file as it is
  and with this kit; if the count does not get smaller, nothing is changed and the two lines are printed.

Built by `make_s801.py` on the live bytes (S798's file). **Walk** 40/40 on made-up patients in the box's real shape
(`patient_ref.mobile` empty for everyone, the mobiles in a made-up console list); the CONTROL red on S798's file (13 of 40).

**Install** (after the publish), one line on the server:
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s801kit && cp -rp /root/deploy/repo/deploy_kits/S801_WA_LIST_MOBILES /tmp/s801kit && bash /tmp/s801kit/install_S801_WA_LIST_MOBILES.sh
```
Undo: `bash /tmp/s801kit/install_S801_WA_LIST_MOBILES.sh --undo`.
