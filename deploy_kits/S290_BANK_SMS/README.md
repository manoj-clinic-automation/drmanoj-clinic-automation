# S290_BANK_SMS

**One line on the VPS:**

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S290_BANK_SMS/install_S290_BANK_SMS.sh
```

**Then, on the owner's phone, signed in:** `https://followup.dr-manoj.in/finance/bank-sms` → open *Phone setup — MacroDroid* and follow the five lines there (the key is shown on that page only; long-press to copy it into MacroDroid).

**What it does.** Each ICICI settlement SMS (`ICICI Bank Account XX… credited:Rs. … Info …ICICIPOS…SET 10XX<merchant>…`) is posted by MacroDroid to one door on the server. The merchant id names the unit (Sanjeevni or clinic) through `business_unit.merchant_id`; the business day is the SMS date minus one (proved 23 of 23 on the owner's own log). The page lists each business day: SMS figure, MPR figure, "matches MPR" / "MPR not yet" / "differs by ₹" / "no SMS", and warns when no SMS has arrived by 10:00.

**Safety.** Only a settlement credit is stored; any other text (OTP, debit, personal) is answered "ignored" and nothing of it is kept. The door needs the key; 60 posts an hour at most. The MPR remains the record.

**Next (not in this kit):** the SMS figure on the morning match and on Darpan's day card, so the early figure shows where staff already look.

**Proof.** `walk_s290.py` — the real patched app over a scratch copy of the real `finance.db`, SMS texts built from the copy's own MPR days: 29 checks (key, rate door, duplicates, three kinds of non-settlement text ignored and unstored, unknown merchant, FT variant, matches/differs, the 10:00 warning, who may see the key, the rest of the app still 200). Negative controls: removing the key check (red at 4), storing a non-settlement text (red at 9).
