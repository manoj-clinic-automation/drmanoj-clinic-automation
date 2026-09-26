# S416_BUNDLE_ALLOWLIST — the five files the nightly code bundle never carried (F-631)

The S279 close found five live VPS files in no nightly bundle: `/root/portal/portal_sw.js`, `/root/portal/http_ece.py`,
`/etc/systemd/system/ring-hook.service`, `/root/wa/casepack/casepack_page.html`, `/root/wa/fu_push_on_arrival.sh`.
Read whole, `code_bundle.py` v1.7's source list explains four of them: root/portal carried no `*.js`; the unit patterns had no
`ring-*`; root/wa carried `*.py` only and never the `casepack/` sub-folder. **v1.8 adds four entries** after the old ones —
the S273/S318/S347 precedent: never an edit, so nothing carried today stops being carried — with the same name walls
(`users`, `secret`, `token`) and the same content scan afterwards.

**`http_ece.py` was already matched by v1.7** (root/portal `*.py`). Its absence from every bundle means it is not on the
box: the S366 installer copies it beside the portal only when pip cannot build the library, and the walk that night
passed with the library. The installer says on its face which of the five exist; the pin is corrected at the close.

**Proof.** `walk_s416.py` 13/13 on a mock root built from the kit's own copies of the five (byte-identical to the live
pins: 08807cdf · 76502193 · 8ed4b672 · ab728b08 · 9cc46b3b) plus seven decoys that must stay out (.env, a token file,
ring_hook.env, a .db and a secret_* page under casepack, users_sw.js, the conf): the live v1.7 leaves the four out, v1.8
carries all five, everything v1.7 carried is still carried, every decoy stays out, no content-scan hit. Then the real
`build` mode (no network) on the same mock root: a tarball with all five. On the box the installer runs `build` again
and reports how many of the five the local bundle now holds. `code_bundle.py` 8200dcca → 37a5a132. No restart.
