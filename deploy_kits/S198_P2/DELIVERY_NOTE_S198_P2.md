# S198_P2 — Forms & Downloads (A3 of the Session-198 clubbed plan)

**One file: `portal.py` `dc093f1f83598b4e1927c2caee639fc7` → `2a162ec49bec4bf111a11dfb97e8d398`.**
No schema · no database · the files ARE the list.

## Owner rulings encoded

Portal-upload model: forms live at `/root/portal/forms/` on the box ONLY — never in the
PUBLIC repo (D320). Everyone logged in (doctor + manager + staff) can Open/Print and
Download; ONLY a proven doctor (the F-98 `_is_doctor` gate, same as the Gist) can add or
remove — upload on the page itself, so a new form never needs a publish or code change.

## Hard edges, proven not promised (gate 20/20 GREEN, runs again on the box pre-swap)

Name sanitiser: basename + charset allowlist + extension allowlist (pdf/png/jpg/docx/xlsx),
traversal = 404 by construction · staff POST to upload/delete = 403 · anonymous = redirect
to login, files included · duplicate name refused (original untouched) · disallowed
extension refused (nothing written) · byte-exact serve, inline for print, `?dl=1` for
download · URL-preservation: exactly ONE tile row changed vs the live baseline.

## Install (VPS)

```
cd /root/deploy/repo && git pull
bash deploy_kits/S198_P2/INSTALL_S198_P2.sh
```

Then open the tile and upload your forms (PDF prints best).
