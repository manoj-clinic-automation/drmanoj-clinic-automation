# S966_WA_BSUID — Meta's WhatsApp ID read as an ID, never as a number

**The parent, S531, 27-Nov-2026 · his "yes" 09:26 IST · MyOperator's mail of 26-Nov-2026 20:30 IST** ("WhatsApp webhook users: 5 days left to update").

## Why

From 1-Dec-2026, a WhatsApp event from MyOperator may carry Meta's **Business-Scoped User ID (BSUID)** in `customer_identifier` instead of the patient's mobile: `IN.` followed by 128 characters, up to 131 in all. A `meta_bsuid` field may come beside it. MyOperator asks every integration to do three things:
1. Treat `customer_identifier` as a mobile only when it is all digits, and as the BSUID otherwise.
2. Store up to 131 characters.
3. Save `meta_bsuid` against the contact.

Message, delivery, read, failure and conversation events are affected. Call webhooks are not.

Before this kit, four live files read that field as a mobile and cut it down to digits. A fifth, the Call Consoles' chat key, would have done the same to any chat the inbox keeps under a BSUID (cold review, MUST):

| file | what it did with a BSUID |
|---|---|
| `/root/wa/wa_receiver.py` | wrote a made-up digit string into the WA_Inbox sheet's phone cell |
| `/root/wa/wa_alert.py` | put a made-up number on the phone alert, and could look up a wrong patient name |
| `/root/portal/portal_inbox.py` | keyed the chat on the last 10 digits pulled out of the ID: a made-up number that a reply or a call would have gone to |
| `/root/finance/records.py` | fingerprinted the made-up number when suggesting a patient for a photo |
| `/root/portal/calls_console.py` | `_s871_key` cut a BSUID-keyed chat into a made-up number. That number was listed on his and the staff Call Console (and on the patient lists), where a template or the Call button could reach a stranger |

## What it does

The rule is the same in all four files. A value with **no letter** is a mobile (every number seen so far). A value **with a letter** is the BSUID. A BSUID is never cut into digits, never sent to and never dialled.

- **Receiver:** a BSUID-only push writes its row with the phone cell **empty**. The message is kept, and the raw log keeps everything as before. A `bsuid` value is written only if the tab ever gets a "bsuid" column.
- **Alert:** a BSUID-only push still alerts. The alert has no number, and its first line says "(WhatsApp ID - no mobile number)".
- **Inbox:**
  - A BSUID-only message is stored under the BSUID, as its own chat. It shows as "WhatsApp ID (no number)", with no MyOperator number link and no call button.
  - When a push brings a mobile together with a `meta_bsuid`, the pair is remembered in a new table, `s966_bsuid` in `inbox.db`. Any chat kept so far under that BSUID moves to the mobile, along with its "read" mark. Later BSUID-only messages from that person join the mobile's chat.
  - A send, template, call, staff text reply or staff template to a BSUID chat is refused in words: "This patient wrote on WhatsApp with a username, so there is no mobile number to reply to or call from here. Reply from MyOperator's own WhatsApp page." The sender itself also refuses, before any network call.
  - A BSUID chat is not counted as a "number abroad".
- **Records:** a BSUID is never fingerprinted. The photo is still listed, with no patient suggested.
- **Call Consoles:** a BSUID chat key gives no number, so it is never listed. `ivr_call` refuses any value with a letter before anything is dialled.
- **A BSUID in `customer_identifier` means the push has no mobile** (MyOperator: the BSUID comes *instead of* the mobile). No later field (`customer_number`, `context.from`, `contact.wa_id`) is trusted for one, and nothing is paired from them (cold review, SHOULD 2). A pair is remembered only from `customer_identifier` digits plus a `meta_bsuid`.

