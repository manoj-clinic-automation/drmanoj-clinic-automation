# S200_R6 — the Staff Ledger revamp: cover duty · settings-linked fines · dark mobile UI

## The owner's three complaints, each answered

**1. "dropdown has no place for shivani cover duty, it can be for other staff also"**
NEW category **Cover duty (Rs 200/day)** — a CREDIT, per-day with a date range, narration
REQUIRED (who was covered), enterable by maker_full and the doctors. And it reaches PAY:
`salary_policy.py` now reads APPROVED `COVER_DUTY` rows alongside night duty into the month's
duty credits. Enter Shivani's four July cover evenings with July dates and her ₹800 lands in
the July compute automatically.

**2. "the uniform fine amount is wrong — link to settings"**
It was wrong: the ledger said ₹20/day while D336 ruled ₹15. The two rate cards can no longer
disagree — the uniform and I-card day-rates are read live from
`salary_policy_settings.json` (`dress_rs` / `icard_rs`), fail-soft to ₹15 if the file is
unreadable. Change the rate on the settings page and the ledger follows, no code.

**3. "date picker at far right… long rows aren't needed… revamp, my colours, mobile friendly"**
The whole app moves to the clinic's own dark family (the register/portal palette): content in a
centred column instead of edge-to-edge rows, the form a compact card with PAIRED fields —
Staff|Category, Date|To, Amount|Instalment — so the date picker sits beside its label, not a
screen away. Dark-scheme date pickers, 16px inputs (no iOS zoom), full-width save button,
nav as tap-friendly pills, tables scroll in place. Every field name/id unchanged — the
advance-ceiling script, previews and gates all work untouched.

## Files

| file | was | now |
|---|---|---|
| `/root/staff_ledger.py` | `acd7b538ec9476f86e243c73eec3d3fd` (v3.2-S192-SL5) | `18052621e60c0840c3f736355947e589` (v3.3-S200-SL6) |
| `/root/staff_register/salary_policy.py` | `260944bf8493783ec102cbdd286db8c6` (R5b) | `9b14c340530826563dafb7ea84e8cc93` |

## Proof offline
Patched from hash-verified live bytes, every anchor exactly once; py_compile + pyflakes clean
(the three pre-existing notes only). **Ledger selftest 294 checks GREEN**, including new ones:
cover 4d = +800 pending · cover narration compulsory · fine rates follow a synthetic settings
file (25/30) and fall back to 15 when it is absent · duty rates unaffected. Two old assertions
legitimately moved with the corrected rate (uniform 3d = −45; the close CSV 445/3545/−3100) —
each updated with its reasoning in place. Policy selftest PASS.

## Install
    cd /root/deploy/repo && git pull
    bash /root/deploy/repo/deploy_kits/S200_R6/INSTALL_S200_R6.sh

Both gated → both backed up → swap → compile → both selftests on the box → restart
staff-ledger + staff-register → probes → rollback of BOTH on any failure.

## After GREEN — Shivani's July cover, then the lock
1. Ledger → New entry → Shivani → **Cover duty** → the four July evening dates → narration
   "covered Alisha's evening duty" → save (doctor = DIRECT).
2. Re-run the July dump if you want to see her ₹800 inside (net becomes 7,675.45).
3. Then the month-end flow → approve Sheet 1 + Sheet 2 → **LOCK**.
