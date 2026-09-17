# S260 BUILD BRIEF — 15 → 17-Sep-2026 · the one document written for the owner

**What this session was for:** the project-knowledge cap, which you asked me to set right as the first
job. **What it became:** the discovery that the store with the cap was the only store holding 184 of
your documents — and the fix for that, the fix for the cap, and the split into two projects.

## What is different now

| before S260 | after S260 |
|---|---|
| project knowledge 92.6 % full; documents deleted mid-close to make room | **79.4 %**, measured; the cap is my routine at every session open, never yours |
| the manifest lived in two stores | one store — the repository; every session reads it from the clone (D528) |
| 184 documents existed only in project knowledge | **180 of them on your PC and hashed**, in `01_RESCUED_FROM_PROJECT_KNOWLEDGE\S260_RESCUE\` |
| one project, growing every close | **two projects** — "Sanjeevni — Pharmacy & Marg" created and its instructions pasted by you this morning; the parent keeps clinic core |
| custom instructions v9 | **v10** — pasted by you this morning |

## What I could not make byte-perfect, and said so

The 180 rescued copies were transcribed (project knowledge hands out text, not files). Ten were done
twice: nine identical to the byte, one had two paragraphs re-wrapped with every word intact. They are
backups, not replacements — nothing leaves project knowledge on their strength alone.

## Faults minted

F-501 (a canon swap is charged as an addition) · F-502 (a write that reported success and did nothing) ·
F-503 (the "cannot hash a project document" claim — untested and false) · **F-504 (the 184 only-copies)**
· F-505 (one canon file with two line endings; corrected).

## What needs you — nothing new

Both pastes are done. Your existing list stands, deferred at your word. One thing to know, not to do:
**your 17-Sep morning stock export had not reached the server or the archive by 06:00 IST** — the
Sanjeevni project's first session checks where it went.

## Next session — S261, in THIS project

The move: upload the 35 Sanjeevni documents into the new project, prove them there, then remove them
here. After that, everything pharmacy and Marg goes to the Sanjeevni project; everything else stays here.

## The publish

One file, when convenient:

```
D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat
```

It carries the Fault Register v2.84, Archive v1.97, Register v5.100, Runbook v181, START_HERE_261,
START_HERE_PROMPT_v10, this brief, the pin list, `MD5SUMS_ALL.txt` and `KIT_ID.txt`. Then, on the VPS,
so its clone carries the close:

```
git -C /root/deploy/repo fetch --depth 1 origin main && git -C /root/deploy/repo reset --hard origin/main
```
