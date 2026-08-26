> ## WORKING PAPER — S203, not a reference
> Written to work something out on 26-Aug-2026. Its conclusions live in
> `MARG_MEDICAL_CURRENT.md`; its evidence and reasoning live in
> `MARG_MEDICAL_HISTORY.md`, both in `deploy_kits/MARG_MEDICAL/`.
> **Do not cite this as current.** Retained, not deleted (F-23).

# S203 — THE PROJECT KB WAS THE STALE STORE, NOT THE REPO

**26-Aug-2026.** Recorded because it inverts the assumption this whole consolidation
was built on, and because it caused a real error in a master reference the same day.

## What was assumed

That project knowledge held the current documents and the repo held copies — so the
preservation pass copied **project KB → repo**, and the consolidation read the Project
to decide what was true.

## What is actually the case

Two documents exist in both stores and **are not byte-identical**, and in both cases
**the repo copy is the better one**:

| document | project-KB copy | `KB_canon_S197fold/filed/` copy |
|---|---|---|
| `S195_Marg_dbf_Encryption_Finding.md` | un-annotated original | **carries the superseding pointer** |
| `S195_Email_Hardening_and_Marg_Guard_BuildState.md` | un-annotated original | **carries four outcome annotations** |

The lines present only in the repo copy of the encryption finding:

> *(S195 verdict superseded at the same session — see `S195_Marg_decrypt_partial_key.md`:
> the thorough attempt returned a decisive negative and remote decryption was RETIRED.
> This finding is retained for the characterisation and the debugger-route note.)*

**Those four lines are exactly the warning that would have prevented the error.** At S203
the master reference asserted that the Marg encryption was "genuinely breakable" and
"parked, not because it failed" — because the Project copy carries no such note and
`S195_Marg_decrypt_partial_key.md` **is not in project knowledge at all.** The annotation
had been written at the S197 fold, into the repo, and never travelled back.

## The rule this earns

**Neither store is authoritative by position.** The repo is not "a copy of the KB", and
project knowledge is not "the live set". When the same document exists in both, it must
be compared by **content, by md5 — never assumed current because of where it sits**
(D188, F-88). A fold that annotates a document in one store and not the other creates a
divergence that no check currently looks for.

**Concretely owed:** an inverse check at the close — for every document present in both
project knowledge and the repo, hash both and reconcile any difference, keeping the
superset. This is F-88's shape applied across stores rather than within one.

## What was done here

The `S203_MARG_CANON` copies of both documents were **replaced with the annotated repo
text** (the banner added earlier this session kept on top). The project-KB versions are
retained beside them as `*.from_projectkb_unannotated` — moved, never deleted.
