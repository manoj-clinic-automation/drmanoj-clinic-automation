# S550_CLAUDE_READS_SCAN — Claude reads the scans (D723, S314)

**What it does.** Every new scan in the scan app is read by Claude first: printed bills, handwritten estimate slips and
challans. Claude fills only what is still empty: the supplier, its phone and email, the number, the date, the amount, and
the items with their make, model, serial, batch, expiry and HSN. The app's own after-checks then run unchanged: the month,
the double guard, the S441 checks and the way home. When Claude cannot read a scan, Sarvam reads it exactly as before.

The scans already in the app are read once in the background, oldest first. A paper still to be sorted, with something
empty, is filled through the app's own filling step, exactly like a new scan. An approved paper is read and its reading
kept, but nothing on it is written. Every reading is kept, in the table `claude_reading`, for the sorting desk (S551).

**What it does not do.**
- It never overwrites what a person typed.
- It never writes anything on a pharmacy paper (the lane, or an old row's kind). Claude reads it alongside Sarvam in its own
  thread and the reading is kept aside. Sarvam fills the paper as before and never waits for Claude.
- It never sends to Claude the Other-document lane or the Personal and Resumes sections. Those stay with Sarvam, as before.
- It never keeps a person's name. Only the listed fields are stored; who a paper is made out to is kept as a kind
  (clinic / doctor / patient / other), never as a name. No free-text note is kept.
- It never shows, logs or backs up the key.

**The key.** The owner's key named *scanapp-reader* is typed once, at a hidden prompt, by the installer. It is stored at
`/root/.scanapp_secrets/anthropic.key`: the folder is 700, the file is 600 and root-only. The key is not in the repository,
not in a backup and not in the database. The call-judging key is a different key and is untouched.

**It stops by itself.** If Claude refuses the key or the credit runs out, the setting `read.claude` becomes
`stopped:<why>` and Sarvam carries on. There is also a daily limit of 400 calls by default, retries included, in the setting `read.claude_daily_cap`. The re-read of the older scans leaves 50 of those for new scans and resumes the next day. A failed attempt never replaces a good reading.

**The owner's switch.** It is on this page, in the card *Reading the scans — Claude*. The card shows ON or OFF, today's
count, the model in use and the older scans' progress:

```
https://followup.dr-manoj.in/scanapp/admin
```

**Files.**

| File | Status |
|---|---|
| `/root/assetapp/asset_register.py` | `99652ff0` → `3d5a36e3` (13 counted edits) |
| `/root/assetapp/claude_reader.py` | new, `3894dc23` |
| `/root/assetapp/claude_reread.py` | new, `47548ab9` |

`clinic_papers.py` and `scanner_widget.js` are untouched.

**Install (server):**

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S550_CLAUDE_READS_SCAN/install_s550.sh
```

To replace the key, run the same line with `--new-key` at the end.

**Undo (server):**

```
cp -p /root/assetapp/asset_register.py.bak_S550_99652ff0 /root/assetapp/asset_register.py && rm -f /root/assetapp/claude_reader.py /root/assetapp/claude_reread.py && systemctl restart assetapp
```

**Proof.**
- The walk has 45 checks, all green. They cover:
  - good, model-not-found, busy, key-refused, credit-out and daily-limit answers;
  - a PDF sent as a document and a photo as an image;
  - fill-only-empty, Sarvam fallback, pharmacy kept aside and the owner's switch;
  - the key appearing nowhere, on the page or in the database;
  - the older-scans pass, including its stop on a refused key.
- The control on the live file goes red (7 checks red).
- An independent cold review found 1 blocker (the made-out-to name) and 11 should-fix items; all are fixed and walked.
- Rehearsed on a made-up root against a stand-in for Claude:
  - fresh install;
  - ALREADY INSTALLED;
  - a bad key text refused;
  - a refused key, which leaves Sarvam in charge;
  - a good key after a refused one;
  - health red, which restores;
  - a wrong live pin, which is refused.
