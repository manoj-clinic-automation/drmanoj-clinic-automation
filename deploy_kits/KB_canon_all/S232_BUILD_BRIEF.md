# S232 BUILD BRIEF — the one document to read before starting

*Written at the S231 close, 08-Sep-2026. It replaces reading this session's papers. Read this, then
Runbook v163 §2, then start.*

---

## 1 · WHERE THE ESTATE STANDS

S230 taught the estate to notice when something stops. **S231 found out what it had not been
noticing at all: its own secrets.**

| | state |
|---|---|
| the four S230 VPS pins | **CONFIRMED** — read back from the box, all four matched their predictions |
| the freshness layer | cron `5 8 * * *` verified registered on an IST box; now on the owner's private system topic |
| the ntfy topic | **rotated** out of a public repository into `/root/wa/.env` alone; five live places moved; proof taken from `/proc/<pid>/environ` |
| system vs message alerts | **split** — staff no longer receive the owner's watchman and health alerts |
| the WhatsApp push | carries the **full message text** (D419); message column found at index 4 |
| the WABA token | 🔴 **CONTAINED, NOT REVOKED** — see §4 |

## 2 · THE FIRST THING TO BUILD — the secret gate

**On 16-Jun-2026 a live MyOperator WhatsApp credential was saved into the public repository by a
mistyped shell command.** The file was called `python test_send.py`, with a literal space in the
name. It carried the Bearer token, the company ID, the phone-number ID and a real mobile number — a
complete, runnable set. **It sat there for 84 days and nothing was looking.**

The rotation is the owner's to arrange. **The gate is ours, and it is the durable half.**

**What it must refuse:** `Authorization: Bearer <literal>` · `-----BEGIN ... PRIVATE KEY-----` · a
bare 10-digit number · secret-shaped assignments (`TOKEN`, `SECRET`, `API_KEY`, `PASSWORD`,
`AUTH`) carrying a literal value of meaningful length.

**What it must NOT refuse, or it will be switched off within a week:**
- `os.environ.get("MYOP_AUTH_TOKEN", "")` — **69 of these exist and they are the correct pattern**
- names-as-constants: `MYOP_TOKEN_KEY = "MYOP_LOGS_TOKEN"`, `SALT_ENV = "PATIENT_FP_SALT"`
- file paths: `DEFAULT_DRIVE_TOKEN = "/root/wa/recordings-archive/drive_token.json"`
- placeholders: `PUT-THE-TOKEN-HERE`, `PASTE…HERE`, `<paste the … token here>`, `«MASKED-S230»`
- selftest fixtures — `CRON_TOKEN` in 51 files, `SECRET/SECRET_PREV` in `call_hook_capture.py`,
  `marg_token="wa…en"` in the walk harnesses
- `credentials:'same-origin'` (99 hits), `password_hash=?` SQL placeholders
- md5 pins and hash constants

**That list is not guesswork** — it is the exact false-alarm set from the S231 census, every entry
opened and ruled out in context. Build the gate against it and it starts life calibrated.

`deploy_kits/NO_PHONE_NUMBERS.py` already runs in `PUBLISH_ALL.bat` and already refuses on numbers.
**Widen that, do not build a second gate.** One gate, one place, or neither gets maintained.

## 3 · THEN, IN ORDER

**⭐2 · The F-363 repair — ONE atomic step.** `HANDOFF_RUNBOOK…Session229close_v161.md` on disk is
7,589 bytes; the true document is 7,607. The file, its `MD5SUMS_ALL.txt` row and its manifest row
must move **together**. Change the file alone and the next Phase 0 halts at 406/406.

**⭐3 · The staff advance policy document.** Both stored copies are wrong and the owner said so. The
50% capping reference and the **waive-the-signed-application-as-pending** path are live and in
neither. Rebuild from `staff_ledger.py` and the D331 → D332 → later trail. **Trust neither copy.**

**⭐4 · F-368 hygiene** — six stale `.env` copies in `/root/wa/` and three stale code copies in live
folders. After the WABA rotation their WhatsApp token is dead, but they hold every other secret in
that file. Not to be touched mid-rotation.

**⭐5 · 1.7 renewals** — the clock is gone (D422 ruled both entries), so this is tidiness now. Then
the eight missing technical vendors, **Tailscale first**.

**⭐6 · 1.9 the medical PC capture chain** (F-362) — prepared, not applied.

## 4 · WHAT IS BLOCKED, AND ON WHAT

🔴 **The WABA rotation is blocked on ONE answer** from MyOperator (Ms. Khushi Jain): **do the old and
new tokens overlap, and for how long?** If they do, this is calm and staged. If they do not, it is a
timed change to four places with patient messaging down in between. **Do not start the rotation
before that answer arrives.** The inventory is complete and measured:
`claude/S231_WABA_TOKEN_ROTATION_INVENTORY.md` — four stores, and canon's claim of a second VPS store
is corrected there.

## 5 · THE FIVE RULES THIS SESSION COST MOST TO LEARN

1. **A count in a record is a claim, not a measurement.** "Two copies" was sixteen files.
   "Flattened to ASCII" was a document nobody had flattened.
2. **Two stores agreeing is not correctness.** A byte sweep is blind to a document that agrees with
   itself everywhere and has been overtaken by reality. The owner caught that in one sentence.
3. **A rotation's blast radius includes people.** Four devices went dark and reception stopped being
   nudged, with no error anywhere.
4. **Search by VALUE, not by the shape it takes in one file.** A URL-shaped search walked past a
   bare-name copy and would have produced a half-rotation.
5. **`is-active` is not proof.** Read the running process, or the log line the code prints itself.

## 6 · TWO THINGS THAT ARE NOT IN ANY BACKLOG BUT SHOULD BE SEEN

- **`D:\Downloads\Projects\_Infrastructure\Credentials\`** — ten plaintext files including
  `github-recovery-codes.txt`, an SSH key as a PNG, WordPress and Hostinger logins. Listed, never
  opened. **A larger single point of loss than anything fixed at S231**, and the reason D421 sends
  everything to Bitwarden.
- **`.env` is deliberately EXCLUDED from the off-box backup** by pattern. Defensible — but it means
  there is no off-box copy of the SMTP password or the service-account key. D421 is the answer.

---
*S232_BUILD_BRIEF · S231 close · next free **D425 · F-369**.*
