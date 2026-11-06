# S713_GMB_SAVE — the GMB Review Assist keeps every draft and your edit · the parent · session 389 · 06-Nov-2026

**For the owner, in two lines.** Every time you press Generate or Fresh variation, the page now saves your ticks and the three drafts on the server, behind your login. A new **✓ Shared** button sits beside Copy. Pressing Copy, WhatsApp or Shared also saves the text that was in the box at that moment, so your edits are no longer lost. The drafts themselves are unchanged.

## Why
D832 Part B. The owner's OK came at 14:58 IST on 05-Nov (`claude/S385_GMB_PLAN.md`) and his "Yes" at 08:45 IST on 06-Nov:
> *"Each press is kept on the server behind your login (never in the repository): the ticks, language, size, the three drafts as generated, and — when you change the text before sharing it — the text as shared. A 'Shared' button beside Copy records that moment. Your edits are the only real signal of what sounds right; today they are lost the moment you copy."*

The live page (d9aad642, S707; read 06-Nov 08:4x IST through the owner's login and found byte-identical, sha-256 ba303d4f…) saves nothing at all: it makes no network call and uses no browser storage.

## Files
| live file | FROM | TO | what |
|---|---|---|---|
| `/root/portal/portal_gmb.py` | — (new) | a4606e4c | Three doors behind the portal's doctor gate: `POST /portal/gmb/api/press`, `POST /portal/gmb/api/share` and `GET /portal/gmb/api/health`. A save also needs the page's own `X-Gmb: 1` header; a page on another site cannot send that header without being refused first. The store is one SQLite file, `GMB_STORE_DB`, by default `/root/portal/gmb_store.db`. It is data: it never goes into the repository, and never into the nightly code bundle, which carries no `.db` (the 05-Nov MANIFEST has none). It has two tables. **press**: IST time, who, language, relation, the ticks as JSON, and the three drafts exactly as generated. **share**: which draft, how (shared / copied / whatsapp), the text in the box, and whether it was edited. **No phone number is kept:** any run of 7 or more digits becomes `[number]` before it is written, and the page never sends a number (WhatsApp opens with none). |
| `/root/portal/portal.py` | a93da673 | 5cf80f82 | The live file plus **one** mount block, after the Call Console's block. The walk proves it: the new file with the block cut out is the live file, byte for byte. The block sits inside `try`, so a failure to load costs only the saving. The page is still served by the existing `gmb()`. |
| `/root/portal/gmb.html` | d9aad642 | 964f0288 | A **✓ Shared** button beside Copy and WhatsApp on each draft. Generate and Fresh variation each send one save. Copy, WhatsApp and Shared each save the text in the box. One small line under the header says *Kept on the server.*, or *Not kept this time — Copy and WhatsApp still work.* Shared answers *✓ Noted*, *✓ Noted, with your edit*, or *Not noted* (it never pretends). **The S707 wording engine is untouched:** the 561 lines from the phrase library to the GENERATE section are identical. |

## Proven (session 389, the cloud workspace; the three live files from the 05-Nov bundle and the S707 kit = the pins)
- `walk_s713.py` (the installer runs it on the server) — the module on a made-up store: **14 of 14 green**. It checks the mount block, the header gate, each refusal, the drafts as generated, IST times, no phone numbers, edited / not edited, the counts, that a refusing gate refuses all three doors, that the store is a `.db`, and that nothing else is written. **Control** on the live tree (no module): **14 S713 check(s) red . 0 green**.
- `browser_walk_s713.js` — the page in Chromium at PC and phone width, served over http, with a made-up API: **32 of 32 green**. It covers one save per Generate carrying exactly the shown drafts and the ticks; Copy, Shared after an edit, Shared unedited and WhatsApp, each saved with the right draft and kind; Fresh variation as a new press; with the server down, the plain warning line, Copy still working and *Not noted*; no sideways scroll; no script error. **Control:** the live page goes red at once.
- `browser_walk_s707_served.js` — S707's own page walk on the new page, unchanged except that it is served over http with the API answering: **BROWSER OK 162/162**. Opened as a bare file it reports 2 red, both the browser's "cannot fetch" console line; the real page is never opened that way.
- The installer rehearsed on a made-up server (see the close report).

## Cold review (independent agent, S389)
**SAFE TO INSTALL**, no blocker. Its six should-fix points, all handled:
1. The number mask now also catches 98765.43210, 98765–43210 and (98765) 43210.
2. The mask runs on the tick values before they become JSON, so the stored JSON stays valid.
3. A Copy, WhatsApp or Shared pressed before the server has answered the press now waits for the press id and is still kept. The saves use `keepalive`, so opening WhatsApp does not cut them off.
4. The installer makes the store once, so two workers never race to create it.
5. The installer checks the new door through the public address as well as the server's own port.
6. **The store is in no backup yet.** It is deliberately out of the code bundle, and nothing else copies it. Adding it to the encrypted state backup is an open item for the parent's backups; it gets a fault number at this session's close. Losing it would cost only the learning record, never the page.

## Reading the store later
The store may hold whatever was typed into a draft. It is read **on the server** by a measuring script that reports counts only (which sentences were cut, which words were swapped, which closings were kept). It is never copied off the server whole.

## Install (on the server, after the publish; window 04:00–23:30 IST)
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s713kit && cp -rp /root/deploy/repo/deploy_kits/S713_GMB_SAVE /tmp/s713kit && bash /tmp/s713kit/install_S713_GMB_SAVE.sh
```
## Undo
```
\cp -p /root/portal/portal.py.bak_S713 /root/portal/portal.py && \cp -p /root/portal/gmb.html.bak_S713 /root/portal/gmb.html && mv /root/portal/portal_gmb.py /root/portal/portal_gmb.py.s713_removed && systemctl restart clinic-portal
```
