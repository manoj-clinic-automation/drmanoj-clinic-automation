# S891_HOME_REDESIGN — the owner's portal home redesigned

**The parent, S489, 19-Nov-2026.** His word 06:24–06:37: the folder tiles were flat (heading and inside names in the same type and
colour; the inside pages the same colour as the folders), and the top of the home took most of a screen. His "ok" 08:12 on the live
preview (in the built-in browser, measured at his PC's size and the opened Fold's).

**One file:** `/root/portal/portal.py` 9da49bd1 → TO (S890's TO). Built by `make_s891.py` from the FROM read out of the 19-Nov bundle,
five exact anchors, each found once:

1. A `<style id="s891">` block at the start of `PORTAL_HTML` (the home only — the Forms page shares `HOME_HEAD` and is untouched):
   - **Folders** — coloured cards, each folder its own colour (top edge, icon well, count pill); the folder name 16 px bold white;
     the inside names one quiet grey line, clamped to two lines.
   - **The open panel** — tinted in the folder's colour, its own heading.
   - **The pages inside** — LIGHT cards (#eef4f9) with dark, medium-weight type and the folder's colour on the left edge.
   - **The top** — the call-alert card one slim bar; Today's four numbers in one row with the feeds line in its heading; Tasks
     beside Today (from 700 px wide); health + the four counts one row of pills.
   - **Phones / the opened Fold (≤ 900 px)** — folders as icon + name, four to a row (two on a narrow phone); the red Renewals count
     stays on the Accounts folder.
2–4. The call-alert card's title, line and button in English for role doctor; every staff home keeps the Hindi.
5. A doctor-only script that turns the bar's own messages into English on their way to the page.

**Measured on the preview:** the opened Fold (884 × 900) — the whole home ends at ~790; his PC (2371 × 1180) — ~900; a phone
(412 × 800) — ~1.6 screens (was 2.2).

**Proof:** `walk_s891_portal.py` — the real portal imported with made-up secrets, the home rendered for the owner and a staff login
(13 checks: the block once, every folder coloured, the CSS byte-for-byte the approved preview, Forms untouched, S890's lines kept,
staff Hindi kept, English for him, the script run in node against the page's own messages, the file = FROM + exactly these pieces).
Control on the live file red as it must be. `rehearse_s891.sh` — dry, install, again, undo, undo again, red rollback, a broken home,
drift, tamper, lock, portal down.

**Install (one line, root, on the VPS):**

    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s891kit && cp -rp /root/deploy/repo/deploy_kits/S891_HOME_REDESIGN /tmp/s891kit && bash /tmp/s891kit/install_S891_HOME_REDESIGN.sh

**Undo:** `bash /tmp/s891kit/install_S891_HOME_REDESIGN.sh --undo`
