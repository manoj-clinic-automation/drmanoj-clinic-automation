# S532_AUTO_HOME — the system sends a scan home from the scan app's own history (the flow proposal's K3)

*Scan App project, S306, 11-Oct-2026. The owner's "ok" of 11:41 IST to `claude/SCANAPP_FLOW_PROPOSAL_v1.md`. Built by
BUILD_NORM_v1 (D704) on the post-S531 bytes. No cross-project read: `assets.db` only.*

## The real cause
The lane is chosen wrong at intake about one time in eight (12 relanes on 145 scans); the suggestion engine knew the
right place after reading but only offered it as a tap for the owner or Shavez, days later; 18 clinic papers waited
without a group though their suppliers had been sorted the same way every time before.

## The rule (`clinic_papers.auto_home`), run once per scan when its reading ends, and at every start for the papers still waiting
- **Evidence** is the supplier's earlier live papers (first two words of the name) that a **person** placed: a paper the
  system placed counts only once a person has moved or sorted it afterwards — the system never feeds itself.
- **Rule 1, the lane** — this paper live (draft or captured), not a challan, not moved by a person: all earlier papers on
  the **pharmacy** lane, **three or more** → it goes there (captured, kind Pharmacy, as the lane door would move it); all
  on the **clinic** lane **and sorted by a person into one group, two or more** → it goes there and Rule 2 sorts it.
  **Never** out of, or into, the lab and Dr MK expense lanes (NK Pathology's and the owner's own); never into Other
  document. A scanner's default lane alone is weak evidence; a person's sorting is strong.
- **Rule 2, the group** — on the clinic lane, a draft with no group: all earlier clinic papers in **one** consumable
  group, two or more → that group, and accepted (D710, `approved_by` "system — from N earlier papers of this supplier").
- **A supplier seen on two lanes (Yuvika) decides nothing.** A section (Construction, Resumes, Misc, Personal) is never
  guessed (D664). A paper a person has moved or sorted is never touched. One look per paper (idempotent: audit rows
  `auto_lane` / `auto_group` with the evidence count).
- The paper's page says *Placed by the system from N earlier papers of this supplier — change it here if wrong.*
- **The heal at start** gives every live paper still waiting (read by the OCR, no group) the same one look. On today's
  database that is **one paper** (B-0133, Variety Stationers → Others, from 4 earlier papers); B-0022 (Envirad, on the lab
  lane) is deliberately left where Sukhveer put it.

## Files
| file | FROM (pinned) | TO |
|---|---|---|
| `/root/assetapp/asset_register.py` | `4e924b80` (S531) | `PIN_TO_asset_register.txt` — one guarded call at the end of `_bg_extract`; backup `.bak_S532_4e924b80` |
| `/root/assetapp/clinic_papers.py` | `93d23481` (S531.1) | `PIN_TO_clinic_papers.txt` (S532.1); backup `.bak_S532_93d23481` |
| `/root/assetapp/scanner_widget.js` | `65127fcb` | read only |
| `/root/assetapp/assets.db` | — | backed up `assets.db.bak_S532_<stamp>` before the restart |

## Proof
`walk_s532.py` on a copy of the real database (made-up rows dated 2031): **25 of 25 green** — the history as the rule
reads it from the real rows (Shivaaz: pharmacy 10; Variety Stationers: clinic 5, others 4; Yuvika: two lanes); a Shivaaz
bill scanned on the clinic lane goes to the pharmacy lane; a Variety bill scanned on the pharmacy lane goes to the
clinic lane, gets Others and is accepted; Yuvika decided nothing; an unknown supplier nothing; a challan never moved;
idempotent; three system-placed papers are no evidence until a person confirms them; a person's move is final; the lab
lane never moved; a supplier whose clinic papers were never sorted is not sent to the clinic lane; the reading hook
itself (the OCR stood in by a stub) sends the paper home; the page says so; every door answers; the live database
untouched. On the LIVE files: red (the control). Installer rehearsed on a made-up root: DONE (the heal placed B-0133) ·
ALREADY INSTALLED · drift refused · red-after-placing restored.

## Install (the owner's one line, after his publish — S531 installed first)
```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S532_AUTO_HOME/install_s532.sh
```
## Undo (one line)
```
cp -p /root/assetapp/asset_register.py.bak_S532_4e924b80 /root/assetapp/asset_register.py && cp -p /root/assetapp/clinic_papers.py.bak_S532_93d23481 /root/assetapp/clinic_papers.py && systemctl restart assetapp
```
A paper the system placed stays placed (as a tap would have); its page names it and it can be changed there.
