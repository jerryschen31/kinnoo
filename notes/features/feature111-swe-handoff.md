# Feature 111 — SWE Handoff: End-to-End Smoke Test Script

## Context
Create an automated smoke test that exercises the full kinnoo workflow against a deployed registry.

## Files to Create
- `scripts/e2e_smoke_test.py` (Python for consistency with the project)

## Test Workflow
The script runs these steps sequentially:
1. **Login**: `kinnoo login --email $TEST_EMAIL --password $TEST_PASSWORD --registry $REGISTRY_URL`
2. **Init**: `kinnoo init test-smoke-agent --framework generic` in a temp directory
3. **Pack**: `kinnoo pack test-smoke-agent`
4. **Publish**: `kinnoo publish test-smoke-agent --remote`
5. **Search**: `kinnoo search test-smoke-agent --remote` — verify it appears
6. **Install**: `kinnoo install test-smoke-agent --remote` in a different temp directory
7. **Run**: `kinnoo run test-smoke-agent "hello"` — verify output
8. **Logout**: `kinnoo logout`
9. **Cleanup**: Delete temp directories, unpublish test agent if possible

## CLI Interface
```bash
python scripts/e2e_smoke_test.py \
  --registry-url https://dev-api.kinnoo.ai \
  --email test@kinnoo.ai \
  --password "$TEST_PASSWORD"
```

## Output Format
```
[1/8] Login .................. PASS (0.5s)
[2/8] Init ................... PASS (0.2s)
[3/8] Pack ................... PASS (0.3s)
[4/8] Publish ................ PASS (1.2s)
[5/8] Search ................. PASS (0.4s)
[6/8] Install ................ PASS (1.5s)
[7/8] Run .................... PASS (0.8s)
[8/8] Logout ................. PASS (0.2s)

RESULT: 8/8 PASSED (5.1s total)
```

## Implementation Notes
- Use `subprocess.run()` to invoke kinnoo CLI commands
- Each step checks exit code + output for expected content
- Use temp directories for init/install to avoid conflicts
- Test agent should use `generic` framework (no API keys needed)
- The script should be idempotent — safe to run multiple times
- Exit code: 0 if all pass, 1 if any fail
- Consider: version-bump the test agent on each run to avoid name conflicts

## Testing
- Script runs against a local dev server successfully
- Each step reports PASS/FAIL correctly
- Cleanup removes temp directories

## Dependencies
- feature89 (server must have health endpoint for pre-check)
- feature101 (Dockerfile — smoketest may run in CI after deployment)

## Acceptance Criteria Summary
1. Script exercises full workflow: login → init → pack → publish → search → install → run → logout
2. Reports PASS/FAIL per step
3. Exit 0 on full pass, 1 on failure
4. Cleans up test artifacts
5. Runnable in CI
