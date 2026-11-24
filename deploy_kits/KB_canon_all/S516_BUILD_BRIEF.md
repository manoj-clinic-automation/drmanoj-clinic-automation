# S516 BUILD BRIEF — for Dr. Manoj (24-Nov-2026, evening)

**What changed today (session 516):**

1. **Every call is now kept on the server first (20:33).** The call hook, which hears every call from MyOperator, writes each call to a table on our own server, then to the Google Sheet exactly as before. If the server copy ever fails, the Sheet and the call are not affected.
2. **A nightly check at 23:40** compares the server's copy with the Sheet, row by row. Your health page has a new line, **call log table = sheet**: green after an equal night, red at once if they differ.
3. **Nothing on any screen changed** — not your Call Console, not the staff's.
4. **Checked twice before it went live** by reviewers who had not seen the work; nothing serious was found, and their smaller points were built in first.

**What waits on you:**

- One double-click to publish this session's records — nothing follows it on the server:

```
D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat
```

- Your one question from yesterday's brief still stands, when convenient: should a call missed after hours carry into the next morning's lists?
- Standing reminder: the packs page — the 25 card shops, and the card and ICICI passwords.

**Next session (517, Opus):** read tomorrow's checks (they confirm today's files and the first night's comparison) and the staff console's first full day. After three equal nights with calls, your Call Console starts reading the server's copy, which also makes it faster.
