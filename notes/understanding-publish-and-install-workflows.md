# Understanding kinnoo-lock.yaml: Locking and Updating Agent Versions

This note explains how kinnoo's lockfile (kinnoo-lock.yaml) works, how it "locks" agent versions for reproducible installs, and how to update it when you want to move to a new stable version.

---

## 1. What is kinnoo-lock.yaml and how does it “lock” versions?

- When you run `kinnoo install`, it creates (or updates) `kinnoo-lock.yaml` in your project directory.
- This lockfile records the exact versions, hashes, and sources of all installed agents and their dependencies.
- It ensures that future installs (with the `--frozen` flag) will install the exact same agent versions and artifact hashes, guaranteeing reproducibility.

### How does it “lock”?
- If you run `kinnoo install --frozen`, the installer will only install the agents/versions/hashes listed in `kinnoo-lock.yaml`.
- If the lockfile is missing, out of date, or if the install would cause “lock drift” (i.e., a different version or hash than what’s in the lockfile), the install fails.
- This prevents accidental upgrades or changes—installs are “locked” to what’s in the lockfile.

---

## 2. How do you update kinnoo-lock.yaml to allow a new stable version?

- To update to a new version, you must explicitly run `kinnoo install <agent>@<new_version>` (or similar).
- This will fetch and install the new version, and update `kinnoo-lock.yaml` to reflect the new version and hash.
- After updating, future installs with `--frozen` will use the new locked version.

### Typical workflow:
1. Initial install (creates lockfile):
   ```
   kinnoo install myagent@1.2.3
   ```
   → `kinnoo-lock.yaml` records myagent@1.2.3 and its hash.

2. Reproducible install (in CI, production, etc.):
   ```
   kinnoo install --frozen
   ```
   → Only installs what’s in `kinnoo-lock.yaml`; fails if anything would change.

3. Upgrade to a new version:
   ```
   kinnoo install myagent@1.2.4
   ```
   → Installs new version, updates `kinnoo-lock.yaml`.

4. Lock to new version:
   ```
   kinnoo install --frozen
   ```
   → Now installs myagent@1.2.4 as locked in the updated lockfile.

---

## 3. Summary Table

| Command                        | Effect on kinnoo-lock.yaml         | Use case                        |
|--------------------------------|------------------------------------|---------------------------------|
| kinnoo install <agent>@<ver>    | Installs and updates lockfile      | Add/upgrade agent version       |
| kinnoo install --frozen         | Installs only locked versions      | Reproducible, locked installs   |
| kinnoo install                  | Installs latest, updates lockfile  | Unlocked, may upgrade           |

---

## 4. Best Practices

- Use `kinnoo install --frozen` in CI, production, or any environment where you want guaranteed reproducibility.
- To upgrade, run `kinnoo install <agent>@<new_version>` (or `kinnoo update`), then commit the updated `kinnoo-lock.yaml`.
- Never edit `kinnoo-lock.yaml` by hand—always let kinnoo manage it.

---

Let me know if you want to see a sample kinnoo-lock.yaml or a diagram of the workflow!
