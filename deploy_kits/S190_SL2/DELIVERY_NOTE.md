# S190_SL2 — D331: the staff advance policy

**One kit, one system: `staff_ledger.py` (live pin `92665b64…` → this build).
Executes the signed contract `S190_Staff_Advance_Policy_D331.md`. The D250 close
engine's arithmetic, waterfall order, interest, skips and capitalisation are
byte-untouched.**

## What changes, in one line each

- Choosing **Advance issued** now shows, inline and before any amount is typed:
  *"Taken against <month>: Rs X of Rs Y max"* — Y derived (base × pct ÷ 100,
  floored to ₹100; base from `staff_master.csv`, pct from `advance_pct.json`,
  default 50, Darpan 75).
- **Over the ceiling** the save refuses with the figures — unless the entry is
  marked **SPECIAL**, which is never direct: even a checker's own special entry
  goes PENDING, because **approval refuses until the signed written application
  (Dr Manoj / Dr Bhawna) is uploaded** against the row. Maker drafts, maker
  uploads, checker approves. No escape hatch. Applies from August.
- **Against-month attribution**: an advance can be booked against a future
  month's salary — it consumes THAT month's quota and the close recovers it
  only from that month (the 17-Aug ₹5,000 → September device).
- The pending queue marks special rows: 📄 application on file / NOT uploaded.
- **No base salary on file → the gate stands down visibly** (inline note names
  the fix), never freezes advances on a data gap.
- The ledger serves the shared scan widget (camera + gallery) for the
  application; files under `/root/staff_ledger/applications/`, sha in the row.

## Numbers

Offline: current bytes **190/190** → this build **212/212, +22 exactly** —
the projection written before measuring, the seventh consecutive to land.
Legacy JSONL rows (no D331 keys) proven to flow through every new path.

## Install

```
cd /root/deploy/repo && git pull
bash /root/deploy/repo/deploy_kits/S190_SL2/install_sl2.sh
```

Expect: currency gate PASS → 190 → 212 staged → swap → 212 live → service
active → **Darpan's derived ceiling printed from the box's own
`staff_master.csv`** (if it does not say Rs 15000, the base in that CSV is the
thing to fix — D331 §5.3, the one open question, now answered by the box).

## Not in this kit

`S190_F2` — the finance side's fail-soft read of the ledger (so the Sanjeevni
inline line counts ledger-attributed advances). Built next, after this lands.
