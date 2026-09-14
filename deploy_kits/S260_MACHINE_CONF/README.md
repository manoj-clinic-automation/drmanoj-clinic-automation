# S260_MACHINE_CONF — Club C.3

*Session 256 · 14-Sep-2026 · one settings file per machine · manojz*

## What this is

Where the medical PC is, where the clinic server is, where this PC keeps its key
and which day the stock figure walks forward from were written into **four files
between them** — the address alone appeared four times. Moving the medical PC
meant editing four files and remembering all four. On 26-Aug an eight-hour outage
turned on that link and nobody could say what the link *was* without reading two
files.

Now there is one file:

```
D:\Downloads\margsync\_config\machine.conf
```

Plain `KEY=VALUE` lines, `#` for a note. **A missing file, a missing key or a
blank value changes nothing** — every script keeps the value it has always used
as its fallback. That is the property the walk exists to prove.

| key | what follows it |
|---|---|
| `MEDICAL_HOST` | the pull's share, the key read over the wire, the probe the pull depends on, and the address the reporter carries |
| `MEDICAL_SHARE` | the same three |
| `SERVER_BASE` | both addresses this PC posts to |
| `TOKEN_LOCAL` | where the sender and the reporter look for the local key copy |
| `STOCK_BASELINE` | the day the computed stock figure starts from |

**The file is not in the repository** (F-185). It says where *this machine* is,
and that is not the code's business. It is also never typed: the installer reads
today's values **out of the live files themselves**, so it starts life saying
exactly what the PC already did.

## What changed, per file

| file | change | from | to |
|---|---|---|---|
| `MargPull\marg_gate.py` | `conf()` reader; `DEF_URL`, `DEF_TOKEN`, `DEF_TOKEN_UNC` derived | `af2c3ca5` | `52f502d1` |
| `MargPull\pipeline_status.py` | same reader; `DEF_URL`, `DEF_TOKEN`, `DEF_TOKEN_UNC`, `DEF_MEDICAL_HOST`, `DEF_SHARE_PROBE` derived | `f4998f61` | `31aad5e6` |
| `MargPull\PULL_FROM_MEDICAL.bat` | `MEDHOST` / `MEDSHARE` read from the file, after their own defaults | `39bd6ac8` | `f7855fa8` |
| `PUSH_STOCK_DAILY.bat` | `BASELINE` read from the file, after its own default | `5c2a6c90` | `5cbec862` |

`pipeline_status.py`'s from-pin is `f4998f61…`, **not** the `0b3dd968…` the KB
Register still records — the live bytes have been `f4998f61` since S205 and
`deploy_kits/S203_R3/SUPERSEDED.md` says so in as many words. Read off the machine
before a line was changed (F-411); the Register row is corrected at the close.

## The format is strict, and that is on purpose

`cmd.exe` splits on `=` and does **not** trim, so `KEY = value` would hand batch
the key `"KEY "` and the value `" value"`. The file is therefore written
`KEY=VALUE` with no spaces, the installer generates it that way, and the walk
checks the generator itself. The Python reader is tolerant of spaces anyway.

## Proof — 37/37, offline, on real copies

`walk_s260.py`: with **no** config file every value in both modules is byte-equal
to what it always was; a file of nothing but comments and a blank value changes
nothing; a real file moves the URL, the key path and the host — **and the share
path and the pull's probe follow the host from one line**; a config path that
cannot be read falls back instead of crashing; and the two `.bat` files set their
old value *before* reading, overwrite only on a present non-blank key, skip
comments, and use the value after reading.

`cmd.exe` does not exist off Windows, so the batch parsing is proved by reading
here **and by running on manojz** inside the installer, through
`probe_conf_s260.bat` — the same six lines as the two real jobs, and nothing else:
no pull, no push, no network.

## Installing

```
D:\dr-manoj-git\drmanoj-clinic-automation\deploy_kits\S260_MACHINE_CONF\manojz\INSTALL_S260_MANOJZ.bat
```

Gates on the four from-pins · writes `machine.conf` from the live files · backs up
as `.bak_S260_<from8>` · installs and re-hashes · walks it, including **taking the
settings file away to prove the fallback** and running the real stock push with
the S259 switch thrown so it parses and sends nothing · restores on failure ·
idempotent, and `--check` reports without changing anything.

## What this unblocks

**3g** — moving the manojz live tools into `D:\Downloads\margsync\bin\`: the
paths they need are no longer written inside them. **3i** — keeping full mobile
numbers out of the Drive mirror, which needs the mirror root named in one place.
And the medical PC's own two settings, once the S259 delivery has landed there.
