# S869_HUB_DAYS_CASH — the Hub's Days and Cash (D1005) — Sanjeevni session 482, 18-Nov-2026

**His OK:** 11:59 IST 18-Nov on mock-up v3 (https://claude.ai/artifact/GeKbcmkCgU2KL11vecWk8R) and his 9-Oct ruling ("a typo … make the necessary
changes one time"). Spec: `deploy_kits/KB_canon_all/S481_HUB_BUILD_SPEC.md`.

## What changes (owner page only; Darpan's and Bhati's screens untouched)
- **Day panel** (Days → tap a day): every bill opens to its medicines with each line's VALUE (strips:tabs × the strip rate); a without-cash bill
  names who it was typed to, exactly as Darpan typed it in Marg; a sale return names the patient, the clinic ID and the mobile (his page: the
  full number), its lines, and carries the Returns card's own verdict with the same Approve / Reject — one check, one action, two places.
- **Dr Bhawna's receipt**: "Received ✓ for Dr Bhawna" on each unreceived row, and a band "N handovers to Dr Bhawna (… to …) are not marked
  received · ₹… — Mark all N received" (she does not use the app; his tap stands for her; each stamp audited as darpan_kal's own).
- **His day entries** ("+ Add an entry" on the panel; removable): *Paid into another account* (never reached the drawer — the day's cash for
  the drawer is less by it) · *Cash taken out* (left the drawer on a doctor's word; counts WITH the doctors — the named party, else the pool).
  Table `owner_day_entry` (new, `hub_cash.py`); the one calculation (`sanjeevni_cash.days()`) reads it; audited.
- **Cash card — "Why the drawer reads ₹…"**: each day handed over short beyond the tolerance, its cause (Darpan's reason, his decision, his
  entries, a late bank UPI), and the actions: Add an entry · Accept (write off) (= darpan_kal's own owner/decide door).
- **Two rules** in the one calculation / the resync: a short he ACCEPTED on Darpan's page leaves the drawer as written off, never more than the
  short he accepted (F-1460); `day_resync` pass 1 takes the bank's UPI on APPROVED days too (F-1459) — audited as before, status named.
- **The one-off** (`oneoff_s869.py`, DRY on a copy inside the proof, LIVE by the installer, idempotent, every change audited): 9-Oct's 23,421
  handover → 13,258 (darpan_kal_day, the landed cash_movement, its cover row, the owed row withdrawn); 14-Nov entries ₹1,580 (NK Pathology UPI)
  + ₹4,000 (taken out, with Dr Bhawna); 4-Nov entry ₹954; 3-Nov's deleted Marg bill A004591 (₹1,760) removed with its 6 lines (kept whole in
  the audit row), its review line resolved, the day re-read from Marg's 13 bills (cash 4,762 = what Darpan handed). Drawer ₹21,508 → ₹549;
  17-Oct's ₹504 waits for HIS tap (Accept, or an entry) → ₹45 of round-offs.

## Files
| file | FROM | TO | how |
|---|---|---|---|
| NEW `/root/finance/hub_cash.py` | — | 8d6c3f69 | the kit's own |
| `/root/finance/sanjeevni_cash.py` | 8e58691b | 818ed0a2 | v1.2, whole file (read whole S482) |
| `/root/finance/sanjeevni_day.py` | 22a38006 | 4359d048 | v1.3, whole file (read whole S482); mounts hub_cash |
| `/root/finance/day_resync.py` | 00b45a15 | 0480d1cc | 5 exact anchors (make_s869.py) |
| `/root/finance/finance_ui/finance_approvals.html` | 17f13acc | 7253dc9f | 9 exact anchors (make_s869.py) |

## Cold review (S482)
Two MUST and seven SHOULD/LOW points built in: the 'Paid into another account' line below Cash received (the column adds up); a filed day not yet handed over is 'not yet handed', never short; the panel re-reads after the Returns card refreshes; the one calculation reads `owner_day_entry` itself; a two-day cover counted by its cover rows; pass 1 never touches a LOCKED day; 'Mark all' says how many; the one-off refuses when pass 0 does not fix 3-Nov; the switch checked before [5/7]. Noted, not changed: Darpan's own page still reads 14-Nov short ₹5,580 (his page does not read the owner's entries); the pool figure in the split (−7,26,095) is the deposits' side and is not read by the Hub; the spec's 21,512 vs this copy's 21,508 are two readings of the same drawer four rupees apart (round-offs).

## Proof
`synth_s869.py` (47 checks on copies, 30 on an already-cleaned copy: the rules, the panel, the doors through Flask incl. a maker refused, pass 1 on approved days, the one-off
DRY / APPLY / again, the page's markers; the review's asks -- the cn-hub key join, a not-yet-handed morning, a two-day cover, darpan_kal's doors, a locked day); the control on the live files red; S365's and S367's walks read the same old/new; S399's walk GREEN.
`rehearse_s869.sh` A1–A5, B1–B8 on a stand. Install: his publish + one server line (header of the installer). Undo: `undo_s869.sh` (files only;
the audited data stays — it is his rulings).
