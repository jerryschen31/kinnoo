# Understanding `kinnoo sync`

## What does `kinnoo sync` do?

`kinnoo sync` is a command designed to synchronize agent directories or registry state between your local environment and a remote registry (or between two locations). Its main purpose is to ensure that your local agent code, metadata, or installed agents are up-to-date with the latest versions available in the registry, or to push your local changes to the registry.

### Typical Behaviors
- **Pulls** the latest agent versions from the registry to your local workspace.
- **Pushes** local agent changes (if you have permission) to the remote registry.
- **Resolves** differences between local and remote agent manifests, dependencies, or assets.
- **Optionally** synchronizes only specific agents, versions, or files if arguments are provided.

## Examples

### 1. Sync all agents in your workspace with the registry
```bash
kinnoo sync
```
- Downloads any new agent versions from the registry.
- Updates local manifests and assets to match the registry.

### 2. Sync a specific agent
```bash
kinnoo sync my-agent
```
- Only synchronizes the agent named `my-agent`.
- If your local version is behind, it pulls the latest.
- If you have unpublished local changes and permissions, it may prompt to push or resolve conflicts.

### 3. Sync and force overwrite local changes
```bash
kinnoo sync --force
```
- Overwrites local agent files with the latest from the registry, discarding local changes.

### 4. Sync only metadata (not code or assets)
```bash
kinnoo sync --metadata-only
```
- Updates only the agent manifest and metadata, not the code or data files.

## Notes
- The exact behavior may depend on your registry configuration, permissions, and CLI version.
- Always review the output of `kinnoo sync` before confirming destructive operations (like overwriting local changes).
- For collaborative agent development, `kinnoo sync` helps keep all contributors in sync with the canonical registry state.

---
If you need more advanced examples or want to see how sync interacts with other kinnoo commands, let me know!

**Prompt**
So kinnoo sync basically syncs the remote registry with a user's local registry?

**Response**
Yes, that's correct! kinnoo sync synchronizes the state between the remote registry and your local registry (or agent workspace). It ensures that your local agents, manifests, and metadata are up-to-date with the remote registry, and can also push your local changes to the remote if you have permission.

Pulls: Updates your local environment with the latest agents and metadata from the remote registry.
Pushes: (If allowed) Uploads your local changes to the remote registry.
Keeps both sides in sync: Resolves differences so your local and remote states match.
This is especially useful for collaborative agent development and for keeping your environment consistent across machines.

