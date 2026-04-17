# src/ History Public Release Checklist

Use this checklist before publishing `src/` and its git history.

## 1. Secret and Credential Safety

- [ ] Run history secret scan for `src/` (all revisions), not just current files.
- [ ] Confirm no hardcoded keys, tokens, passwords, private keys, or auth headers.
- [ ] Confirm no accidental `.env`, key material, or credential blobs were ever committed under `src/`.
- [ ] If any leak is found, rotate credentials first, then rewrite history before publishing.

## 2. Sensitive Information Disclosure

- [ ] Remove personal identifiers from code defaults and comments (names, usernames, machine-specific labels).
- [ ] Remove internal filesystem layout references that expose private structure beyond what is needed.
- [ ] Review defaults, examples, and docstrings for internal-only hostnames/paths.

## 3. Exploit-Resistance Baseline

- [ ] Validate archive extraction is path-safe (no zip-slip path traversal risk).
- [ ] Confirm no `subprocess(..., shell=True)` on untrusted input paths.
- [ ] Confirm no unsafe deserialization patterns (`pickle.loads` on untrusted data, unsafe YAML loading).
- [ ] Confirm runtime command execution paths enforce policy checks where intended.

## 4. Release Hygiene

- [ ] Run targeted security tests for install/fetch/archive code paths.
- [ ] Run representative CLI smoke tests for package, install, and fetch flows.
- [ ] Ensure docs accurately describe security behavior and limitations.
- [ ] Record audit date, scanner commands used, and sign-off owner.

## 5. Decision Gate: Keep History vs Fresh History

Use this rule before publication:

- Publish with history only if all are true:
  - [ ] No credential leaks in `src/` history.
  - [ ] No unresolved high/medium severity issues in current `src/`.
  - [ ] No sensitive internal identifiers that create avoidable disclosure risk.

- Otherwise publish with fresh history:
  - [ ] Create a clean export of current `src/` state.
  - [ ] Start public history from the sanitized baseline commit.

## 6. Recommended Commands

```bash
# Inspect src-only history volume

git rev-list --count --all -- src

# Look for common credential patterns in src history diffs

git log --all -p -- src | rg -n --pcre2 "AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{40,}|-----BEGIN (RSA|OPENSSH|EC|DSA|PGP) PRIVATE KEY-----|api[_-]?key\s*=|token\s*=|password\s*="

# Keep only src history in a temporary clone (requires git-filter-repo)

git filter-repo --path src/
```

## 7. Audit Record

- Audit date:
- Auditor:
- Scope:
- Tools/commands used:
- Findings summary:
- Publish decision:
