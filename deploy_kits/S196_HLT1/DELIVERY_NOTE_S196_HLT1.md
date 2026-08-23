# S196_HLT1 — Delivery note: the renewals line (portal health tile, Task #8)

**What it does.** Your personal Inbox-Janitor GAS already carries the RENEWALS
list and nags by email (S195). v2 additionally **pushes that list to the VPS
once a day**, and the `/finance/health` page grows a sixth card:

- inside 30 days → "N inside 30 days · nearest: GoDaddy dr-manoj.in in 12 days"
- inside 7 days → the same line as a **warning**, which is what the portal
  tile's headline picks up — the tile line you asked for
- overdue → **bad**, names the item and how many days past
- the GAS stops running → "feed stale" warning after 72 h (a reminder system
  whose own death is silent is the thing we keep refusing to build)
- not wired yet → a quiet info line, never an alarm before the wire exists

**Mechanism.** One-path token (`FINANCE_RENEWALS_TOKEN`, its own secret — the
marg-push pattern; the personal GAS never holds a key that opens anything
else). Fail-closed until the token is set. State is one JSON file; **no DB
row, no schema change, no page redesign** — the health page renders the new
card through its existing machinery. Days are recomputed from dates at every
render, so the card can never age.

**Pins.** `finance_app.py` `df75024392e31ae99bb3fde9fab24062` →
`cfacce276153e7ff83c58e0fc2e7ddc7` · smoke projection **654 → 665** ·
11 new checks (token fail-closed / wrong-token / one-path-only / valid-rows
filter / all five card states + stale + no-feed).

**Install:** publish, then on the VPS:
```
cd /root/deploy/repo && git pull && bash deploy_kits/S196_HLT1/INSTALL_S196_HLT1.sh
```
Then the two token steps the installer prints (VPS env + GAS Script Property)
and paste `Renewal_Nag_v2.gs` over the old file in the personal project.
