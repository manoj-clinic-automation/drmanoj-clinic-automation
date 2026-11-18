# S871_WA_FOREIGN_NUMBERS — the parent, S480, 18-Nov-2026

**His word:** "go" (13:09 IST). He confirmed in MyOperator (13:18) that the "20171 69002" WhatsApp chat was a US number (+1).

**The fault:** `portal_inbox.last10()` kept the last 10 digits of every WhatsApp sender and assumed India. For a sender from abroad:
- Reply went out as +91 plus the cut number. MyOperator refused it three times on 13-Nov: "Recipient phone number is invalid".
- The inbox and the Call Console showed "+91 …".
- Call rang an invalid Indian number.
- The inbox's "MyOperator" button opened the chat under /91/.

**The change** (`make_s871.py`, exact anchors, FROM md5 checked):

| file | FROM | TO |
|---|---|---|
| /root/portal/portal_inbox.py | ff0f02a8 | 6abc6461 |
| /root/portal/calls_console.py | 36f6221c | eb13790d |

`portal_inbox.py`:
- **Chat key.** Indian numbers (10 digits, 91+10, 0+10, 0091+10) are unchanged. A number abroad (11–15 digits) keeps every digit, country code first. The key is idempotent.
- **Patient list.** It keeps the old last-10 rule (`ten()`).
- **Sending.** `myop_send` splits the code from the number with the ITU code lengths, so the US goes out as `1` + 10 digits. India still goes out as `91` + 10.
- **Send log.** The CSV and the mail text write the whole number. The log page shows "+<number> (abroad)".
- **Refusals.** Templates and Call are refused for a number abroad, in plain words.
- **Inbox page.**
  - It shows "+1 xxxxx xxxxx · abroad".
  - The MyOperator link uses `/<code>/<number>`. This was checked live on 18-Nov: `/1/<10 digits>` opened the same conversation.
  - No Call button is drawn for a number abroad.
- **Once-only move.** On the first ingest, a chat stored under a cut key is moved to the whole number, using the raw pushes. The marker `offsets.fname='s871:rekey'` stops it running again.
  - When two numbers share one cut key, nothing is moved.
  - When the cut key looks like an Indian mobile (starts 6–9), only that sender's own messages are moved.
- **Health.** Unchanged (S859's walk pins its keys). The count of chats abroad is `abroad_count()`, a count only.

`calls_console.py`:
- WhatsApp items keep the whole number.
- `fmt_num` shows "+1 xxxxx xxxxx · abroad".
- `ivr_call` refuses a number abroad.
- The awaiting card has no Call button for it.
- `callBack()` refuses it, and every other Call button for it is hidden on load.

**Cold review:** NOT SAFE on the first build. It found two MUST, two SHOULD and four LOW points. All of the following are built in now:
- **MUST 1.** `wa_items` kept only 10-digit keys, so the chat would have vanished from the Console.
- **MUST 2.** `wz_write` and the marks door refused any key but 10 digits.
- **SHOULD 3.** The move now runs in a SAVEPOINT. A failure rolls back only the move; the mark is written and the ingest goes on.
- **SHOULD 4.** The raw files are read before the write lock is taken (`s871_plan`). Only the UPDATEs run under it (`s871_apply`). The proof prints both times.

The first build's Console file goes red on H12, H13 and H15.

**Known and accepted (LOW):**
- A sender whose whole number is 10 digits including the country code (e.g. Singapore 65 + 8 digits) is still taken as Indian.
- An Indian number typed with an extra digit, e.g. 11 digits not starting with 0, now reads as "abroad". Only the sheet or CSV inputs can produce this; the webhook never does.
- In the 6–9 branch only the sender's own messages move; our failed replies, the read mark and any retry row stay under the cut key.

**Proof in the build:**
- walk_s871 58/58 on made-up numbers (54 where node is missing). Its control on the FROM files went red at 18/46.
- S870's walk 20/20 and S817's walk 48/48 + 10 mutations gave the same result on old and new.
- S859's inbox walk 24/24.
- S666's walk 20/23 on both old and new (its frozen expectations, unchanged).

**Install:** his publish, then one server line:
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s871kit && cp -rp /root/deploy/repo/deploy_kits/S871_WA_FOREIGN_NUMBERS /tmp/s871kit && bash /tmp/s871kit/install_S871_WA_FOREIGN_NUMBERS.sh
```
Undo: `bash /tmp/s871kit/install_S871_WA_FOREIGN_NUMBERS.sh --undo`. A chat already moved stays under its whole number; the old files still list it, just shown as digits.
