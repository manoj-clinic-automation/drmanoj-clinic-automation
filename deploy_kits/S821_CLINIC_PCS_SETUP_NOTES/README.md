# S821_CLINIC_PCS_SETUP_NOTES — the Medical PC's card says how that PC is set up now (S453, 14-Nov-2026)

**The owner's word (14-Nov-2026 05:57 IST):** the Medical PC's card must say how that PC is set up now, and that its kit
keeps itself current.

**The one line (VPS):**

    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S821_CLINIC_PCS_SETUP_NOTES/install_S821_CLINIC_PCS_SETUP_NOTES.sh

`DRY=1` before `bash`: every gate, the rebuild, the walk and its control — nothing changed.

**What changes** (`/root/finance/pc_kits.py` 9c2b3615 → 4191e447, 12 exact counted edits in `edits_s821.py`; the page is
`https://followup.dr-manoj.in/finance/pcs`, owner only; `clinic-finance` is restarted):
- an entry of `PCS` may carry `setup_now` (`{"noted": date words, "items": [lines]}`). Its card then shows a block
  **How this PC is set up now** — below the *Only a person can do these* list, above the *Kit on the server* line — the
  lines as a list and a last small line *Noted <date>.* The block has its own class (`.setnow`); its CSS is put into the
  page only when a card shows the block;
- the **Medical PC** carries one, noted 14-Nov-2026: the cable and (since 13-Nov-2026) the Wi-Fi dongle; the dongle in
  the working FRONT USB port and the pen drive in a REAR one; put them back the same way after a reinstall, a repair or
  a move;
- an entry may carry `kit_keeps`: one sentence right after *Kit on the server: <version>, packed <date>.* and before
  any *Last: …*. **Medical:** checked every night; a changed program is repacked into the kit by itself, or the night's report says
  why not (a NEW program is not added — kit S822); the new kit shows on the page after the next publish AND the
  next server line (nothing on the server pulls the clone by itself — only a kit install line does).
  **Reception:** checked every night against its recorded (pinned) programs, a difference is reported; not repacked by itself. Both describe
  `pc_kits_current.py` (S723, nightly on Dr Manoj's PC). **Dr Manoj's PC** has none — its kit restores from the nightly copy;
- every one of these strings is plain text and goes through `html.escape`.

**What is untouched.** Every route and its methods, the owner-only gate, the cross-site check, the one-time codes, the
two api doors, both setup files, the phones, `setup_notes.py` and its *Other set-ups* section, the page's existing CSS.
A PC without the two keys renders exactly the bytes it rendered before. Nothing is written; no database change.

**Proven by:** `walk_s821.py` — 24 checks on made-up kits and health rows, both files mounted on Flask as the live app
mounts them: the block, its three lines and *Noted 14-Nov-2026.* on the Medical card only and in its place; each kit
sentence on its own card, before any *Last: …*, none on Dr Manoj's PC; with the two keys taken off at run time the page
is the old page byte for byte (with a trail, without one, and with the Medical kit absent); markup in a line is shown
as text; a note out of shape shows nothing and the page still opens; the routes, the gate, the 404 for a PC without a
kit, the cross-site refusal and the Medical setup file are the same old and new; *Other set-ups* is the same byte for
byte. **The control:** pointed at the 9c2b3615 file, 11 of the 24 go RED. The installer was rehearsed on a made-up root
with stub `systemctl`, `curl` and `sleep`: DRY, good, again, DRY-undo, undo, undo over a foreign file, undo with no
backup, wrong FROM, lock held, service dead after the copy (the old file back), SUMS broken, kit file not live + edits.
NOT done here: a look at the page on a 375 px screen; a run on the server itself.

**Undo:** `bash /root/deploy/repo/deploy_kits/S821_CLINIC_PCS_SETUP_NOTES/install_S821_CLINIC_PCS_SETUP_NOTES.sh --undo`
puts the 9c2b3615 file back from `/root/s821_backup/` and restarts `clinic-finance` — only when the live file is this
kit's and that backup is the file it replaced.

**The standing rule this follows (S617):** a kit that changes a PC, a phone or a set-up updates its card on this page in
the same kit — when the Medical PC's cable, dongle or pen drive moves, the `setup_now` lines move with it.
