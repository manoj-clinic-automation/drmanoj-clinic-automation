# S307_SUPPLIER_CHECK_2 — the wrong-supplier check, second stage, on Amir's bills

**Session 266 (Sanjeevni project) · 17-Sep-2026**, on the owner's "go".

## What it adds

S285 warns on Amir's step 4 when an item on a bill has never come from the supplier the bill names. This kit covers
two cases S285 could not see.

**1. A purchase return under the wrong supplier.** A return is a bill with a minus amount, with its own item lines, so
S285's test already ran on it, but its words spoke of goods that *came*. For a return the warning now says what is
wrong:

> ⚠ Ye **wapsi** hai. **TYRO BR** kabhi **SOLO TRADERS** se nahi aaya — pehle hamesha **KEDAR** se aaya hai (3 bill).
> Wapsi galat supplier ke naam to nahi likhi? Marg mein dekh lijiye.

**2. The same bill number and date under two suppliers.** Every other bill with that number and date under another
supplier, still carried by a live bill-wise export, is named on the bill.

- **Same amount** — possibly one bill entered twice, which would put it on two payment sheets:

  > ⚠ Isi bill number aur isi taareekh ka bill **DEEPAM PHARMA** ke naam bhi hai, aur rakam bhi wahi ₹900 hai. Ek hi
  > bill do supplier ke naam to nahi chadh gaya? Marg mein dono dekh lijiye.

- **Different amount** — two suppliers' number series can meet (the 1-Sep bill 160 of DAANSHI and KEDAR is genuine):

  > ⚠ Isi bill number aur isi taareekh ka ek bill **YUVIKA SURGICALS** ke naam bhi hai (₹3,830). Do alag supplier ho
  > sakte hain — ek baar Marg mein dekh lijiye.

**What stays the same:**

- Nothing is decided for Amir: *Supplier galat likha* (S285) is still his to pick, and *Theek hai* clears the bill.
- A bill that no live export carries any more is not a twin. A number Amir has already corrected in Marg stays quiet.
- The lists, S285's warnings and every quiet bill render exactly as before.

## The proof

**`selftest_s307.py`: 25 checks, 0 failed.** It uses S285's fixture plus these cases:

- **Same number and date, same amount:** both 502s warn, each naming the other.
- **Different amounts:** 252 gets the softer look.
- **A dead export:** a same-number bill only in a superseded export is not a twin.
- **Return under the wrong supplier:** it warns as a *wapsi*.
- **Return of the supplier's own item:** quiet.
- **Before vs after:** both modules' lists and S285 warnings are identical, and an ordinary warning and a quiet bill
  render byte-for-byte as before.
- **No tables:** no warning, no crash.

**Rehearsed on the office PC** against the 17-Sep nightly database (`rehearsal_s307.txt`):

- **Amir's list on 17-Sep:** empty. All 128 answered bills are *Theek hai*.
- **All live bills since April, judged as if they were on his list:**
  - **4 bills carry a same-number twin:** 160 of 1-Sep (DAANSHI ₹5,377 / KEDAR ₹12,400) and 252 of 9-Jun (DEEPAM
    ₹1,900 / YUVIKA ₹3,830), both genuine, both different amounts.
  - **None has the same amount.** Bill 502 of 18-Aug had been in the database under MANNAT and DEEPAM at ₹10,641 each,
    but the live exports carry it under one supplier only. It was corrected in Marg, so it stays quiet.
  - **Returns:** 5, and none warns.

**On the box, before anything is placed,** `walk_s307.py` runs on a scratch copy of the live database. It builds his
list with both the live and the patched file and requires them to be identical, renders every bill, and prints how many
live bills the new checks would warn on.

## Install — one line on the VPS, after the publish

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S307_SUPPLIER_CHECK_2/install_S307_SUPPLIER_CHECK_2.sh
```

It restarts clinic-finance. **Rollback:** put `/root/finance/amir_day.py.bak_S307_b3c20319` back in place, then run
`systemctl restart clinic-finance`.
