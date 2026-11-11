# S782_XRAY_LEFTOVERS — the parked X-ray pictures: fewer for staff, the rest to the owner and Shavez (F-1236, D887)

**The owner, 10-Nov 13:01 IST:** *"I do not want to leave any work for staff in Check karein as much as possible."* — and on 11-Nov
05:15–05:43 IST: older pictures to him and Shavez; the file name first, then the slips and Docterz, then what the film prints; names
"might not be spelt exactly"; that day's patients sorted closest first; the search box to take a name and the FULL mobile number.

S427 read all 39 pictures parked at the 11-Nov copy (counts only). The re-try (S752 / S772 / S776) now also:
- **(a)** reads a 1–3-digit number in the name as the photo's own number when no patient who came that day (or a date on its film)
  has that ID and the name is not that ID's patient — nothing is stripped before the film is read;
- **(b)** sends a second upload — the very same file name as a copy already filed on the ID its film prints, the film's same date(s)
  and ID, all that day's films with photos — to *X-ray inbox / _filed / duplicates* (never deleted, never filed twice);
- **(c)** never files a picture whose film prints the ID of ANOTHER patient who came that day (0 of the 393 filed so far affected);
- **(d)** files a picture on the ONE X-ray patient of the film's day (±1, photo still missing, his day over) whose name is the
  picture's but for the usual spelling variants — the same SOUND (SUNEETA = SUNITA, KAVITHA = KAVITA, SHYAM = SYAM) or one vowel inside
  a long word (RAMESHWAR / RAMESHWER) — the first words agreeing; never when anyone else who came those days has a name like it, and
  never when the film or the name carries an ID that is a real other patient. ANIL ≠ SUNIL, SARITA ≠ SARIKA ≠ SAVITA, VANITA ≠ VINITA, MANISHA ≠ MONISHA, RAJKUMAR ≠
  RAJKUMARI, SANTOSH ≠ SANTOSHI, RAZA ≠ RAJA;
- ignores a film date that is no calendar date instead of stopping the re-try.

**Check karein** (`check_screens.py`): reception sees the pictures first seen in the last 7 days; older ones only the owner and
Shavez (the lab logins) — the owner's tile says so. That day's patients: names that match but for the spelling first ("Similar
name"), the rest by likeness, the three best on top, the others folded ("All other patients"). The box under them takes a clinic ID,
a NAME or a 10-digit MOBILE and lists up to 8 patients with the full mobile number and "came that day"; it answers only for a picture
that is waiting. **The duty map v22** (reception's X-ray line counts the last 7 days) arrives with the git pull.

/root/finance/records.py bae45d82 (S776) → 794cb87f (`make_s782.py`) · /root/finance/check_screens.py ce7d248d (S757) → c259e6a2
(`make_s782_cs.py`) · claude_code_briefs/DUTY_MAP.json v21 fdec576c → v22 616e0839 (`make_s782_dm.py`).
**On the 11-Nov copy (before (d) and the search):** 39 parked → 1 filed, 2 to duplicates; (d) filed 1 more on the copy in its first
form (now stricter). Reception's list: 6 of 39 are within 7 days.
**Cold reviews (fresh agents), all closed before install:** round 1 — five (a duplicate never re-asked or stuck; a second VIEW sent to
duplicates; an impossible film date stopping every re-try; a short ID stripped before the film was read); round 2 — a letter-likeness
rule that took ANIL for SUNIL (caught by S776's own walk); round 3 — two blockers (SAVITA/SARITA by one letter; a one-digit-off ID that
is a real patient) and two more (a day not over; the search usable as a patient directory); round 4 — two more (VANITA/VINITA, an A/I vowel; a short old ID spelt another way dropped as a photo number) — vowels now only E/I, O/U, A/E or an A in or out.
**Walks (cloud, an empty-schema database, made-up patients):** S782 31/31 with the CONTROL red on the live files (19 of 31); S776
17/17, S772 39/39, S752 50/50 and S373 20/20 on the new files. The installer re-runs every one of them on a copy of the LIVE database,
and the proof, before it writes anything.

**Install** (after the publish), one line on the server:
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s782kit && cp -rp /root/deploy/repo/deploy_kits/S782_XRAY_LEFTOVERS /tmp/s782kit && bash /tmp/s782kit/install_S782_XRAY_LEFTOVERS.sh
```
Undo: `bash /tmp/s782kit/install_S782_XRAY_LEFTOVERS.sh --undo` (both files back to S776 / S757).
