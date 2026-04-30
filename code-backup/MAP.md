# Backup map for in-place modified files

- original: /home/runner/work/kinnoo/kinnoo/FEATURES.txt
  backup: /home/runner/work/kinnoo/kinnoo/code-backup/FEATURES.txt
  reason: Added `visibility` field to every feature entry (Stage 0 first-pass classification)
  restore: cp /home/runner/work/kinnoo/kinnoo/code-backup/FEATURES.txt /home/runner/work/kinnoo/kinnoo/FEATURES.txt

- original: /home/runner/work/kinnoo/kinnoo/TASKS.txt
  backup: /home/runner/work/kinnoo/kinnoo/code-backup/TASKS.txt
  reason: Added `visibility` field to every task entry (Stage 0 first-pass classification)
  restore: cp /home/runner/work/kinnoo/kinnoo/code-backup/TASKS.txt /home/runner/work/kinnoo/kinnoo/TASKS.txt

- original: /home/runner/work/kinnoo/kinnoo/TESTS.txt
  backup: /home/runner/work/kinnoo/kinnoo/code-backup/TESTS.txt
  reason: Added `visibility` field to every test entry (Stage 0 first-pass classification)
  restore: cp /home/runner/work/kinnoo/kinnoo/code-backup/TESTS.txt /home/runner/work/kinnoo/kinnoo/TESTS.txt

- original: /home/runner/work/kinnoo/kinnoo/tests/client_cli_registry/test_registry.py
  backup: /home/runner/work/kinnoo/kinnoo/code-backup/tests/client_cli_registry/test_registry.py
  reason: Added requested `[agent]` note and updated imports/CLI invocation to support private CI dependency on public `kinnoo`
  restore: cp /home/runner/work/kinnoo/kinnoo/code-backup/tests/client_cli_registry/test_registry.py /home/runner/work/kinnoo/kinnoo/tests/client_cli_registry/test_registry.py

# Stage 4 note
# Additional in-place changes after Stage 5 documented above for private-CI dependency alignment.
