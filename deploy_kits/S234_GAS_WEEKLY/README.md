# S234_GAS_WEEKLY — the weekly Apps Script re-export, and the drift it exists to find

**Session 234 · 08-Sep-2026 · detour item 4 of D432.**

---

## What it is

A weekly job on the VPS that re-downloads the three unversioned live Apps Script
projects and **compares them twice**:

1. **against last week's export** — *what changed in Google this week*
2. **against the repository copy** — *how stale is the copy everybody reads*

**It is not a backup job with a diff bolted on. It is a drift detector that
leaves a backup behind.** The backup half is nearly free: the exports land in
`/root/state_backup/gas/`, which the 01:50 encrypted bundle already carries.

## The fault it closes

S230 found **2,122 lines of live clinic automation in no repository at all** and
exported three projects by hand into `deploy_kits/S230_GAS_EXPORT/`. That export
is a photograph taken on 07-Sep-2026 and **nothing refreshes it.**

The census had already measured what that costs, in the same document:

| file | live | repo |
|---|---|---|
| `gas/VPS_Push_UPI.gs` | 263 lines, 7 fns | 200 lines, 6 fns — **a whole generation behind** |
| `deploy_kits/S195_STMT/Bank_Statement_Relay.gs` | 44 lines | 74 lines — the pre-survey copy |

Both drifted silently. Both were found only because a session went and looked.
**This is the thing that looks.**

## 🛑 HOLD 2 is enforced in code, not in prose

The owner's standing instruction, 07-Sep-2026: the **Clinic Callback Tracker**
is not to be touched at all — *"no edit, no trigger change, **no re-export**, no
tidy"* — and its abandoned v1 ancestor falls under the same rule because it
carries an unscoped `removeTriggers()`.

So the tracker's id sits in a `DENY` map inside `gas_export.py`, and a settings
file naming it is refused with **EXIT 44 before a single network call is made.**
Lifting that takes a deliberate code change and the owner's word.

**A hold that lives only in a document is one config edit away from being broken
by a session that never read the document.** Two selftest checks assert the
refusal, including one that hides the denied id among valid entries.

## It reads Google and cannot write to it

No project edited, no trigger created, changed **or read**, no Script Property
touched. The scope requested is `drive.readonly`; the only endpoints in the file
are `files.get` and `files.export`. Three selftest checks hold that promise: the
scope, the absence of any other Drive endpoint, and the absence of any
`.post(`, `.patch(`, `.put(` or `.delete(` call anywhere in the source.

## Comparison is by content, and one file is compared on shape

Files are compared by **md5 of the exact bytes**, never by Drive's
`modifiedTime` — which moves when nothing meaningful changed and can sit still
through a same-second edit.

**One deliberate exception.** `DailyClinicReports/Code.gs` has four MyOperator
values masked in the repository copy (S230 §4), so it can never match live byte
for byte and would shout drift every week for ever — and a weekly false alarm is
how a real one gets ignored. That file is compared on **line count and function
names** instead, and the report says so. When those four values move into Script
Properties, the entry comes out of `MASKED` and byte comparison resumes.

## Refusal stances

| code | meaning | what happens to the existing export |
|---|---|---|
| 10 | no conf, no key, or no `GAS=` list | nothing written |
| 11 | the google libraries are not importable | nothing written |
| 41 | **PERMISSION** — a project is genuinely not shared | its previous export stands |
| 42 | a project lost files, or more than 20% of its lines | that project is not swapped in |
| 43 | **RATE LIMIT** after retries | nothing swapped |
| 44 | a denylisted project appears in the settings | nothing at all, no network call |

**41 and 43 wear different words on purpose.** At S233 a quota refusal printed
the permission message and would have sent the owner to Google to re-share five
sheets that were already shared correctly. One message for every failure is a
message that lies.

## Proof taken before handover

| gate | result |
|---|---|
| `gas_export.py selftest` | **31 checks, 0 failures** |
| `WALK_gas_install.py` | **26 checks, 0 failures** |
| `bash -n install.sh` | clean |
| `py_compile` | clean, to a temp `cfile` (F-376) |

The walk drives `install.sh` in a sandbox against a stand-in exporter and covers:
the ordinary install · a second run not duplicating the settings line · a project
not shared · a failing selftest never being installed · the export itself
refusing · an incomplete kit · and the shipped settings line naming three
projects, none of them the denied one. **Four of those assert the settings file
comes back byte-identical.**

## What is deliberately NOT in the export list

- 🛑 **The Clinic Callback Tracker and its dead ancestor** — HOLD 2, enforced in
  code.
- **The two personal-account projects** (Inbox Janitor, CC saver). They were
  exported by hand at S233 and live in two stores already, and **D431 bars them
  from the repository permanently** — their source carries passport, licence and
  policy numbers. Adding them here is a one-line settings change if the owner
  wants their weekly drift watched too; it is not taken unasked.
- **The four dead or empty projects** (#4, #7, #8, #9 of the census). Nothing to
  watch.

## F-378 — the second comparison did nothing, and said so in words that read as fine

**Found on the first live install, behind 24 green selftests and a 26-check
walk.** v1 read a folder's `_PROJECT.json` to learn what was in it. The
repository copy it compares against — `deploy_kits/S230_GAS_EXPORT/` — was
written **by hand** at S230 and has no `_PROJECT.json`, so v1 returned nothing
for it and the first real run printed, three times:

```
the repository copy is behind: nothing
    DailyClinicReports       (there is no repository copy to compare against)
```

The copy was right there. **The entire second comparison — the one that answers
"how stale is what everybody reads" — was inert, and its output looked like a
mild note rather than a failure.** That is the S208/S209 shape again: green
gates, and only running it against the real thing found it.

**v2 builds the metadata by reading the files on disk when there is no meta file,
counting lines and hashing exactly as the exporter does.** Five selftest checks
now cover it, including one asserting that a matching hand-made folder reports
**nothing** rather than "no copy".

**And one more thing v2 does because of it:** a file differing only in trailing
whitespace is reported as `changed_whitespace` — *"differs ONLY in trailing
whitespace — not an edit"* — because the S230 export has one file without a
final newline and a weekly false alarm is how a real alarm gets ignored.

## Files

| file | what it is |
|---|---|
| `gas_export.py` | preflight · run · diff · list · selftest |
| `install.sh` | ten stages; restores the conf on any failure |
| `GAS_LINE.txt` | the settings line, three projects |
| `WALK_gas_install.py` | drives the installer in a sandbox, every failure path |
| `INSTALL_ONE_PASTE.txt` | the two lines, and what each exit code means |

---
*S234_GAS_WEEKLY · Session 234 · built offline, walked, installed by the owner
from two lines.*
