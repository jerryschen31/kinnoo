# Test714 Test-Agent Handoff

- Implement integration test proving legacy password/session/reset paths are disabled by default after cutover.
- Ensure protected routes do not silently fallback to legacy auth paths.
- Suggested markers: `regression_integration`, `server_api`, `security_checks`.
