# S306_BUNDLE_MASK

**One line on the VPS:**

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S306_BUNDLE_MASK/install_S306_BUNDLE_MASK.sh
```

## Why (F-518)

The server's nightly code backup (01:35, to Google Drive, then copied to the PC at 03:10) carried the two machine passwords written in the finance service's settings file. Its safety scan catches a password only when it is written in quotes; that file writes them without.

## What changes

`/root/state_backup/code_bundle.py` v1.3 → v1.4. In every service settings file the backup carries, a password-shaped setting keeps its name and its value is replaced with `MASKED_BY_CODE_BUNDLE`. The backup records the fingerprint (md5) of the original file, so it can still be checked against the Register, and it refuses to ship at all if a password value is still inside (exit 23 — the previous Drive copy stands).

**Not done here:** the two passwords are not changed. Copies made before tonight (Drive history, the PC's dated copies) still hold them; changing the passwords stays on the key-rotation list (F-456).

## Proof

- `test_s306.py` on the 17-Sep bundle's real tree: 22 checks — the masker on its own (quoted, unquoted, several on one line, comments and EnvironmentFile untouched, idempotent), a full build with neither value anywhere in the tarball, only the masked file differing from v1.3, v1.3 shown to carry the values, and the guard refusing (exit 23) with masking switched off. v1.3 as the new file fails it.
- The installer runs the same test **on the box**, over the live tree, before placing anything, then builds once from the placed file (no network) and requires the MASKED line.
