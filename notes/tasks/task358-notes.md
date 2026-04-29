# task358 notes

## Summary
- Added new `kinnoo uninstall <agent-name>` command wiring in `src/kinnoo/cli.py`.
- Implemented uninstall flow in `src/kinnoo/uninstall_command.py` with mandatory interactive confirmation.
- Uninstall now performs safe single-target directory removal from resolved install root.
- Added uninstall trace writer support in `src/kinnoo/install_trace.py`.
- Added regression test `tests/test_cli_install.py::test_feature74_uninstall_confirmation_and_removal`.

## Teaching Notes
- Destructive commands should require explicit confirmation by default; this keeps CLI behavior safe in interactive workflows.
- Keeping uninstall scoped to one agent name avoids accidental bulk deletes in early lifecycle phases.
- A dedicated uninstall trace event improves operational auditability without changing install-time trust behavior.

## Validation
- `python3 -m pytest tests --testmon -k test_feature74_uninstall_confirmation_and_removal`
