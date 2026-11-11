# S785_XRAY_DOORS — the owner's way to his X-ray page

**The owner, 11-Nov-2026 06:34 IST:** *"Cannot find the flow from my portal page or through my command console or through the month
tile."* — 06:38: *"go"*. Before this kit his X-ray page (`/finance/records/xray-check`) was reached only from Patient records, or from
the third line of the folded "Scans & papers" section of his console.

- `/root/portal/portal.py` 59b5c252 → an **"X-ray photos"** tile in the **Patients** group, right after Patient records — the doctors
  only; Dr Bhawna's 'only' list keeps it off her home. The page's own gate (unit 'records') is unchanged.
- `/root/finance/owner_console.py` 27d31775 → **Needs you** (the section that is always open) carries a line *"N X-ray photos waiting
  more than 7 days — yours and Shavez's to file"* while any wait (S782 took them off reception's list); the Scans & papers line says
  "waiting to be filed". A failure in reading them never breaks the section.

Built by `make_s785.py` on the live bytes (the 11-Nov bundle). **Walk** 10/10, the CONTROL red on the live files (9 of 10); a full
rehearsal of the installer (place, restarts, health, journal, undo) on a stand-in root. Needs S782's `check_screens.py` (c259e6a2) live.

**Install** (after the publish), one line on the server:
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s785kit && cp -rp /root/deploy/repo/deploy_kits/S785_XRAY_DOORS /tmp/s785kit && bash /tmp/s785kit/install_S785_XRAY_DOORS.sh
```
Undo: `bash /tmp/s785kit/install_S785_XRAY_DOORS.sh --undo`.
