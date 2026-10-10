# S511_RECEPTION_MATCH — the reception login's tiles, and Morning match's list (Club F, 1)

Session 304 (parent), 10-Oct-2026. The owner's list, item 7 (CLUB 3 a).

## What changes
- **The shared `reception` login** now shows **Docterz daily collection**, **Morning match** and **Check karein**, as Alisha's and
  Shivani's logins do (`tile_grants.json` v33 → v34; the login already holds the roles those pages ask for).
- **Morning match** opens on a list of the **October working days still waiting for a first pass, oldest first** — one tap opens
  a day. One day waiting goes straight to it; none goes to yesterday, as before. Shavez's list also shows the days waiting for his
  check. On the session's copy of the books: **8 days, 01-Oct to 09-Oct**.
- **The verdict** no longer says *"the counter sheet, Docterz and the bank agree"* while the bank's file has not come: it says the
  counter sheet and Docterz agree, and that the bank is matched when its file comes (F-796).

## Install (his one line on the VPS, after PUBLISH_ALL)
    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S511_RECEPTION_MATCH/install_S511_RECEPTION_MATCH.sh

## Undo
    \cp -p /root/finance/clinic_money.py.bak_S511_683f7511 /root/finance/clinic_money.py && \cp -p /root/portal/tile_grants.json.bak_S511_64f8b049 /root/portal/tile_grants.json && systemctl restart clinic-finance clinic-portal
