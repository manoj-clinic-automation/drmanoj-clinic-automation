# S210_TRUTHFLOW — D354: Marg + bank ARE the day

## The owner's ruling (30-Aug-2026, his words — this kit executes it)

> "making him checker, accepting his errors, and they get to my page automatically is my
> purpose... everyone gets the correct marg and bank data which is the sole truth, and i
> have the facility and authority for any reconcile."

## The three pieces

**1 · `patch_finance_app_autofile.py` — apply now CREATES the day it loads into (D354).**
A staged day with no `day_entry` is filed from the two ruled truths: net sale from the
staged Marg bills (credit notes subtract) · UPI from the bank record (`upi_txn`, the S208
final ruling) · cash = net − UPI. Created `status='submitted'`, so it lands in the owner's
approvals queue like any hand-filed day; approval, edits (day_revision), exceptions and
review are untouched. HONESTY GUARDS: a day with net ≤ 0 or bank-UPI over net cannot be
built by formula and stays manual; already-filed days untouched; `marg.autofile='0'` turns
it off; F-155 (applied only when every day loaded) stands.
**Selftest 25/25** on the three newest finance_app copies · **F-87 rehearsal 9/9 on a
seeded store** (`REHEARSAL_autofile.py`): cash/UPI split to the paise, ledger advance
correct, all three guards proven.

**2 · `patch_marg_report_words.py` — the three misleading sentences fixed AT SOURCE.**
The C3 finding (S203) executed at last: "will attribute to WALK-IN" → what D348 actually
rules (counts in full; named park for cross-match; nameless book WALK-IN) · the
"needs finance_ingest at S180 U1 or later" developer-speak → "returns, kept and carried
through signed" · "scored low" (retired vocabulary) → "park for review, never attached to
a guessed patient". Wording only; no parsing or routing changes. **Selftest 15/15** on the
live-pinned parser copy (`6411a57d…`) and the working-tree copy.
⚠ The medical-PC's own `marg_report.py` copy carries the same old words — its warnings do
not reach the owner's console (the VPS re-parses), fold into the next courier sync.

**3 · `finance_approvals.html` — "apply failed — network" stops lying.**
A server error now shows its HTTP status and the first line of what the server said;
"could not reach the server" is said only when that is true. (Base: S210_MARGTIDY page —
this file supersedes that kit's copy; install this one.)

## Install — VPS, one line at a time (restart IS needed)

```
git -C /root/deploy/repo fetch --depth 1 origin main && git -C /root/deploy/repo reset --hard origin/main
```
```
/root/wa/venv/bin/python3 /root/deploy/repo/deploy_kits/S210_MARGTIDY/patch_finance_app_margtidy.py /root/finance/finance_app.py
```
```
/root/wa/venv/bin/python3 /root/deploy/repo/deploy_kits/S210_TRUTHFLOW/patch_finance_app_autofile.py /root/finance/finance_app.py
```
```
/root/wa/venv/bin/python3 /root/deploy/repo/deploy_kits/S210_TRUTHFLOW/patch_marg_report_words.py /root/finance/marg_report.py
```
```
\cp /root/finance/finance_ui/finance_approvals.html /root/finance/finance_ui/finance_approvals.html.bak_S210_TF_$(date +%Y%m%d_%H%M%S)
```
```
\cp /root/deploy/repo/deploy_kits/S210_TRUTHFLOW/finance_approvals.html /root/finance/finance_ui/finance_approvals.html
```
```
systemctl restart clinic-finance.service && sleep 3 && systemctl is-active clinic-finance.service
```

(Each patch prints `already patched -- nothing to do.` if it was applied before — safe.)

**The walk:** open the approvals page → Marg section → **Apply on the 28/29-Aug report.**
Expected: "applied: 2026-08-28 (…bills), 2026-08-29 (…)" — the days now EXIST, submitted,
in your queue. The money card advances past 27-Aug. The three reworded sentences replace
the misleading ones on the next push received.

*S210 · 30-Aug-2026 · owner-ruled D354 · anchors refused if ambiguous · nothing installed
by the assistant.*
