# S980_FILM_COUNT_RISE — the X-ray film morning count, stuck since 09-Nov

*The parent, S545, 28-Nov-2026. His ask 18:15: "the film log is not showing the machine counts, the box data is wrong". His fact 18:39: "a new box can only go in when the current one comes down to 0 — many times in the middle of the day".*

**What was wrong.** The last count saved was 09-Nov (8×10: 21 left). A new box went in when that box ran out, so the machine's figure went UP. The morning screen let staff save a higher figure only when the last count was 20 or less — it was 21 — so every save since was refused ("badhi kaise? Dr Manoj se confirm karaiye"), with no way through. The films left, days left and spare boxes all stood still at 09-Nov.

**What changes.**
- A higher figure is a new box: staff tick **"Haan, naya box lagaya gaya"** and Save — whatever the last count was. The tick is always shown.
- Still refused: a rise of 20 films or fewer from a last count above 20 taken within the last 3 days (a typo — a new box never gives that in so short a time). Across a longer gap any rise with the tick is a box load.
- "New box" ticked while the figure is NOT above the last count: refused once, the typed figures kept and the tick cleared, with both ways out on the screen — no new box: just Save; a box did go in (more than a box used since): Save and tell Dr Manoj (the films used will read a box short).
- When staff save a rise from above 20, he gets one line on his phone ("X-ray film: a new box marked by …").
- His own Save takes the same tick.
- Everything else on the page (used, gaps, spare boxes, the order line) is unchanged; the box that went in is counted by the figures as before.

**File.** `/root/finance/xray_film.py` 5e3a2bd1 → a5690a40.

**Install** (one server line, any hour):
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s980kit && \cp -rp /root/deploy/repo/deploy_kits/S980_FILM_COUNT_RISE /tmp/s980kit && bash /tmp/s980kit/install_S980_FILM_COUNT_RISE.sh
```
**Undo:** `bash /tmp/s980kit/install_S980_FILM_COUNT_RISE.sh --undo`

**Proof.** walk_s980 (made-up counts, through the real routes) 15/15 on the TO, two mutants red; on the FROM it reproduces the stuck case (the save from 21 refused "risen") — the control; the live shape on the 28-Nov copy: the film log and list pages byte-identical for him and staff, only the staff morning page differs (the tick now shown); rehearsal on a made-up root.

**Cold review (NOT SAFE, 2 MUST — both built in):** across a long gap (19 days) a real new box can show a figure 20 or less above the last count — the typo guard now applies only to counts 3 days apart or less; a ticked new box whose figure fell was silently saved as a small fall (a box of films lost from the figures) — now refused with "Dr Manoj ko batayein". SHOULDs built in: his own message wording; the old rule's docstrings marked superseded. Noted for him: a gap with two boxes used shows only the page's "check" flag; the second box is his to enter.
**Second look (NOT SAFE, 2 MUST — both built in):** the 'boxlow' message sent him to a correction form that refuses the same entry, and told staff not to untick — a stray tick on a normal fall would have left the count stuck again; now the message gives both ways out, the figures come back typed and the tick cleared (walk J: a stray tick, then Save, saves).
