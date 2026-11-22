# S931_PAUSE_ASK_APPROVE — a dress / i-card pause needs Shavez's or the doctor's approval

*The parent · S498 · 22-Nov-2026 · the owner 15:11: "pause shd start only with Shavez or my approval, reception can only initiate it."*

| file | what changes |
|---|---|
| `staff_register/staff_register.py` 22a75b96 (S929) → TO | Reception's (Alisha, Shivani) **"Ask for a pause"** is stored as an ask: the dress / i-card fine is **not** paused. **Shavez or a doctor** taps **Approve** (the pause starts from the date asked) or **Reject**. Their own pause starts at once. The asks show as **PAUSE ASKED** on the staff list, as a card on **Pending review** (Approve / Reject there too), and in the portal Staff Register tile's *to approve*. A re-issue's approval (S929) never closes or counts an ask. |

## Proof
`walk_s931.py` (made-up register, real logins as test users): **17/17**; the live file red. S929's walk 23/23 and the register's own `--selftest` OK on the new file. Rehearsed: dry, forced red rollback, install, again, undo, tamper, SUMS, lock.

## Install
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s931kit && cp -rp /root/deploy/repo/deploy_kits/S931_PAUSE_ASK_APPROVE /tmp/s931kit && bash /tmp/s931kit/install_S931_PAUSE_ASK_APPROVE.sh
```
