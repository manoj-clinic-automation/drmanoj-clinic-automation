# S972_EVENING_WIDENED — the evening check widened (the parent · S539 · 27-Nov-2026 · D1099, D1100 · K1 of S537_MORNING_CHECK_FINAL_BUILD_PLAN · Opus)

His words 14:31 27-Nov: *"skip cash to UPI corrections, only revenue mismatch flow to be kept; I don't want any corrections in Docterz
the next morning etc, only same-day Docterz edits should be there"*; 15:09: *"finalise now and build in fresh chat"*.

| file | from → to |
|---|---|
| `/root/finance/evening_check.py` | b3c5bebb (S960) → see `TO_PINS.md5` |

`parchi_desk.py` is NOT changed (its PLANNED line released): the desk already mounts every door `evening_check.init` adds.

**What changes.** On the same export, the same one push per export and the same desk box, beside the slips Docterz does not carry,
the evening compares the MONEY of each patient's X-ray / procedure slip lines with the export (X-ray = Laboratory + Radiology,
net = amount − discount, as `revenue.py`), for every patient with a slip today, and names:
1. **chhoot** — Docterz billed the full rate, the slip carries a chhoot → "Docterz mein chhoot ₹100 lagaiye";
2. **kam** — the slip carries more than Docterz → "Docterz bill mein ₹300 jodiye" (when Docterz holds a chhoot the slip does not:
   "chhoot sahi hai to parchi par bhi likhwayein, nahi to Docterz mein hataiye");
3. **twice** — Docterz billed one slip line twice → "dono taraf hua tha?" **[Haan, parchi theek karo]** (writes the OTHER side —
   R↔L — of that line, offered only for a line with a side and no chhoot; with no side: "do baar / doosra view?", no tap) / *Nahi: Docterz se ek hataiye*; and the mirror, the slip carries a line
   twice and Docterz once → **[Nahi, parchi se ek hataiye]** (removes exactly the repeat; not when a chhoot entry waits on it) /
   *Haan: Docterz mein doosra jodiye*;
4. **more** — Docterz has more than the slip, or a kind the slip lacks → "kaunsa sahi?" (Docterz, or Shavez's parchi);
5. **head** — the patient's X-ray + procedure total agrees, the split does not (an X-ray billed as a procedure, or back) → ONE line
   "jod barabar, head galat: Docterz mein sahi head mein daaliye", no tap; that patient leaves the missing list for those heads.

Each line clears by itself when the next export (or the slip) agrees. The push: missing only → the S960 words exactly; shapes only
→ "N farq — Docterz aur parchi"; both → "N parchi Docterz mein nahi · M farq"; all agree → "✓ 26-Nov: Docterz aur parchi sab mile".
**Payment mode is not compared.** Left out: a patient with a radd today (the morning matches the refund), a pair answered on his
"Slips not in Docterz" list, a kind the export lacks altogether (S960's own missing line). The probe's line gains `head`, so the installer reads `reader_same` $23, `reader_diff` $25, `maxday` $27. `EVCHK_SHAPES=0` turns the shapes off
(the S960 check exactly as it was). One additive column, `evening_check_push.shapes` (keys `shape:slip:kind`, no names).

**Decisions made in the build (stated, not asked):** the two slip-side writes are the only taps — the Docterz-side answers are
words beside the line (the next export is the proof); "kaunsa sahi?" has no slip write (the service cannot be read from an amount —
review Q2), Shavez corrects the slip on the desk; a "Haan" second line copies the first without a chhoot (a chhoot needs its approval
road); the five shape names are `chhoot · kam · tdoc · tslip · more`.

**Proof.** `walk_s972.py` (made-up database and exports): **S** the sixteen made-up lines exactly (two same-price lines → `more`; repeats on other slips → no write), X-ray billed under procedure named once, and the eleven that must not
be named (radd, his answer, free line, rejected chhoot billed in full, radiology column, two Docterz rows, no ID, no slip, yesterday's
slip, another day's row, a non-UID row) · **R** the reader · **P** one push per export: mixed, again, `--status`, corrected → cleared,
shapes only, the first clean, shapes off (S960's words), missing only (S960's words exactly), an afternoon export · **A** the two
answers, each refused twice, for every wrong line, and when the line's items changed since the box was drawn · **K** the desk box, English, the three doors mounted by `parchi_desk.init`,
403 · **Y** yesterday's line. CONTROL: the walk on the live code as it is goes red at S1. **S960's own walk** (a copy, unchanged)
on the TO with the shapes off: ALL PASS with the live clock's send road (with the shapes on its one odd fixture — a procedure
billed as discount only — is named, as it should be: 8 known differences, all that fixture). `make_s972.py` remakes the TO from the
live bytes (19 anchors, each once). `probe_s972.py`, on the box, read-only, counts only: the last 30 exported days — the shapes the
evening would name on the slips as they stand, and the reader's money against the tracker's own `clinic_day_line`; **an error, no
day read, more than 3 lines a day, or the reader off on more than a quarter of the pairs stops the install.** `rehearse_s972.sh`
(23 paths on a made-up root). Seven mutants of the reviews' fixes each turn the walk red.

**Cold review:** NOT SAFE → fixed: 1 MUST (two slip lines at the same price — "Haan" could copy the wrong one; now `more`, no tap) and
6 SHOULD built in — the tap carries the item ids it showed and is refused if they changed; check and write in ONE immediate
transaction (two taps cannot both write); repeats spread over other slips get no write; the tap refreshes the box, not the whole
desk page (a half-typed slip survives); the probe gates on the worst single day (≤ 8) and on at least 5 money pairs; X-ray billed
under procedure is named once. Noted (not changed): with the shapes off, the status line still says "shapes 0"; a pending chhoot is
read as given, as the morning check reads it.

**Second look:** NOT SAFE → fixed: 1 MUST (an X-ray billed under the procedure head, money equal, offered a "Haan" that wrote a phantom
line — now one `head` line, no tap) and 3 SHOULD built in — the same head rule for a kam/more pair; the copy is the other side (R↔L),
no tap without a side; a failed tap shows words. **Re-look:** SAFE, 0 MUST; built in: no `head` line when the slip carries a repeated line (two errors at one price could
otherwise move a real procedure). Noted: a Docterz discount entered under the other head beside a `chhoot` line.
