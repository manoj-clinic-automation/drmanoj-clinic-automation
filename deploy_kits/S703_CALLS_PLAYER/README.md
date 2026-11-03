# S703_CALLS_PLAYER — the Call Console's recording player · the parent · session 382 · 03-Nov-2026

**For the owner, in two lines.** On the Call Console, tapping a recording now opens a player at the foot of the screen: *Loading…* until the sound starts, then a progress bar with the time played and the length (e.g. 0:42 / 2:15); the same button pauses and plays, a tap on the bar jumps there, and if the recording cannot be fetched it says so in plain words. The row's own button shows the time and fills as it plays.

## Why
The owner, 10:45 IST 03-Nov: *"when I tap on it, only the color changes, and I do not know whether it is working or not. So need a progress bar there when it is playing."* S698's button played the sound with nothing on screen.

## File
| live file | FROM | TO | what |
|---|---|---|---|
| `/root/portal/calls_console.py` | a0f58fec (S698) | e0f9312a | 4 counted edits (`make_s703.py`, re-run on the box): the player's style; the player bar's markup; `playJk()` rewritten with `plToggle()`, `plSeek()`, `plClose()`; the page's foot note. No route, no query, no other part of the page. |

## Proven (S382, the cloud workspace, python3 + flask + Chromium, S698's made-up data — phones 5000000xxx)
`walk_s703.py` **24 of 24 green** in headless Chromium against a stand-in recording route (a made-up 12-second tone; one key answers 404, one answers after 2.5 s): the bar hidden until a recording is opened; tap → *Loading…* or the time at once; while playing *0:0x / 0:12* and the bar moving; the row's button *❚❚ time* and filling; pause stops the time (▶ on both); the row's button plays on; a tap at ¾ jumps to ~0:09; at the end *Finished · 0:12* and the button restored; a second recording stops the first; × closes everything; a recording the server lacks → a red plain-words line, the button restored; the three kinds of button — Needs-you *Listen* (the bar says *Recording — <name>*), a timeline row (*Recording — <name> · <time>*, no menu or button words), a slow one (*Loading…* with the pause sign, then the time); a message pop-up sits above the bar; no script error on PC or phone; at 390 px the bar fits, a 16 px time, the red line wholly on screen with room kept under the page. **Control** on the live file: 19 red · 5 green. Mutants: 4 of 5 caught (the 5th — the audio's own error event — is covered twice over by the play() refusal on a missing file).
Independent cold review: SAFE TO INSTALL; its should-fix built in (pause sign while loading, the label from the name and time, the pop-up lifted above the bar, room under the page measured from the bar, the lock's owner line, the Listen and timeline buttons and the phone page in the walk).
`render_s703.py` (runs on the box too): the page rendered through the live and the new module — the new carries the player, and with the four S703 pieces taken out it is the live page **byte for byte**; control (the live module twice) red.

## Install (on the server, after the publish; window 04:00–23:30 IST)
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s703kit && cp -rp /root/deploy/repo/deploy_kits/S703_CALLS_PLAYER /tmp/s703kit && bash /tmp/s703kit/install_S703_CALLS_PLAYER.sh
```
## Undo
```
\cp -p /root/portal/calls_console.py.bak_S703 /root/portal/calls_console.py && systemctl restart clinic-portal
```
