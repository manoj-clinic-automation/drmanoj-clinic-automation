# S679_SALE_BILLED_TO_PARTY — a sale billed to a party account is named, and the staff told to correct it

*Sanjeevni session 367 · 29-Oct-2026 · on the owner's word of 16:55 IST.*

## For the owner
A sale can only be Cash or UPI — never billed to a party (your ruling). If a counter person bills a sale to a party account by mistake,
the medical PC now refuses that day's sale report **by name** — *"bill A00xxxx is billed to a party account"* — and Shavez's *Aaj ki
reports* says in Hindi: *"Bill A00xxxx party ke khaate mein bana hai — bikri sirf Cash ya UPI mein hoti hai. Marg mein yeh bill Cash ya
UPI mein theek kijiye, phir report dobara nikaaliye."* The day stays due until a corrected export comes. Nothing else changes.

## What happened (28/29-Oct)
On 28-Oct a stand-in at the counter billed **A004482** (₹1,198, cash 0) to **DEEPAM PHARM**. Marg's text export then prints the party's
name in the D.R. column where `.CASH` / `.UPI` stands. The medical PC's reader stopped at that line (09:57, 29-Oct: *"line 12: a bill row
whose payment head is not where the header says"*); its note reached the server as a *reader stop*, so Shavez's tile said *"aapko kuch
nahi karna"* and the 28-Oct sale never came. The closing stock of 28-Oct was taken (09:08 and 09:53, VERIFIED).

## What changes — three files, two machines (`make_s679.py`, every anchor exactly once)
| file | FROM | TO | what |
|---|---|---|---|
| medical PC `D:\SendToClinic\marg_txt.py` | 18fa8a83 | aa7baee5 | a bill row whose D.R. holds a word that is not a payment head (no leading `.`, not blank / `#`, not CASH / UPI however printed, a space on its left) → refused: *"line N: bill <no> is billed to the party account <name>, not cash or UPI -- correct the bill in Marg (Cash or UPI), then export again"*. VERSION S679. |
| medical PC `D:\SendToClinic\marg_watch.py` | 39fa2773 | a009d2fd | the note may carry the **bill number** (exempt from the six-digit mask) and **never the party's name**: *"the reader refused it: bill <no> is billed to a party account, not cash or UPI"*; idempotent for Drive's .why. Start line S679. |
| server `/root/finance/reports_tile.py` | 535b5790 | 03902a5d | `hindi_reason` names it first (above). Not a reader stop (S556's exact pattern), not matched by DUTY_MAP's reader-stop GLOB → the row is *wrong* and `shavez.sale_report` stays due. |

The server reads cash from the CASH column and non-cash as NET − CASH; it never read the D.R. word. Nothing else downstream changes.

## The proof
- **Medical side** (`walk_s679_pc.py`, run on manojz's VM over the medical PC's mirror — no patient text leaves the PC side): **11 of 11
  green** — made-up texts (party → named; `.CASH`, `.UPI`, blank, `#`, `.CASH #`, `.UPI #` → the same bytes as the old reader; `CASH`, `UPI`, `-CASH`, `# .CASH` → never a party, the old refusal; a run-in
  description and an off-column word → the old refusal word for word), the note (bill out, party never, idempotent, masking kept), all
  47 kept reasons → the old note, **all 155 distinct kept texts → the same bytes or refusal under old and new, the 2 copies of the 28-Oct
  text apart (now named, bill A004482)**, the reader's own selftest clean. Control on the live pair: 3 S679 checks red. The watcher's
  own selftest: 72 OK, no FAIL (old and new).
- **Server side** (`walk_s679.py`): **7 of 7 green** on the 29-Oct database copy; old = new over all 25 distinct stored (reason, verdict)
  pairs; control on the live file: 2 S679 checks red · 0 older red · 4 green.

## Install
**Server** (the owner's one line, after the publish):
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s679kit && cp -rp /root/deploy/repo/deploy_kits/S679_SALE_BILLED_TO_PARTY /tmp/s679kit && bash /tmp/s679kit/install_S679_SALE_BILLED_TO_PARTY.sh
```
**Medical PC** (the chat, through the file tools — F-764): Drive `ToMedical\_kit`: each FROM read first; `marg_txt_S638.py.superseded`
and `marg_watch_S556.py.superseded` kept beside; the manifest (CRLF; the `marg_txt.py` line's md5 → aa7baee5…, an S679 comment) then the
two files, each read back. The agent installs at its next kit check and restarts the watcher (marg_watch.py changed). **It covers new
exports only:** a text already refused and noted (the 28-Oct one) is not noted again (`_keep_refused` and the `.note` marker), so the
server keeps its old reader-stop row for it -- Shavez was told directly to correct A004482 and export again (an independent review's find). Read on the heartbeat: watcher md5 a009d2fd, `marg_txt.py` aa7baee5, *"marg_watch
S679 starting"* in the log.

## Undo
Server: `\cp -p /root/finance/reports_tile.py.bak_S679_535b5790 /root/finance/reports_tile.py && systemctl restart clinic-finance`.
Medical PC: put the two `.superseded` files back as Drive `_kit\marg_txt.py` / `marg_watch.py` and the manifest's line back to 18fa8a83.
