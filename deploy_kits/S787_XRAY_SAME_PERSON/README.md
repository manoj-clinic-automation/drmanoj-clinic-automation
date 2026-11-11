# S787_XRAY_SAME_PERSON — one card per person on the X-ray check pages; "Not in Docterz"

**The owner, 11-Nov-2026 08:38 IST:** *"In my X-ray check page, Reshma with a spelling RESMA is entered multiple times. Patient of 5th
November, staff added her photos again on 9th November, and there is no way to tackle this. Another is Sachin Agrawal, again a patient
of 5th November ... He was not in doctors, not registered in doctors, so there is no flow for him also. Do the needful."*

`/root/finance/check_screens.py` c259e6a2 (S782) → TO · `/root/finance/records.py` 794cb87f (S782) → TO · `claude_code_briefs/DUTY_MAP.json`
v22 616e0839 → v23 (with the git pull).

1. **Another photo of a patient filed that day files by itself.** Before each filing plan (`/api/xray-plan`) `check_screens.s787_auto`
   gives a parked photo the ID of the patient whose X-ray photo was FILED on its day (the film's printed date when read; ±1 day) when
   its name is his but for the usual spelling (S782's sound rule: RESMA = RESHMA) — only when exactly one such patient, nobody else
   who came those days has a name like it, and the film or the name prints no other real patient's ID. On the 11-Nov copy: 3 of 39
   (RESMA → her 5-Nov ID among them). It is written as a person's answer by "system · S787", so the next filing run files it.
2. **The same person's photos are one card** (names alike, days within a week): the title says "· N photos"; one answer — the
   patient tapped, "Not in Docterz" — goes to every photo of the card. Counts (his tile, Aaj ka kaam's line) count people. On the 11-Nov
   copy: 39 photos → 29 cards (SACHIN AGARWAL: one card of 3).
3. **"Not in Docterz"** — a new button on Check karein (*Docterz mein nahi*) and on his page (*Not in Docterz (not registered)*): the
   card leaves every waiting list (reception's duty line too — the duty map v23) and waits on a **fifth tile, "Not in Docterz"**, on
   his X-ray page, with the photo and the same picker and search box: once the patient is registered, find him by name or mobile and
   file all his photos in one tap. "Not an X-ray" stays one photo at a time.

Built by `make_s787.py` on the live bytes (S782's files; the duty map v22 shipped as `DUTY_MAP.json.v22` for the remake). **Walk**
22/22 on the 11-Nov copy of finance.db (counts and ok/BAD only); the CONTROL red on the live files; both pages' scripts pass
`node --check`. The installer re-runs the walk on a copy of TODAY's database before writing.

**Install** (after the publish), one line on the server:
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s787kit && cp -rp /root/deploy/repo/deploy_kits/S787_XRAY_SAME_PERSON /tmp/s787kit && bash /tmp/s787kit/install_S787_XRAY_SAME_PERSON.sh
```
Undo: `bash /tmp/s787kit/install_S787_XRAY_SAME_PERSON.sh --undo` (answers already given stay).
