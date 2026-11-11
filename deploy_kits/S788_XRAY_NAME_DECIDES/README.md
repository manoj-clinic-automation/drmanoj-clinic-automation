# S788_XRAY_NAME_DECIDES — the name decides when the number is one digit off

**The owner, 11-Nov-2026 09:14 IST:** *"For such cases, the name should be the deciding factor where all other parameters match and the
ID is only slightly off"* — S. (24-Oct): the film was read as another patient's ID (another X-ray patient of that day, his photo filed); her ID is one digit off it, and her two other photos that day were filed there. The safety rule of S782 (c) had held it for a person.

`/root/finance/check_screens.py` 597dd8c9 (S787) → TO. Before each filing plan, `s787_auto` now first asks `_s788_name_decides`: the
photo gets the ID of the patient when its name — word by word, or with the spaces taken out, allowing the usual spelling — is that of
exactly ONE patient who came on the film's day ±1 (so nobody else who came has a name like it), he had an X-ray (slip or Docterz)
those days, and there IS a number (read on the film or written in the file name), every one of which is his ID or one digit off it —
even when that number is another patient's. Written as "system · S788", filed by the next filing run.

The reason line on both pages now says what the film reads: *"No ID in the file name; the film reads NNNN (the name of that ID)"* instead of
"No clinic ID on the photo".

On the 11-Nov copy: 3 photos (the 24-Oct one among them); none where a number was far off; none when a second patient of the same
name came those days (checked with a made-up one). **Walk** 8/8 (+ S787's walk on the new file); the CONTROL red on the live file.

**(b) The lab list, the owner 09:22 IST:** *"How about filing these reports automatically and not holding them just because there was no
blood slip"* — every report on "Lab report came, no blood slip" is ALREADY filed in the patient's record (the lab's mail files it);
the list only asked whether a blood slip was made. Now: those reports leave Shavez's Check karein and his Aaj ka kaam count; his own
page keeps them as a list for information ("Lab report filed, no blood slip" — the report, no buttons). Only a report that looks like
the WRONG ID (the lab's name is another visitor's of that week; 1 of 42 on the 11-Nov copy) still asks, as before.

**Walk fix:** S787's walk (re-run by this installer) assumed nothing was yet on the "Not in Docterz" tile; on the live database the
owner had already marked one, so two of its checks went red and the first run of this installer stopped (nothing written). The two
checks now look only at the card the walk itself marks. A red walk now prints its red lines.

**Install** (after the publish), one line on the server:
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s788kit && cp -rp /root/deploy/repo/deploy_kits/S788_XRAY_NAME_DECIDES /tmp/s788kit && bash /tmp/s788kit/install_S788_XRAY_NAME_DECIDES.sh
```
Undo: `bash /tmp/s788kit/install_S788_XRAY_NAME_DECIDES.sh --undo`.

**F-1264 (S430, 11-Nov-2026):** a patient's name and clinic IDs were taken out of this kit's papers (names -> initials). Its files therefore no longer match the installer's checks: the kit is history, superseded by `S791_XRAY_MATCH_RULES` -- do not re-run it.
