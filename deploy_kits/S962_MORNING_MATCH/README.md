# S962_MORNING_MATCH — the day check becomes the Morning Match, part 1 (the parent · S529 · 26-Nov-2026 · D1080 kit C · Opus)

His "ok" 12:58 IST 26-Nov on the Morning Match mock-up v2.1 (artboards 3, 4, 5): https://claude.ai/artifact/KVC77sMev1YwczYXWy4PzF
His words 12:21: refund — "sometimes docterz might also get this cancellation, so system shd behave accordingly"; morning — "drop
cash / upi, as its already on physical register"; the back-date list — "shavez also sees it so he can remind me" · "Automatic".
Closes **F-1678** (a refunded / radd slip dropped out while Docterz kept the bill — false cards) and **F-1679** (Shavez got "Added"
on slips only his login can back-date).

| file | from → to |
|---|---|
| `/root/finance/day_check.py` | d5c95ea9 (S846) → see `TO_PINS.md5` |
| `/root/finance/slip_adjust.py` | 41c55a99 (S442) → see `TO_PINS.md5` (slip_adjust gains `refund_t`, added on first use) |
| `/root/finance/slip_log.py` | 3553a965 → see `TO_PINS.md5` (the radd form `_radd_form` only) |

**What changes.**
1. **A radd after billing is matched both ways.** Docterz kept the bill → "billed · refunded" (or "billed · money never taken");
   Docterz cancelled it too → "cancelled · refunded". No false "No OPD parchi" / "No X-ray parchi" card, no false money card, never
   subtracted twice. The register's book is read as written NET of a refund (the 23-Oct database: a refunded fee was never written),
   so a radd's line Docterz still bills is taken out of Docterz's side — as clinic_money's S442 already does for the morning match.
   An OPD radd covers one consultation of its ID; an X-ray/procedure radd its ID's X-ray and procedure lines (only lines of its own
   amounts when the ID has another live parchi that day). A bill paid two ways whose every line is a radd's goes with it.
2. **A slip Docterz does not carry goes to HIS back-date list by itself** — the same rows as `/finance/clinic/not-in-docterz`. Its
   money is still placed against the register; no staff "Added" / "Not paid" / "Free" for it. A part-billed line (Docterz has the
   bill, short) stays a staff card as before. When his answer says money was taken but the register does not hold it, one
   "check by hand" card says so.
3. **The day in one line** on top of the day check: Register = Docterz + slips not in Docterz − refunded / never taken + Docterz
   entries still missing + not explained (each part shown only when not zero; staff read it in Hinglish). What matched is folded:
   "✓ N patients match · M refund / radd matched".
4. **The named staff see his back-date list** (Shavez, Bhati, Shivani, Alisha — no other login) read-only, with **"Paise liye hi nahi"** on a row the register
   does not hold (writes his list's own `nid_mark` 'free', by their login — named as theirs, never as his) and **"Dr sahab ko yaad dilayein"** (a push to his login
   through the call-back clock's own road, counts only, once in three hours across the days — a push that did not go does not count; two taps at once send one; only from the live database).
5. **His console line**: "<day>: all matched", or the counts — "N to back-date · staff fixing M · K to check by hand · ₹X not
   explained". Only rows his own list carries go to the back-date list; anything else keeps its staff card as before.
6. **The slip desk's radd** asks **Cash mein lautaye / UPI se lautaye / Paise liye hi nahi**; a refund shows "↩ Refunded · Cash ·
   26-11 12:40" on the slip at once (the approval still follows, as before).

**Not in this kit (part 2, his look first):** the register's own refund line (filled from the tags; staff confirm) and the drawer /
bank effects of it — the register stays as the counter writes it.

**Proof.** `walk_s962.py` — 39 checks on made-up days (every case of the paper, and the cold review's: a refund on a bill paid two ways; two parchis of one ID at one amount; a failed push never blocks the next reminder; only the named staff tap; a visit Docterz's clinical report knows stays a staff card; a UPI refund on a split bill comes off the UPI leg; two lines of one slip make one row), ALL PASS on the TO; on the FROM it goes red at T1
(a refund Docterz kept still makes a false parchi card). `probe_s962.py` — the live database, read-only, counts only: on the 26-Nov
copy, 40 days, 29 checked, 0 errors; 8 back-date rows (one per slip and kind) replaced staff cards, the one real radd (23-Oct) matched with the same
money as before; every day whose line shows money 'not explained' (10 of 29) already carried a check-by-hand or patient-not-found card before. `rehearse_s962.sh` — every installer path on a made-up root.

**Install** (one line on the server, after the publish):
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s962kit && cp -rp /root/deploy/repo/deploy_kits/S962_MORNING_MATCH /tmp/s962kit && bash /tmp/s962kit/install_S962_MORNING_MATCH.sh
```
Undo: `bash /tmp/s962kit/install_S962_MORNING_MATCH.sh --undo` (the `refund_t` column and any answers stay; harmless).

No patient name, number or clinic ID in any file of this kit (F-185).
