# S776_XRAY_FEWER_LEFT — fewer parked X-ray pictures left for staff

**The owner, 10-Nov-2026 13:01 IST:** *"I do not want to leave any work for staff in Check karein as much as possible."*
After S772 (live 12:57), S774 (read-only, on the live database) found 41 of 70 pictures still parked: 23 match nobody recorded that
day; the rest could be placed by these rules — for a picture nothing else placed, its film read, never a child's picture, names
compared by WHOLE words (never first letters — SUNITA is not SUNIL), and "close" meaning the same FIRST word or two words shared
(a surname alone never):
- **R1** the ID printed on the film, on its X-ray day by the film's date — the name strict, or close while no patient of that day
  (X-rayed or only seen) has an ID one keystroke off; a picture with no name is never placed on a read ID alone;
- **R2** the film's date within a day; the file has no ID (or one a keystroke off) and the film prints none (or his): the name close
  to ONE X-ray patient of that day, whose X-ray of that day still has no photo;
- **R3** the film's ID is a patient who CAME that day with no X-ray billed (name as R1), or with no ID on the film the name is word for
  word ONE such patient — filed on him; it then shows on the owner's *X-ray taken, no X-ray slip* list (S757) to go to Shavez to bill;
- a file's ID that is not confirmed gives the film's day only when that ID is not an X-ray patient of that day — the file's ID never files.

`/root/finance/records.py` bfd5b845 (S772) → built by `make_s776.py` (five counted edits + `s776_block.py`). Nothing else changes.
**Cold review:** R1 NOT SAFE (R2 matched a surname alone while the file's own ID named another patient) — built; its probe stays
parked. **Walks:** S776 17/17 (cloud), CONTROL red on the live file; S772 39/39 and S752 50/50 on the new file. On the box the installer re-runs
them, plus S373's, and the proof on a copy of the live database with the film reads.

**Install** (after the publish), one line on the server:
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s776kit && cp -rp /root/deploy/repo/deploy_kits/S776_XRAY_FEWER_LEFT /tmp/s776kit && bash /tmp/s776kit/install_S776_XRAY_FEWER_LEFT.sh
```
Undo: `bash /tmp/s776kit/install_S776_XRAY_FEWER_LEFT.sh --undo` (back to S772).
