# S208_DARPAN — the day card, exceptions first

**Staged, not installed. Requires S208_BANKMATCH on the server first.**

Everything the server can verify, it verifies silently. Darpan sees only what
the two truths — the bank MPR and Marg's sale export — could not settle
between themselves. On a clean day his whole morning is one tap.

**Evening:** count the drawer, type one number. That is the only thing he
ever types.

**Morning (`/finance/darpan`):** the card in his convention — day sale net of
returns (CN bills expandable) · UPI with its matched bills · net cash =
sale − UPI − home − procedure · the three categories expandable to detail ·
bank MPR collapsed · exceptions with two-tap answers · the drawer at ₹50
tolerance, with the full arithmetic shown only when it is out.

**Exceptions:** *bank says UPI, rung as cash* → "Haan, UPI tha" creates a
correction row / "Nahin" escalates · *bank orphan* → attach to a bill, log as
an advance (the money-received-bill-later ledger), or escalate · *bill
orphan* → escalate. Every answer is audited, who and when. A second answer on
an already-answered row is refused.

**The owner's page (`/finance/darpan/corrections`):** every rung-as-cash bill
with its bank reference, the exact Marg instruction, tick-off with user and
time, corrected/pending counts, month-wise navigation.

**The guard:** a second form for an already-filed date is refused with "ask
the doctor" — one owner grant allows one re-file, then it is spent. And the
owner tools: dismiss a stale not-filed flag (reason mandatory — the
2026-06-12 case), reject a pending staged push.

## Proven

37/37 on the real 27-Aug shape — the whole day walked end to end — and the
patch applied to a **byte-exact reproduction of the live finance_app.py**
(base + stock block, md5 `ada47c79…`): compiles, both blocks coexist, revert
returns the exact original.

## Install

```
bash /root/deploy/vps_deploy.sh S208_DARPAN
```

Gates: kit SUMS → live-file currency → backup → copy → patch → compile →
37/37 → smoke-suite non-regression → restart → all routes present (the stock
routes checked too, so this install proves it broke nothing). Any red
restores.

*S208_DARPAN · staged 30-Aug-2026 · the VPS was not touched.*
