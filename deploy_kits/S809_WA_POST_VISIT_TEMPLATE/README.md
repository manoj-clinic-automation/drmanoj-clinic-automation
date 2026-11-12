# S809_WA_POST_VISIT_TEMPLATE — the new post-visit wording

**Session S442, 13-Nov-2026, the parent. On top of kit S808.** The owner (04:12 and 04:30 IST, 13-Nov): X-rays and blood reports are no longer put into the Docterz app (since September they are kept on the server), so the post-visit message must not promise reports there; he made a new template in the MyOperator panel and it is approved.

## What was read in the panel (as him, 04:33 IST)
`copy_drmanoj_post_visit` — Utility, Approved, created by him. Against the old `drmanoj_post_visit` it drops "& Reports / और रिपोर्ट" (the line now reads "Prescription / पर्चा के लिए Docterz app par registered mobile se login karein") and "(Orthopedics & Joints)". One blank — the patient's name. Buttons: Book Appointment, Call Clinic. The rest is word for word the old message.
**Not seen in the panel's list: the template's language code and the blank's key.** The kit takes them as the old template's ("en", "1") because the name says it is a copy. If either differs, MyOperator refuses the message — and the first thing that happens after install is a test to the owner's phone, which shows it. Nothing reaches a patient before that test is confirmed.

## What it does
- `/root/portal/portal_wa.py` (e8b27db9 → 4b153e7d): the new message is ADDED to the portal sender's list (7 lines). Every other message is untouched; the old post-visit message stays in the list (the hand page `/portal/wa` shows both).
- `/root/portal/wa_ladder.py` (5189a155 → c5e6a74c): the "After today's visit" list uses the new name (one line; the version line).
- The store: the "After today's visit" switch is set OFF and its test is forgotten, so the NEW wording must reach his phone and be confirmed before the switch can be turned on (the test is kept per list, not per wording).
- Both files are remade on the box from the live bytes; **the kit ships no copy of a live file**. Nothing is sent.

## Proof
`walk_s809.py`, 7 checks, the REAL portal sender with only the line to MyOperator replaced by a recorder: the new message known, same shape; what leaves (name, language, the one blank); the six lists; the contract with the sending file; the 9:05 pm run sends the new message once; the test is the new message; no number in the kit. Control on the live files: red 5 of 7. Two mutations (the list left on the old name; a second blank) red.

## Install
With S808 in one line (the owner's own mobile is the line's last word):
`cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s808kit /tmp/s809kit && cp -rp /root/deploy/repo/deploy_kits/S808_WA_LADDER_SEND /tmp/s808kit && cp -rp /root/deploy/repo/deploy_kits/S809_WA_POST_VISIT_TEMPLATE /tmp/s809kit && bash /tmp/s809kit/install_S808_then_S809.sh <his own 10-digit mobile>`
Alone (S808 already in): `bash /tmp/s809kit/install_S809_WA_POST_VISIT_TEMPLATE.sh`. `DRY=1` writes nothing. `--undo` puts both files back as S808 left them (undo S809 before S808).

## Files
`make_s809.py` · `walk_s809.py` · `install_S809_WA_POST_VISIT_TEMPLATE.sh` · `install_S808_then_S809.sh` · `SUMS.md5` · `KIT_ID.txt`.
