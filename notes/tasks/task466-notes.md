# Task466 - publish version history retention + latest version listing

## Summary
- Added regression coverage to verify publish keeps multiple versions for the same agent.
- Verified list and search surfaces show the latest version after multiple publishes.
- Confirmed both versioned registry artifacts remain retrievable.

## Files changed
- tests/test_cli_registry.py
- TASKS.txt

## Tests
- Command:
  - python3 -m pytest tests/test_cli_registry.py --testmon -k "test_publish_preserves_all_versions"
- Result:
  - 1 passed, 9 deselected

## Teaching notes
- A robust publish pipeline should preserve immutable version artifacts and compute a latest projection separately for discovery views.
- For integration tests around storage backends, asserting emitted target paths from command output makes tests resilient to backend root-layout differences.
