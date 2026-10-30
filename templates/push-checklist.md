# Push checklist

What is this file? The list to tick before a push. The technical lead fills it after the customer approves. A push is not made while any line is open. The pre-push guard checks part of it.

## Push <version or task ID>
- [ ] Test flag: <off in the pushed commits>
- [ ] Version and changelog: <both updated; one line per item>
- [ ] Build and tests: <green; paste the summary line>
- [ ] Working tree status: <only files in scope changed>
- [ ] Document scan: <records current, no stale line>
- [ ] Secret scan: <no addresses, keys, tokens or personal data in files or commit messages>
- [ ] Co-author line: <present in the commit message>
- [ ] Model name: <stated correctly in the report>

Sources: [C-23, C-25, C-38, C-39, C-46, C-47]
