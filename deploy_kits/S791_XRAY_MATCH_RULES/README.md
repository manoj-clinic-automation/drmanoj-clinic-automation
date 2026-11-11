# S791_XRAY_MATCH_RULES — the 8 rules for X-ray photos still waiting (D906), and the payment-gap highlight

**The owner, 11-Nov-2026 09:41 IST:** *"bring a plan so that maximum patients can be matched through all the data pipelines … and we
only flag those here which really need to be flagged."* — **09:45 IST:** an X-ray of someone not registered *"could be a payment gap.
So they should also be highlighted."* — **09:57 IST:** *"First, complete this X-ray and lab report section."* Plan: `claude/S428_XRAY_MATCH_PLAN.md`.

## What changes (three files, finance restarted once)
| file | from | to |
|---|---|---|
| `/root/finance/check_screens.py` | dc713523 (S789) | a8a3552c |
| `/root/finance/records.py` | a2481f74 (S787) | b81e4e8f |
| `/root/finance/owner_console.py` | 97d63d71 (S786) | 2c77db31 |

**check_screens.py.** Before each filing plan (the mailbox script asks every 15 minutes), after S788 and S787, every waiting photo is
tried by the rules; each writes a "system · S791 <rule>: why" answer that the next filing run files, and each needs exactly ONE patient:
- **B** the number on the file is a patient who came on the film's day ±1, and the film reads the same number or the name's first
  word is his (no X-ray slip → it shows under "X-ray taken, no X-ray slip"); never when the name is another visitor's (that is C).
  Also: the ID printed on the film is an X-ray patient who came and the name is his by its first word or consonants.
- **A** the name, spelt the ways staff spell it (short words kept, vowels left out, two letters swapped) is exactly one patient who
  came, he had an X-ray, every number his ID / one keystroke off / two digits swapped / no real ID (a misread film).
- **C** as A, and a number is a patient who came that day without an X-ray (typed wrong at the machine).
- **D** only the first name was written and only one patient who came that day ±1 has it.
- **E** S787 (another photo of a patient filed that day) with A's wider spelling.
- **F** nobody who came that week has the name; exactly one patient in the whole list does (two words or more) → filed, and the
  X-ray goes on Shavez's "X-ray to bill" list by itself until a slip is made.
- **G** nobody in the whole list and nobody that week → "Not in Docterz" by itself, raised as a **possible payment gap**.
- **H** stays for a person: two or more possible patients, a number and name no rule settles, a day with no slip or Docterz line
  (the card now says the photo's date may be wrong).

**Payment gaps** (every "Not in Docterz" X-ray, marked by a person or by G): red tile on his X-ray page, a red line on his console's
Needs-you (owner_console.py), the photo card on Shavez's Check karein and in his Aaj ka kaam count. Closed only by a person: **billed**
(the photo given an ID once registered) or **explained** in one tap — Staff · Family / own · Free · Billed another way (key `pg:<drive id>`).

**records.py.** A photo given an ID files on the patient's X-ray day the film's date points to, not the day it was uploaded again
(so a re-upload no longer raises a false "no X-ray slip").

**F-1264.** check_screens.py's docstring no longer names a patient or IDs; kits S787 / S788 / S789's papers were scrubbed the same
way and their SUMS remade (they are history now). This kit's `walk_s787.py` / `walk_s788.py` are those kits' walks, scrubbed; S787's C1
now allows S791's answers alongside S787/S788's.

## Proof (11-Nov copy, 03:15 IST, in the device VM)
39 waiting photos (29 cards) → **28 answered**: B 7 · A 3 · C 2 · D 2 · E 1 · F 1 · S787/S788 5 · **G 7** (4 cards → payment gaps);
**8 cards left for a person** — each one the plan marked unsure. Walks: **S791 24/24** (the rules, five made-up-namesake guards, the
explain door 403/400/200/409, rule F on Shavez's list, the film's-day filing, both pages render and their scripts parse) · S787 22/22 ·
S788 10/10 · S789 3/3 · the CONTROL red on the live files. `make_s791.py` remakes all three from the live bytes, byte-exact.

## Install (after the publish), one line on the server
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s791kit && cp -rp /root/deploy/repo/deploy_kits/S791_XRAY_MATCH_RULES /tmp/s791kit && bash /tmp/s791kit/install_S791_XRAY_MATCH_RULES.sh
```
Undo: `bash /tmp/s791kit/install_S791_XRAY_MATCH_RULES.sh --undo` (answers already given stay; each is on his "Filed by themselves"
tile with "Wrong patient? Move").
