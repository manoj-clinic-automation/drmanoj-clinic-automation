# S510_PAYMENTS_MARKED — the server honours the Janitor's marks (Club D)

Session 304 (parent), 10-Oct-2026. The Inbox Janitor v2.4 marked the old rows of the Payment Register sheet at 22:16 IST:
59 *[NOT A PAYMENT]*, 1 *[DUPLICATE of row N]*, and 33 Docterz notification rows whose words (patient names) it replaced.

## What changes
- **The accountants' monthly payment digest** (pack item 7) leaves out the rows the sheet marks as not a payment or duplicate.
- **The nightly read of the sheet (02:05)** records every change as before, except a Docterz row's: the old words are never kept
  as history — the record says *"a Docterz notification — the patient's details were removed from the sheet"*. Any older record
  holding such words is scrubbed on every run.

## Install (his one line on the VPS, after PUBLISH_ALL) — before 02:05 tonight is best
    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S510_PAYMENTS_MARKED/install_S510_PAYMENTS_MARKED.sh

## Undo
    cd /root/finance && \cp -p packs.py.bak_S510_2a7c2a63 packs.py && \cp -p payments_register.py.bak_S510_fa12a0a1 payments_register.py && systemctl restart clinic-finance
