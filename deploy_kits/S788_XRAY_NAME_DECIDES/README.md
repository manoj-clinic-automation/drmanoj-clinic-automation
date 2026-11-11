# S788_XRAY_NAME_DECIDES — the name decides when the number is one digit off

**The owner, 11-Nov-2026 09:14 IST:** *"For such cases, the name should be the deciding factor where all other parameters match and the
ID is only slightly off"* — SUNDARWATI (24-Oct): the film was read as 8344 (another X-ray patient of that day, his photo filed); her ID
is 8343, and her two other photos that day were filed there. The safety rule of S782 (c) had held it for a person.

`/root/finance/check_screens.py` 597dd8c9 (S787) → TO. Before each filing plan, `s787_auto` now first asks `_s788_name_decides`: the
photo gets the ID of the patient when its name — word by word, or with the spaces taken out, allowing the usual spelling — is that of
exactly ONE patient who came on the film's day ±1 (so nobody else who came has a name like it), he had an X-ray (slip or Docterz)
those days, and there IS a number (read on the film or written in the file name), every one of which is his ID or one digit off it —
even when that number is another patient's. Written as "system · S788", filed by the next filing run.

The reason line on both pages now says what the film reads: *"No ID in the file name; the film reads 8344 (Ram Kumar)"* instead of
"No clinic ID on the photo".

On the 11-Nov copy: 3 photos (SUNDARWATI to 8343 among them); none where a number was far off; none when a second patient of the same
name came those days (checked with a made-up one). **Walk** 8/8 (+ S787's walk on the new file); the CONTROL red on the live file.

**Install** (after the publish), one line on the server:
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s788kit && cp -rp /root/deploy/repo/deploy_kits/S788_XRAY_NAME_DECIDES /tmp/s788kit && bash /tmp/s788kit/install_S788_XRAY_NAME_DECIDES.sh
```
Undo: `bash /tmp/s788kit/install_S788_XRAY_NAME_DECIDES.sh --undo`.
