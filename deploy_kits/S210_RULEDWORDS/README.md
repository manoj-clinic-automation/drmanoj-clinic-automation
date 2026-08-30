# S210_RULEDWORDS — stored warnings brought under the rulings, on read

## Why the retired sentences survived the parser fix

Warnings are written into `marg_push_staging.survey_json` AT PUSH TIME and the list replays
the stored text. `patch_marg_report_words` (S210_TRUTHFLOW) fixed the parser — future pushes
only. The 28/29-Aug rows and every older row still carried the retired sentences, which is
exactly what the owner saw again after installing.

## What this does — one anchored insertion in `api_marg_push_list`

Stored warnings are rewritten AS SERVED, numbers preserved:

- `4 credit note(s) totalling -1442.00 — kept, ... (needs finance_ingest at S180 U1 or later)`
  → **`4 SALES RETURN(s) — credit notes totalling -1442.00 — kept and carried through
  signed; each is approved by you against the same patient (S208)`**
- `10 of 27 bills carry no clinic ID and will attribute to WALK-IN`
  → **`10 of 27 bills carry no clinic ID — they count in sales in full; named ones park for
  the cross-match, nameless book as WALK-IN (D348)`**
- `— scored low so they go to review rather than to a possibly wrong patient`
  → **`— these park for review, never attached to a guessed patient`**

One rule now covers every row ever stored AND every row to come. Unknown warnings pass
through untouched. Rulings applied: S208 (CN = SALES RETURN, same patient, owner approval)
and D348 (no-ID routing; "scored low"/"low confidence" vocabulary retired).

**Selftest 15/15** — the rewrite proven against the owner's EXACT pasted sentences, plus
patch/compile/no-op/refusal on margtidy-patched copies. Requires S210_MARGTIDY applied
first (refuses otherwise, changes nothing).

## Install — VPS, one line at a time

```
git -C /root/deploy/repo fetch --depth 1 origin main && git -C /root/deploy/repo reset --hard origin/main
```
```
/root/wa/venv/bin/python3 /root/deploy/repo/deploy_kits/S210_RULEDWORDS/patch_finance_app_ruledwords.py /root/finance/finance_app.py
```
```
systemctl restart clinic-finance.service && sleep 3 && systemctl is-active clinic-finance.service
```

Walk: reload the approvals page → Marg section → the 28/29-Aug row's warnings read the
ruled sentences above, numbers unchanged.

*S210 · 30-Aug-2026 · display honesty only — no parsing, routing, or number changes.*
