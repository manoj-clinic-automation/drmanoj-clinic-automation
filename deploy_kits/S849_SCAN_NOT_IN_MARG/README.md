# S849_SCAN_NOT_IN_MARG — scanned bills not found in Marg, asked of the doctor and Amir (17-Nov-2026, Sanjeevni session 473; D993, D995; F-1433)

**Why.** F-1433: the ROSIKA scan B-0150 (Deepam Pharma, 12-Oct) sat five weeks on the Purchase bills page's waiting list and nobody was asked —
it is the same paper as Marg bill A000678, already scanned as B-0154 (both lines, batches and rates agree; the reader joined "50 + 10 free" into
"5010"). The owner's words 16-Nov 12:00–12:34 and 17-Nov 11:32; his "ok" 11:38 on mock-up v2 https://claude.ai/artifact/FY6ubLCgQTww6g3Aqsjjzh.

**Now** (NEW `scan_ask.py`; seams in five files): a scan on the Purchase bills page's own waiting list (`provisional_s781.provisional`) after Marg's
purchases run `purchase.not_in_marg_days` (7, his setting on the page) past its bill is asked —
- of the **doctor**: one Needs-you line (Bills & papers) → `https://followup.dr-manoj.in/finance/sanjeevni/not-in-marg`: the scan inline, and each
  Marg bill of that dealer within 20 days with its own scan and lines, side by side, item/batch/rate/expiry ticked or crossed, the best match named;
- of **Amir**: first on his card, in Hindi, one tap each; while asked it leaves his plain "Marg mein daalne ke bill" list.
Answers (the first closes it for both): **same bill** (joined CONFIRMED, or kept as that bill's second scan when it has one — exactly the
reception's "Yahi bill hai?"), **another bill — Amir enters it** (his do-line until Marg's export carries it; asked of the doctor again if still
not in Marg after the same days), **not a purchase bill** (leaves every purchase list). The doctor can undo the last two. Months before
`purchase.register_from` are the doctor's only, folded. OFF: `/root/finance/_off/S849_OFF` (or ALL_OFF).

**Files:** NEW `scan_ask.py` · `sanjeevni_approvals.py` 7d75f9d5 (mount + Needs-you) · `amir_day.py` c016278b (his card + tap) ·
`purchase_app.py` d1999929 (his enter list skips 'not a purchase bill') · `provisional_s781.py` 4d9cef55 (the waiting list skips it) ·
`scan_register.py` eb48202f (Amir may open the scans of his question) — whole files by `make_s849.py` on exact anchors.
**Proof:** `synth_s849.py` 21/21 on a made-up assets.db beside a copy of finance.db (T0–T20); the control on the live files red. On the box
the installer adds R1–R3 on copies of the live databases (B-0150 asked, best match A000678; the page; Amir's card) and runs walk_s781,
walk_s761, walk_s750/753/755, walk_s814, walk_s845 on the live and the new files — every last line the same.
**Install:** publish, then the one server line in the installer's head. **Undo:** `bash /root/deploy/repo/deploy_kits/S849_SCAN_NOT_IN_MARG/undo_s849.sh`.
