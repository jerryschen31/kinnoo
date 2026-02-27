# SWE Agent Handoff Brief: Task28 — kinnoo pack Unit & Integration Tests

## Overview
This handoff covers implementation of task28 for feature5: writing unit and integration tests for the kinnoo pack command. The goal is to ensure robust coverage of archive creation, error handling, file inclusion, manual extraction, and agent execution.

---

## Task Details

**Task ID:** task28  
**Feature:** feature5 — kinnoo pack — Agent packaging

### Steps
1. **Test kinnoo pack with valid agent directory**
    - Archive contains all required files (kinnoo.yaml, run.py, requirements.txt, manifest-listed files)
    - Wheel files for dependencies are present
    - No errors
2. **Test missing arguments, missing files, invalid manifest, and error cases**
    - Error handling: kinnoo pack fails gracefully, prints clear error, no archive created
3. **Test manual extraction of .kno archive**
    - Extract .kno archive using tar/gzip command-line tool (or Python tarfile)
    - Confirm requirements.txt, run.py, kinnoo.yaml, and other expected files are present in agent-dir
    - Throw error if any are missing
4. **Test end-to-end agent execution after manual extraction**
    - Run kinnoo run on extracted agent directory
    - Verify agent executes entrypoint and prints output

---

## Files to Modify/Create
- `tests/test_pack.py`

---

## Associated Tests
- **test46:** kinnoo pack unit tests cover positive cases
- **test47:** kinnoo pack unit tests cover negative/error cases
- **test48:** kinnoo pack integration tests cover manual extraction and run workflow
- **test50:** Manual extraction of .kno archive verifies required files

---

## Acceptance Criteria
- All tests pass, covering positive and negative cases
- Archive integrity and agent execution are verified without relying on kinnoo install

---

## Guidance for SWE Agents
- Use Python’s unittest or pytest framework
- For archive extraction, use subprocess to call tar/gzip or Python’s tarfile module
- Check file presence with os.path.exists or pathlib
- Simulate error cases (missing files, invalid manifest) and assert correct error handling
- For agent execution, use subprocess to run kinnoo run and capture output

---

## Troubleshooting Tips
- If you encounter issues with archive extraction, verify the .kno archive format and use standard tools
- For error handling, ensure all exceptions are caught and clear messages are printed
- If agent execution fails, check for missing files or incorrect manifest

---

## Contact
If you encounter blockers or need clarification, reach out to the TechLead Agent for guidance.
