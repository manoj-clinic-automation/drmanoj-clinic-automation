# S616_OWNER_TASKS_TILE — the tasks and Voicenotes panel gets a door on the owner's home (S336, 22-Oct-2026)

**The owner, his board note 06:21 IST:** *"we developed a messaging and tasks app and connected with voiceapp, cant see
it in my portal"*.

**What was there.** The tasks section (S493/S495: he gives a task; the person answers done / can't / a note; he replies
or closes) and the Voicenotes lines (S514; 36 lines waiting since 12/14-Oct, none used) live on his panel
`https://followup.dr-manoj.in/finance/aaj`. His portal home had no door to it: staff have *Aaj ka kaam*; his home has
*Today* (the console).

**What it does** (two files, exact counted edits in `edits_s616.py`):
- `/root/portal/portal.py` 3be15f45 → new: a blue **Tasks & messages** tile on his home, under *Today*, with a live
  line — *36 Voicenotes lines waiting · 2 tasks open · 1 answered by staff* — opening the panel on Tasks. It shows only when the
  Voicenotes door answers the login as the panel's owner: Dr Bhawna, the staff and a finance outage see the home as before.
- `/root/finance/aaj_panel.html` 36bd57bc → new: `?tab=tasks` opens on Tasks; the page is named *Staff lists & tasks*.

**The one line (VPS):**

    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S616_OWNER_TASKS_TILE/install_S616_OWNER_TASKS_TILE.sh

**Proven by:** `walk_s616.py` (26 checks: every login's home from both files against the live grants — same tiles and
groups; the doctor's page is the old one plus the two blocks; every script parses; the panel byte-identical but for the
three edits); the S586 files go RED. In the rehearsal a real browser at 375 px: owner with 36 lines → shown with the
line; owner with nothing → shown, 'Give a task'; not the owner (403) and finance down (502) → hidden; the panel opens
on Tasks for `?tab=tasks` and as before without it.

**Undo:** `--undo` puts both old files back (`/root/s616_backup/`) and restarts the portal.
