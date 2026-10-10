# S508_EXPORTS_CONFIRMED — reception sees, in green, that both Docterz reports are in

Session 304 (parent), 10-Oct-2026. The owner asked that staff get a **confirmation** that both evening Docterz exports are done
(*"Good idea, do it"*, 22:31 IST).

## What reception sees on their Aaj ka kaam
- After 7 pm, while either report is missing (or the follow-up log is short — S507): the job line, as now —
  *"Jaane se pehle: aaj ki Docterz ki dono report nikaliye"*.
- Once both are on the server: the same place shows a **green row**, nothing to press —
  *"Aaj ki dono Docterz report server par aa gayi ✓ — Consultation: 22 patient (21:00) · Follow-up log 09-Nov tak (21:00)"*.
- Before 7 pm and on Sundays: nothing.

## Install (his one line on the VPS, after PUBLISH_ALL)
    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S508_EXPORTS_CONFIRMED/install_S508_EXPORTS_CONFIRMED.sh

## Undo
    cd /root/finance && \cp -p aaj_kaam.py.bak_S508_e8517623 aaj_kaam.py && \cp -p aaj_kaam.html.bak_S508_d7c9c38b aaj_kaam.html && systemctl restart clinic-finance
