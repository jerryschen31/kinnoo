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
  reason: Added requested `[agent]` note documenting private/public test-separation refactor requirement
  restore: cp /home/runner/work/kinnoo/kinnoo/code-backup/tests/client_cli_registry/test_registry.py /home/runner/work/kinnoo/kinnoo/tests/client_cli_registry/test_registry.py

# Stage 4 note
# No additional in-place file modifications were required for Stage 3 worktree validation or Stage 5 runbook generation.