**Not in this kit (stated decisions, for a follow-up once real BSUID events arrive):**
- A BSUID-only chat that has never been seen with a mobile appears in his Inbox and his alert, but not on the two Call Consoles' lists. They list chats by number only.
- A STOP sent from such a chat is not put on the WhatsApp ladder's stop list. `wa_ladder.m10` reads no number from it (cold review, SHOULD 1). Before this kit it could have stopped a made-up number.
- The WA_Inbox sheet (Apps Script) now gets an empty phone cell for such a row. Nothing on the server reads that cell for a BSUID chat.

**With no BSUID in a push, every file behaves exactly as before.** Two walks prove it:
- **`same`:** 12 made-up push shapes. The sheet row, the alert, the inbox's read of each push, the inbox store, records' sender, and the inbox and console chat keys are all equal, FROM against TO.
- **`replay`:** at install, on the box. It reads the REAL raw pushes of the last 30 days, read-only, through both sides. Only counts are printed, and every push must give the same result. A phone field holding an unknown lettered value (anything other than Meta's `XX.` shape) stops the install (cold review, SHOULD 3).

## Files

| live file | FROM | TO |
|---|---|---|
| /root/wa/wa_receiver.py | 793f0182 | see TO_PINS.md5 |
| /root/wa/wa_alert.py | 89c08929 | see TO_PINS.md5 |
| /root/portal/portal_inbox.py | 1c1fc915 (S959) | see TO_PINS.md5 |
| /root/finance/records.py | 274460dc | see TO_PINS.md5 |
| /root/portal/calls_console.py | 19023822 (S959) | see TO_PINS.md5 |

The TO files are made by `make_s966.py` from the FROM bytes of the 27-Nov bundle, by exact anchored replacements: every anchor must occur the stated number of times, or nothing is written. The installer makes them again from the live bytes and requires the result to equal the kit's TO.

## Install

On the server, as one line, after his publish:

```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s966kit && cp -rp /root/deploy/repo/deploy_kits/S966_WA_BSUID /tmp/s966kit && bash /tmp/s966kit/install_S966_WA_BSUID.sh
```

The installer runs in five steps:
- **[1/5]** checks the kit sums.
- **[2/5]** checks the ground: all five files are FROM, or all five are already TO.
- **[3/5]** runs on the box's own Python. It remakes the files from the live bytes, then runs the walk (green on TO), the control (red on FROM), the `same` walk (green) and the `replay` of the real pushes (green).
- **[4/5]** takes backups `*.bak_S966_<from8>`, swaps the files in and reads them back. It then restarts wa-receiver (at a quiet moment, with no push in the last 20 s), then clinic-portal, then clinic-finance. Each service must answer.
- **[5/5]** checks the journals: no "wa_alert NOT loaded" and no "records NOT mounted".

Any red after [4/5] begins puts all five files back and restarts the services. So does a killed run. `DRY=1` runs [1]-[3] only. `--undo` puts the five backups back and says how many chats are kept under a BSUID: the old code would read those as numbers (cold review, SHOULD 4).

## Proof

- **walk:** 29 checks on the TO, all green. The control on the FROM is 24 red. The added checks cover: a BSUID with a fallback field, re-reading the same pushes, the same BSUID with a new mobile, the console key and the call guard.
- **same:** 8 checks, all green.
- **cold review:** 1 MUST and 4 SHOULD. The MUST and SHOULDs 2, 3 and 4 are built in. SHOULD 1 is stated above. SHOULD 5 is built in as far as the routes allow offline: the routes are proved by their source.
- **second look:** SAFE, no MUST. Two SHOULDs, both built in:
  - The replay gives a push with no time of its own a fixed time, so "now" never enters a result.
  - The replay copies the live, growing logs once, and both sides read that one copy.
- **rehearsal:** 12/12.
- **JS:** run under node: "WhatsApp ID (no number)", no MyOperator link, and "WA" as the initials.

There is no live BSUID to read yet. The first real one will show in his Inbox as "WhatsApp ID (no number)", or straight under the patient's number if it came with one.
