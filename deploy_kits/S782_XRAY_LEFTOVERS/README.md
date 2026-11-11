# S782_XRAY_LEFTOVERS — the parked X-ray pictures that photo numbers and second uploads kept on staff's list (F-1236)

**The owner, 10-Nov-2026 13:01 IST:** *"I do not want to leave any work for staff in Check karein as much as possible."*
S427 read every one of the 39 pictures still parked at the 11-Nov database copy (counts only): 6 carry a 1–3-digit photo number
("NAME 2"), 3 are a second copy of a photo already filed, 18 have a name that matches no patient anywhere, 6 a one-word name several
patients share, 5 a known name not on the film's day. Three rules are added to the S752/S772/S776 re-try, for a parked picture only:

- **(a)** a 1–3-digit number in the name is the photo's own number — not a clinic ID — when no patient who came on the first-seen day
  (or the day before), or on a date printed on its film (a day either side), has that ID, and the name is not that ID's patient. The
  re-try reads the name without it; every earlier rule then decides as before. Nothing is stripped before the film has been read.
- **(b)** a picture with the very same file name as a copy already filed on the ID its film prints — the film's same date(s) and ID —
  whose X-rays of that day all have their photos (study count known) is a second upload: it goes to *X-ray inbox / _filed /
  duplicates* (never deleted) and is never filed twice. A second view is always named apart ("NAME 1234 2"), so it never qualifies.
- **(c)** nothing is filed by itself while its film prints the clinic ID of ANOTHER patient who came that day (0 of the 393 pictures
  filed so far would have been held by it).
- A film date that is no calendar date is ignored instead of stopping the re-try (it would have stopped S772 too).

`/root/finance/records.py` bae45d82 (S776) → b13d11f5, built by `make_s782.py` (exact anchors, each once). Nothing else changes.
**On the 11-Nov copy:** 39 parked → 1 filed (a photo number), 2 to duplicates (second uploads) → 36.
**Cold review** (a fresh agent): five defects found and closed before install — a planned duplicate never re-asked, or stuck once no longer one; a second VIEW could
have gone to duplicates (now: the very same name only); an impossible film date stops every re-try; a short ID stripped before the
film was read. **Walks:** S782 16/16, CONTROL red on the live file (10 of 16); S776 17/17, S772 39/39, S752 50/50, S373 20/20 on the
new file. The installer re-runs all of them on the box, and the proof on a copy of the live database.

**Install** (after the publish), one line on the server:
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s782kit && cp -rp /root/deploy/repo/deploy_kits/S782_XRAY_LEFTOVERS /tmp/s782kit && bash /tmp/s782kit/install_S782_XRAY_LEFTOVERS.sh
```
Undo: `bash /tmp/s782kit/install_S782_XRAY_LEFTOVERS.sh --undo` (back to S776, bae45d82).
