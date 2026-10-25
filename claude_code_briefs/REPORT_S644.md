# REPORT_S644 — S644_BUYING_MODEL (Kit II, the buying model) · installed 25-Oct-2026 08:2x IST by the owner's server line

## For the owner
- The system's own order list is now made the new way behind one setting, **How the list is made: Levels**, on your approvals page under *Buying rules for medicines* (read live on your page at 08:2x IST: the line, the button *Change to Fixed days -- as before*, the 23 suppliers' rhythms, the 11 settings; no red anywhere).
- **Nothing changed for the staff.** Darpan's Marg sheet stays the order; the new list is made at 09:00 and scored every night in the background. The first list the new way is made tomorrow, Monday 26-Oct, at 09:00.
- Your page's weekly score today still reads the OLD engine's shadow list (15 % of what was bought was on it beforehand; 54 % of what it listed was bought within 14 days; 9 medicines ran out, 4 of them listed in time). The new list's first week is scored on the night of 1-Nov; the 14-day figure a week later. D673's bar for the switch: three weeks at 85 % / 80 % / no more stock-outs than Darpan's sheet.
- Old (fixed days) is one button away and was proved line-for-line equal to today's engine before the install.

## For the chat
**Pins FROM → TO (built from the 25-Oct 01:35 IST bundle; the installer rebuilt them from the box's live bytes and read them back; the 26-Oct bundle confirms):**
order_rules.py 8d078dbe → 8a116cbda12e0e2173925c1ae73ed3f8 · porders_s454.py 673883e8 → 438714b8d5c094a9ee7cdc71731b44e0 · spine/spine_read.py 10697b38 → ad441b1dabf489e1bd54bb5aa62310a4 · spine/order_rehearsal.py 104d366d → c5d019ef62d1231502dbc28f2b7833ef · spine/selftest_spine.py 7d0edb4a → a05229e1b74f5cf629d36e0f9434aeee · finance_ui/finance_approvals.html a7016a4e → 885f6f31571ae19d20b8cb065080ad0b (the parent's template; finance_app.py not touched).
**Backups:** `*.bak_S644_<from8>` beside each file; `finance.db.bak_S644_<stamp>`. **Restarted:** clinic-finance once. **Crontab:** unchanged. **Data step:** four columns on order_supplier_rule (rhythm_mode seeded once: Kedar fixed, 22 learnt), eleven order.* settings, bill_days90/rhythm_at refreshed, order.model = levels (order.source = marg_sheet read, not written). The installer's own output stands in the owner's terminal (his paste: `S644_BUYING_MODEL: DONE`); the chat did not see its middle lines.
**Live read-back (sub-agent, 08:2x IST):** the fold as above; Kedar's rhythm row shows "—" for last buy (fixed mode: the calendar, by design); no "last list stood on" line yet (the process has made no plan since the restart; the 09:00 prepare writes it).
**Not done, said:** Darpan's tab header line (B.2a) — his tab is unused on marg_sheet; goes with the kit that moves the source. B.6 not built (charter). The kit's replay reads the tables of the nightly copy (the reference's store), not an offline spine. `_line_out` adds the key `model` to every row (fixed rows say fixed) — the one new key on a fixed line.
**Outside the brief, noticed:** the spine's own status line says its stock differs from Marg's printed closing on 191 items (24-Oct 23:50 build) — the engine stands on stock_figure's figure either way; named in the plan as the reason the score, not the replay, decides the switch. F-1024 (the parent's) names S619's DUTY_MAP rewrite — this kit touches no duty.

## The walk (the chat's build run, cloud workspace, 25-Oct-2026 ~07:3x IST, on the 25-Oct bundle + database copy + the spine rebuilt offline from MargArchive; the installer repeated it on the box)
```
S644 WALK  today=2026-10-25  python=/usr/local/bin/python3
1 · fixed is today (old bytes vs new bytes, model = fixed)
  ok   plan + interim equal on 2026-10-25 Sun (16 suppliers, 26 lines)
  ok   prepare_day rows equal on 2026-10-25 (0 rows, made {'fixed': 0, 'interim': 0, 'held': 0, 'skipped': 0})
  ok   no made_through stamp on fixed
  ok   plan + interim equal on 2026-10-26 Mon (16 suppliers, 26 lines)
  ok   prepare_day rows equal on 2026-10-26 (13 rows, made {'fixed': 12, 'interim': 1, 'held': 0, 'skipped': 5})
  ok   no made_through stamp on fixed
  ok   plan + interim equal on 2026-10-29 Thu (15 suppliers, 24 lines)
  ok   prepare_day rows equal on 2026-10-29 (0 rows, made {'fixed': 0, 'interim': 0, 'held': 0, 'skipped': 0})
  ok   no made_through stamp on fixed
2 · the rhythm (model = levels)
     supplier                         mode   bd90 every last buy   due   next        gap  cap
     KEDAR PHARMACEUTICAL             fixed    30     2 2026-10-24 False 2026-10-26    4   14
     A.A. PHARMACEUTICALS             learnt   17     5 2026-10-24 False 2026-10-30    5   14
     AGARWAL SURGICALS AND MEDICALS   learnt    3    30 2026-10-24 False 2026-11-23   30   45
     DAANSHI PHARMA                   learnt    2     7 2026-10-12 False 2026-10-26    8   14
     DEEPAM PHARMA                    learnt   13     6 2026-10-16 False 2026-10-26    6   14
     DRUG DEAL                        learnt    5    19 2026-10-16 False 2026-11-04   19   45
     ESS KAY AGENCIES EXTN            learnt    7    16 2026-10-16 False 2026-11-02   16   45
     ESSENTIAL PHARMA                 learnt    3    28 2026-09-28 False 2026-10-26   29   45
     GUNINA PHARMACEUTICALS PVT LTD   learnt   24     3 2026-10-24 False 2026-10-27    3   14
     JANTA PHARMACEUTICALS            learnt   15     6 2026-10-16 False 2026-10-26    6   14
     JUBILEE AGENCIES                 learnt   10     7 2026-10-06 False 2026-10-26    8   14
     KRISHNA MEDICOS                  learnt    5    18 2026-10-20 False 2026-11-07   19   45
     L.K. DRUG HOUSE                  learnt   15     5 2026-10-16 False 2026-10-26    5   14
     MANNAT PHARMA                    learnt   16     4 2026-10-24 False 2026-10-28    5   14
     RADHA MEDICAL & SCIENTIFIC       learnt    5    18 2026-10-16 False 2026-11-03   19   45
     RAMA MEDICOSE                    learnt    1     7 2026-08-22 False 2026-10-26    8   14
     RAVI MEDICAL AGENCY              learnt    3    30 2026-10-02 False 2026-11-02   30   45
     SAISUN PHARMA PVT. LTD           learnt    4    14 2026-10-06 False 2026-10-26   15   21
     SCIENTIFIC&MEDICAL AID CENTRE    learnt    2     7 2026-09-26 False 2026-10-26    8   14
     SHIVAAZ FORMULATIONS             learnt   25     3 2026-10-24 False 2026-10-27    3   14
     SHRADDHA MEDICOSE                learnt   11     7 2026-10-24 False 2026-10-31    8   14
     VERMA BROS. AND CO               learnt    2     7 2026-10-20 False 2026-10-27    8   14
     YOGENDRA AGENCIES                learnt    8    11 2026-10-16 False 2026-10-27   12   21
  ok   Kedar is rhythm_mode fixed (the owner's Mon + Fri)
  ok   every learnt interval within 2..30
  ok   Gunina (30 bill days, median 3) is reviewed every 3 days
  ok   a supplier with fewer than 3 bill days gets the default 7
  ok   every learnt supplier's cap follows its interval (14 / 21 / 45)
  ok   the words say the interval
     {"before": "1970-01-01", "after_interim_2026-10-24": "1970-01-01", "after_order_2026-10-23": "2026-10-23", "after_proposal_2026-10-24": "2026-10-24", "after_order_2026-10-25": "2026-10-24", "interval": 7, "due_today": false, "next": "2026-10-31"}
  ok   a supplier never bought from: last buy none (due)
  ok   an interim-only order does not move last buy
  ok   (a) a sent order moves it
  ok   (b) a sent fixed proposal moves it
  ok   an order sent today is not 'before' today
  ok   due today is false with a buy yesterday and interval 7; next = yesterday + 7 (or the first allowed day after)
     {"before": "2026-10-24", "interval": 3, "due_today": false, "next": "2026-10-27", "set_review_days": [200, {"review_days": 5}, null], "interval_after_override": 5, "words_after_override": "Gunina \u2014 Mondays, delivered same evening, cover 9 days, cap 14, Thursday blocked \u00b7 reviewed every 5 days (set by you), cap 14", "set_mode": [200, {"rhythm_mode": "fixed"}], "due_today_after_mode": false, "next_after_mode": "2026-10-26", "bad_review_days_99": 400, "bad_rhythm_mode_maybe": 400}
  ok   (c) Gunina: with its real orders / bills, last buy is a real day before today
  ok   the owner's review_days override wins and the words say 'set by you'
  ok   rhythm_mode fixed puts the supplier back on its calendar (Monday next)
  ok   bad values refused (review_days 99, rhythm_mode maybe)
3 · the list made again (B.2a)
     {"prepare": {"fixed": 5, "interim": 4, "held": 1, "skipped": 4}, "stamp": "{\"end_day\": \"2026-10-23\", \"sales_through\": \"2026-10-23\", \"spine_built\": \"2026-10-25T07:19:34+05:30\"}", "tick_same": "same", "tick_moved": "relisted 10", "ids_kept": true, "rows_before_after": [10, 10], "tick_again": "same", "tick_touched": "touched -- stale", "stale": true, "tick_late": "past 13:00", "tick_fixed": "off"}
  ok   prepare_day on levels stamps made_through
  ok   same inputs: no relist
  ok   moved inputs + untouched: made again once (rows > 0), ids kept, row count kept
  ok   a touched list is marked stale, not rebuilt
  ok   after relist_until nothing happens
  ok   on fixed the relist is off
4 · on the way (B.4)
     {"interval": 3, "on_order_days": 4, "counted_ages": [1, 3, 4]}
  ok   levels: a sent order counts within max(on_order_days 4, interval 3 + lead 1) = 4 days and not beyond
  ok   fixed: on_order_days alone, as before
5 · the owner's fold and the settings route
     {"keys": ["inputs", "made_through", "other", "other_words", "relist", "rhythm", "score", "settings", "stale", "value", "words"], "value": "levels", "n_settings": 11, "rhythm_n": 23, "error": null, "a_word": "Kedar \u2014 Mon & Fri, delivered same evening, cover 8 days, cap 14, Thursday ok, single-source extra waived; review 24-Oct-2026 \u2192 weekly \u00b7 fixed days (your ruling)", "b_word": "Gunina \u2014 Mondays, delivered same evening, cover 7 days, cap 14, Thursday blocked \u00b7 reviewed every 3 days (learnt from 24 bill days), cap 14"}
  ok   owner_state carries model with value, words, settings (11), rhythm rows, score, inputs
     {"order.model=levels": 200, "order.model=sideways": 400, "order.relist_until=12:30": 200, "order.relist_until=25:99": 400, "order.review_min_days=31": 400, "order.review_max_days=1": 400, "order.review_min_days=3": 200, "order.big_day_days=0": 200, "order.big_day_days=91": 400, "model_now": "levels", "keys_on_card": 17}
  ok   settings route: levels ok, a wrong word refused, HH:MM ok, 25:99 refused, min > max refused, max < min refused, min 3 ok, big 0 ok, 91 refused, 17 keys on the card
6 · the real day, both models (the table the chat reads)
  ok   the levels plan was made on the spine
  ok   the levels plan says its window end and model in inputs
     fixed : {"suppliers": 16, "held": 1, "lines": 26, "value_rs": 52289, "lot_based": 0, "interim_suppliers": 0, "interim_lines": 0, "no_supplier": 34}
     levels: {"suppliers": 17, "held": 1, "lines": 27, "value_rs": 78938, "lot_based": 23, "interim_suppliers": 0, "interim_lines": 0, "no_supplier": 34}
     the fifteen largest quantity differences (item · supplier · fixed -> levels · why):
       TRAMATEE P TAB 15T           MANNAT PHARMA                 0 -> 50   strip  usual lot 50 strips: 50 strips instead of 30 strips; one lot is 16 days of sale -- more than the cap of 14
       ROSIKA FORTE                 DEEPAM PHARMA                20 -> 50   strip  usual lot 50 strips: 50 strips instead of 10 strips; one lot is 24 days of sale -- more than the cap of 14; scheme: about 20 free per 100 bo
       PATOPAN DSR                  KEDAR PHARMACEUTICAL          0 -> 30   strip  the box is 3x what is actually needed; usual lot 30 strips: 30 strips instead of 10 strips
       MEG QCS                      KEDAR PHARMACEUTICAL          0 -> 30   strip  the box is 5x what is actually needed; usual lot 30 strips: 30 strips instead of 5 strips
       TYRO BR                      KEDAR PHARMACEUTICAL         30 -> 50   strip  usual lot 50 strips: 50 strips instead of 30 strips
       ORICOX P                     MANNAT PHARMA                30 -> 50   strip  usual lot 50 strips: 50 strips instead of 40 strips; one lot is 14 days of sale -- more than the cap of 14
       ONKET DT                     ESS KAY AGENCIES EXTN        30 -> 50   strip  usual lot 25 strips: 50 strips instead of 40 strips; scheme: about 20 free per 100 bought
       FOLITRAX 15 MG TAB           SAISUN PHARMA PVT. LTD       20 -> 40   strip  usual lot 40 strips: 40 strips instead of 10 strips; one lot is 44 days of sale -- more than the cap of 21
       TOLTRIS PLUS                 SHIVAAZ FORMULATIONS         40 -> 25   strip  usual lot 25 strips: 25 strips instead of 30 strips; scheme: about 20 free per 100 bought
       NARCOGEN FORTE               KRISHNA MEDICOS               0 -> 12   strip  usual lot 12 strips: 12 strips instead of 2 strips
       JAKMAC 5                     GUNINA PHARMACEUTICALS PVT   10 -> 0    strip  
       GEN D3 NANO                  GUNINA PHARMACEUTICALS PVT   10 -> 0    strip  
       DEFVAX 6                     SHIVAAZ FORMULATIONS         30 -> 40   strip  usual lot 15 strips: 15 strips instead of 10 strips; scheme: about 20 free per 100 bought; plus 20 short-supplied on order #42 (2026-10-17) 
       CROCAL                       SHIVAAZ FORMULATIONS         10 -> 0    strip  
       BIO D3 MAX                   GUNINA PHARMACEUTICALS PVT   10 -> 20   strip  usual lot 20 strips: 20 strips instead of 10 strips; one lot is 15 days of sale -- more than the cap of 14
  ok   the two models differ somewhere (else the model is not in force)
  ok   every levels line has a quantity > 0 and a unit
  ok   a lot-based line is not rounded to tens unless its lot is
7 · the spine selftest on the new bytes (the pure functions made to fail on purpose)
  ok   selftest_spine.py OK on the new bytes
      SELFTEST OK  71 checks
8 · the cron commands once each, as scripts, on scratch
  ok   order_rules.py tick (prepare) runs
  ok   order_rehearsal.py runs and writes the weekly file with by_model / darpan keys
N · negative control -- the OLD bytes
  ok   OLD bytes have no model_rate, no relist, no review_interval (the checks above would be red on them)
  ok   OLD bytes: prepare_day leaves no made_through stamp and has no relist
  ok   OLD selftest has no S644 checks (fewer checks than the new one)

WALK GREEN  (46 checks, 0 red)
```
## The replay
```
replay on finance.db: closing as on 23-10-2026, anchor 2026-10-22, 199 medicines sold, 100 like-for-like
  lost sale %              reference       0.69   kit       0.69     0.0 %
  empty-shelf item-days    reference      84.00   kit      84.00     0.0 %
  average stock Rs         reference  169663.68   kit  169663.68     0.0 %
  supplier orders / week   reference      20.39   kit      20.39     0.0 %
  lines / week             reference      40.33   kit      40.33     0.0 %
  (between-review orders / week: reference 3.3, kit 3.3)
REPLAY OK -- the kit's arithmetic is within 0.0 % of the reference (10 % allowed)
```
