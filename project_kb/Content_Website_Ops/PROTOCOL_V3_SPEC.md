# PROTOCOL_V3_SPEC — EOS system for project "Content_Website_Ops"
**For the executing Claude (Cowork session):** this document is your complete brief. It was authored in the Content & Website project chat (no disk access there), which is why you found no "protocol v3" anywhere — the term is defined HERE, now. Do not search for it further. Execute exactly this.

## 1. What Protocol v3 IS (context you lack)
End-of-session (EOS) closeout for the **Content_Website_Ops** Claude project, upgraded to use direct folder access:
- v1 = zip download + manual unzip + manual push (retired)
- v2 = zip download + EOS_RUN.bat one-click (today's bridge — the zip you'll find was produced this way)
- **v3 (you are implementing this):** the chat-side Claude produces a kit; the Cowork-side Claude (you) places it into the repo, maintains the project KB inside the repo, and stages cleanup. The user's ONLY manual act per EOS: one double-click on push_kit.bat (git execution stays human-triggered by design).

## 2. Authoritative answers to your open questions
- **"Protocol v3 document?"** — this file. Nothing else exists or is needed.
- **KB location (pinned):** `D:\dr-manoj-git\drmanoj-clinic-automation\project_kb\Content_Website_Ops\` — KB lives INSIDE the repo (versioned, rides existing 4-destination backup). The existing `END_OF_SESSION_PROMPT.md` / COLD_START_KIT files you found belong to OTHER projects' KBs — **do not modify anything outside `project_kb\Content_Website_Ops\`**. If `project_kb\` itself doesn't exist, create it.
- **Canonical session state (pinned):** Notion Clinic HQ session log (chat-side Claude appends at EOS) + this repo KB folder. No Claude-project-settings file swapping anymore.

## 3. Inputs you have
- `D:\Downloads\1 ROUGH WORKING FOLDER\KIT_2026-08-16_content_website_eos.zip` — **md5 must equal `b018ec0281e7ca233c1326dc443e6cd1`. Verify before use; STOP and report if mismatched.**
- This spec file, same folder.

## 4. Tasks (in order, full-file writes only — never partial edits)
1. Verify the kit zip md5 (§3).
2. Extract it. You get folder `KIT_2026-08-16_content_website_eos\`.
3. Move that folder to `D:\dr-manoj-git\drmanoj-clinic-automation\deploy_kits\KIT_2026-08-16_content_website_eos\` (create `deploy_kits\` if absent; if the kit folder already exists there, replace it wholly).
4. Create `D:\dr-manoj-git\drmanoj-clinic-automation\project_kb\Content_Website_Ops\` and write into it:
   a. `NEXT_SESSION_PROMPT.md` — copy from the kit root (it exists there), then append one line: "PROTOCOL v3 ACTIVE since 2026-08-16: KB lives here in-repo; EOS placement done by Cowork session; user action = one push_kit double-click."
   b. `SESSION_HANDOFF_2026-08-16.md` — copy from kit root.
   c. `KB_README.txt` — new, three lines: this folder is the canonical KB for the Content_Website_Ops Claude project; written only by that project's EOS runs; other projects must not write here.
5. Cleanup staging: move the kit zip and this spec file from `1 ROUGH WORKING FOLDER` into `D:\Downloads\_session_archive\Content_Website_Ops\2026-08-16\` (create path). Do NOT delete anything — move only.
6. Report back: md5 verified (value), files placed (tree of `deploy_kits\KIT_...` and `project_kb\Content_Website_Ops\`), archive done.
7. Tell the user their one remaining act: double-click `deploy_kits\KIT_2026-08-16_content_website_eos\scripts\push_kit.bat` (or push via GitHub Desktop).

## 5. Governance (inherited from the automation project — binding)
One writer per file · full-file replacements only · md5 verified before any extraction · never touch other projects' KB folders or any file outside the paths named above · no PHI is involved in this kit (verify nothing patient-identifiable slipped in; if found, STOP and report) · staff/financial data never enters the repo.

## 6. Standing pattern for FUTURE EOS runs (record this in your session notes)
Chat-side Claude produces `KIT_<date>_content_website_eos.zip` + updated `NEXT_SESSION_PROMPT.md` inside it → user downloads the single zip into `1 ROUGH WORKING FOLDER` → a Cowork task with folders `D:\dr-manoj-git` + the rough folder attached says "EOS placement per PROTOCOL_V3_SPEC" (this spec will live in the repo KB after step 4, at project_kb\Content_Website_Ops\ — copy this file there too as `PROTOCOL_V3_SPEC.md`, making future runs self-referencing) → you repeat §4 steps with the new kit → user double-clicks push.
