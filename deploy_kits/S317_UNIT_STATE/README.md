# S317_UNIT_STATE

**One line on the VPS:**

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S317_UNIT_STATE/install_S317_UNIT_STATE.sh
```

## What it does

Closes **F-496**. The nightly code bundle has carried the unit files since S243 and the root crontab
since S250, and between them they say **what each scheduled job would do**. Neither says **whether it
is switched on**. A `.timer` that was never enabled has no symlink in any `*.wants` directory, never
fires once in its life, and its unit file inside the bundle is byte-identical to a healthy one.
`gather()` skips symlinks on purpose, so no bundle in this estate's history has ever contained one.

The patch adds one generated member beside `crontab.txt`:

```
unit_state.txt
```

It carries two facts, and is explicit about where each comes from:

1. **the enable symlinks**, listed from disk (`*.wants` / `*.requires` under `/etc/systemd/system`),
   as `dir/link -> target`. This is filesystem truth: no link, not enabled, whatever the unit says.
2. **`systemctl is-enabled` and `is-active`** per carried unit — asked **only** when the bundle is
   being built against the real root. If `ROOT` is a copied tree the two columns read `not-asked`
   and the file says so in writing, because a bundle built from a copy must never report that
   copy's units as the live machine's.

Nothing reads a unit's **content** — `is-enabled` prints one word — so the S306/F-518 masking wall is
untouched. `BUNDLE_INFO.txt` gains `unit_state_captured=`.

## Proof

`selftest_s317.py` patches a **copy of the live file** and then builds **two whole bundles** against a
fake root — one with the change, one without — and compares them member by member: **26 checks**.
Among them: the only new member is `unit_state.txt`, nothing the old build carried was dropped, its
manifest row matches its bytes, the tarball still verifies against its own manifest, an enabled unit
reads `wants-link=yes` and a never-enabled one `wants-link=no`, a unit's `Environment=` **value**
never appears in the file, a non-zero `systemctl` exit is read rather than treated as a failure, and
a machine with no `systemctl` at all says `unavailable` instead of raising.

Two negative controls, each of which must turn a green check red: an unlistable unit directory
(becomes a note in the file, not a crash) and a manifest row removed for the new member (the
verifier must object).

A live-shape walk was run against the 18-Sep 01:35 bundle unpacked as a root: 251 files gathered,
20 units listed, bundle built and verified.

## What it does not need

`show_unit_state_s317.py` is read-only and **need not be run by anyone** — the installer prints its
table once, and from tonight the same table is in the bundle, which the PC nightly already copies.
