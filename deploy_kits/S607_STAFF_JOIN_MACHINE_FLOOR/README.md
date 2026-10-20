# S607_STAFF_JOIN_MACHINE_FLOOR — the machine card offers only this joining's fingers (S331, 20-Oct-2026)

Follows S606 (Add staff, installed 18:36 IST). Reading the live page after the install: the machine card offered two
fingers from the machine's **set-up day, 07-Oct** — number 2 (very likely the owner's own administrator finger) and the
retired 100. A "Yes, this is Arjun Dev" there would have given the owner's finger to Arjun Dev.

**Now:** only fingers pressed from the day before the joining was opened are offered, and only those can be linked
(the server refuses any other). `staff_easy.py` and `staff_easy.html`; nothing else.

**The one line (VPS):**

    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S607_STAFF_JOIN_MACHINE_FLOOR/install_S607_STAFF_JOIN_MACHINE_FLOOR.sh

**Proven by:** `walk_s607.py` — 38 checks on scratch copies (S606's 36 + an old unknown finger is not offered and
cannot be linked); on the S606 files the same walk goes RED (it links the old finger). Rehearsed on a made-up root:
DRY, install, ALREADY INSTALLED, `--undo`. **Undo:** `--undo` puts the S606 files back (`/root/s607_backup/`).
