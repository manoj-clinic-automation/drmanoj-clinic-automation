# S836_CHECK_KAREIN — Check karein refined (D979 item 3)

The parent, session S465, 14-Nov-2026. Built from the approved mock-up (seven boards, 14-Nov) and S450_XRAY_LAB_FILING_STUDY §I.

**What changes on the screens**
- **Shavez and the doctors — "Din ke hisaab se"** (the first chip, opened by default): the last 7 days, each date with its X-rays
  (filed / baaki / abhi samay hai / dikkat) and blood tests (aayi / baaki / abhi samay hai); a date opens its patients.
  His X-ray page (`/finance/records/xray-check`) carries the same strip in English ("Last 7 days").
- **Reception — "Kal ki X-ray"** on top from 9:30 am: the last X-ray day before today, how many, how many filed, the rest by name
  ("aaj 3 baje tak", after 3 pm "abhi"), and what is still baaki from the 7 days before it. A row leaves by itself once filed.
- **"Kya yeh photo inki hai?"**: once a day's upload window is over, a day with exactly one X-ray without a photo and exactly one
  unplaced picture asks, one tap (Haan / Nahi; Nahi is remembered). It files by itself only when nobody answered the picture, it is
  not a child's, its day is not a guess and is over, its name fits nobody else who came that day ±1, no number on it is another
  patient's, AND it carries a positive sign (the name fits him, or the ID read on the film is his or one keystroke off — never a number in the file name, which may be the camera's counter) — shown under
  "Filed by themselves" with Move. Otherwise it only asks. (Tightened after the cold review: R1–R4, and the second look's camera-counter point.)
- **"Not in Docterz" = complimentary** (his word, 13-Nov 19:27–19:34): one tap "Muft X-ray" (or "Parchi bana di") closes it;
  the payment-gap wording, the red tile and his console's red Needs-you line are gone.

**Not in this kit:** lab reports with no ID — suggested patients (a later kit; the no-ID list lives in `slip_log.py`).

**Every state comes from the code that already decides it** — 'baaki' is records.xray_items' open `xray_missing` (S834's due rule,
not copied), 'abhi samay hai' is `records.XRAY_DUE` not reached, blood 'baaki' is check_items' open `blood`.

**Files** (built by `apply_s836.py` from the live bytes; every anchor exactly once):
- `/root/finance/check_screens.py` a8a3552c → f3c16787
- `/root/finance/owner_console.py` 16ebd73d → 72da1da8

**Proof.** `walk_s836.py` 40/40 (three mutations go red) on a copy of the 13-Nov database with made-up patients on made-up January-2027 days (IDs made at
run time above every real one); the control on the live files goes red. The earlier walks S787/S788/S789 give the same result on old
and new; S791's walk reds only on the wording and the console line this kit removes by design. Both pages' scripts pass `node --check`.

**Install:** the publish, then one server line (the installer's header). `DRY=1` first if wanted; `--undo` puts both files back.

**Known, left for a later kit (second review, LOW):** a waiting picture that already carries a patient's ID but is dated more than a day before or two days after the X-ray day does not count as his photo 'on its way' for the pair question.
