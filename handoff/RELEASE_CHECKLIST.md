# Release Checklist

- [ ] DeepSeek or other worker inspected the handoff files and repository.
- [ ] The requested task was completed without broadening scope.
- [ ] No private, login-gated, or robots-disallowed source was accessed.
- [ ] No API key or secret appears in the diff, logs, or generated files.
- [ ] Database backup exists before any destructive migration.
- [ ] Duplicate and evidence impacts were reviewed.
- [ ] Relevant tests pass.
- [ ] `git diff --check` passes.
- [ ] Live `/api/health` returns HTTP 200.
- [ ] Live counts were compared with the expected local state.
- [ ] Independent reviewer returned PASS.
- [ ] Only after all checks: commit and deploy.
