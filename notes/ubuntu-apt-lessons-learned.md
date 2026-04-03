# Lessons from Ubuntu APT's Security Model for Kinnoo

_Date: April 2, 2026_

This note analyzes the Ubuntu APT package security model (as explored in `temp.txt`) and evaluates which ideas kinnoo should adopt, adapt, or deliberately reject. The goal is to strengthen kinnoo's trust story without over-engineering the developer experience.

---

## 1. Summary of APT's Security Chain

The conversation in `temp.txt` walked through SQLite's journey from developer to end-user via Ubuntu's APT repositories. The key security stages are:

| Stage | Actor | Action | Mechanism |
|-------|-------|--------|-----------|
| Submission | Developer | Signs `.changes` manifest listing source files | Developer's GPG Private Key |
| Ingestion | Launchpad | Verifies developer signature, accepts source code | Developer's GPG Public Key (on file) |
| Building | Ubuntu build servers | Compiles source in isolated sandbox; generates NEW binary hash | Sbuild/Pbuilder (clean room) |
| Index signing | Ubuntu | Signs `InRelease` file (manifest of all package hashes) with Archive Master Key | Ubuntu Archive Master Private Key |
| Delivery | End-user's machine | Verifies `InRelease` signature using stored Public Key | Ubuntu Archive Master Public Key |
| Installation | End-user's machine | Downloads `.deb`, hashes it, compares to hash in verified `InRelease` | SHA-256 comparison |

The critical architectural insight is the **double-lock** pattern:
1. **Authenticity**: GPG signature on the index proves the index came from Ubuntu.
2. **Integrity**: SHA-256 hashes inside the verified index prove each package wasn't tampered with.

And the **trust consolidation** pattern: end-users trust ONE key (Ubuntu Archive Master Key), not thousands of individual developer keys. Ubuntu acts as a trusted intermediary.

---

## 2. How Kinnoo's Model Compares Today

### What kinnoo already does well

| APT Concept | Kinnoo Equivalent | Status |
|-------------|-------------------|--------|
| Package signing | Ed25519 signing via `kinnoo pack --sign` | Implemented (Feature40) |
| Hash verification at install | `.kno.sha256` sidecar + `verify_archive_checksum()` | Implemented |
| Signature verification at install | `verify_detached_signature_artifacts()` blocks invalid sigs | Implemented |
| Strict enforcement | `kinnoo install --strict` / `kinnoo publish --strict` | Implemented (Feature71) |
| Permission declarations | `permissions` field in `kinnoo.yaml` with install-time consent | Implemented (Feature39) |
| Runtime monitoring | Behavioral monitoring, violation logging, kill switch | Implemented (Feature41) |
| Audit trail | `install-trace.json`, `violation-events.jsonl`, `uninstall-trace.jsonl` | Implemented |
| Lockfile for reproducibility | `kinnoo-lock.yaml` with `archive_sha256` and `signature_fingerprint` | Implemented (Feature72) |

### What kinnoo is missing (gaps relative to APT)

| APT Concept | Kinnoo Gap | Severity |
|-------------|-----------|----------|
| **Signed index (InRelease)** | Registry index is unsigned; individual packages are signed but the index listing them is not | High |
| **Trust consolidation** | Each developer signs their own package; end-users must evaluate each developer's key independently | Medium |
| **Clean-room builds** | Developers build their own archives; no server-side rebuild from source | Low (see analysis below) |
| **Key distribution infrastructure** | No key server, no web-of-trust, no automatic key rotation | Medium |
| **Mirror integrity** | No mechanism to verify that a registry mirror hasn't been tampered with | Medium |

---

## 3. Critical Analysis: Where APT and Kinnoo Diverge

Before blindly copying APT, it's important to understand fundamental differences between the two ecosystems.

### 3.1 APT distributes compiled binaries; kinnoo distributes source+runtime bundles

APT's clean-room build step exists because C/C++ compilation can produce different binaries from the same source depending on the build environment, compiler flags, or injected backdoors. The "build barrier" (Ubuntu recompiles everything in a sandbox) closes the gap between "what the developer wrote" and "what the user runs."

**Kinnoo's situation is different.** A `.kno` archive contains Python/JS/TS source code, not compiled binaries. The end-user can inspect `run.py` directly. There's no compilation step that could silently inject malicious code. The source IS the artifact.

**Verdict:** A full clean-room rebuild is unnecessary and would be impractical for kinnoo (agent code often depends on API keys, external services, and framework-specific runtimes that can't be "built" in isolation). However, a lighter version — **server-side integrity checks** — could be valuable (see recommendations below).

### 3.2 APT has a single trusted authority; kinnoo is a community registry

Ubuntu has Canonical as a centralized trust authority. They employ maintainers, review packages, and sign everything with one master key. This works because Ubuntu is a curated distribution.

**Kinnoo is closer to npm or PyPI** — an open registry where any developer can publish. There is no central authority reviewing every agent before it goes live. Copying APT's "trust one key" model would mean kinnoo (the organization) would need to review and vouch for every published agent, which doesn't scale.

**Verdict:** Kinnoo should NOT try to become a gatekeeper like Canonical. Instead, it should provide tools for end-users to make informed trust decisions (verified publishers, security badges, reputation signals) — which is already the plan for Phase 9 (features 84-86).

### 3.3 APT's threat model centers on mirror tampering; kinnoo's centers on malicious agents

APT mostly trusts that its developers are legitimate (they go through a rigorous Debian/Ubuntu maintainer onboarding). The main threat is that a mirror server gets compromised and serves modified packages. Hence the focus on index signing and hash verification.

**Kinnoo's primary threat** is different: a bad actor publishes a malicious agent directly to the registry. The agent itself IS the threat, not the delivery channel. Kinnoo's existing defenses (permission declarations, security sweeps via `kinnoo check`, preflight checks, sandbox execution, runtime monitoring) are actually more relevant to this threat model than APT-style index signing.

**Verdict:** Kinnoo's per-agent security features (permissions, sandbox, monitoring) are MORE important than registry-level signing for the near term. APT doesn't need these because it trusts its developers implicitly. Kinnoo can't.

---

## 4. Recommendations: What Kinnoo Should Borrow

### 4.1 Registry Index Signing (HIGH priority, future)

**The idea:** Sign the registry index itself, not just individual packages. When a user runs `kinnoo search` or `kinnoo install <name>` and the CLI fetches the package list from the registry, that list should be signed by the registry's key.

**Why it matters:** Right now, if the kinnoo registry server is compromised, an attacker could:
- Modify the index to point users to malicious archives (even if each archive has its own signature, the attacker could substitute a legitimately-signed but different/older archive)
- Remove packages from the index (denial of service)
- Inject fake metadata (wrong descriptions, wrong version numbers)

**APT parallel:** The `InRelease` file is the signed index. Kinnoo would need an equivalent: a `registry-index.json` (or similar) that lists all packages with their versions and SHA-256 hashes, signed by the kinnoo registry key.

**Implementation sketch:**
1. Registry generates an index manifest listing every `(name, version, archive_sha256)` tuple.
2. Registry signs this index with a **Registry Signing Key** (Ed25519, consistent with existing kinnoo signing).
3. CLI downloads the signed index, verifies the signature using a **Registry Public Key** shipped with the kinnoo package (analogous to Ubuntu's `/usr/share/keyrings/`).
4. CLI compares downloaded archive hashes against the verified index.

**Complexity:** Medium. The main challenge is key rotation and distribution (what happens when the registry key needs to change?). APT handles this with key expiry dates and transition periods. Kinnoo could start with a simple approach: ship the registry public key in the `kinnoo` pip package itself, and rotate it with new kinnoo releases.

**When:** Post-launch (Phase 9+). The current per-package signing already protects against the most common attacks. Index signing adds protection against registry-level compromise, which is a lower-probability but higher-impact threat.

### 4.2 Publisher Identity Verification (MEDIUM priority, already planned)

**The idea:** APT's trust consolidation model (one key to rule them all) doesn't fit kinnoo, but a lighter version does: **verified publishers**. Link a developer's signing key to a verified identity (GitHub account, email) so that end-users can see "this agent was published by @jerry, whose identity is verified via GitHub OAuth."

**APT parallel:** Ubuntu verifies developer identity before accepting their GPG key into the Launchpad database. Kinnoo needs an equivalent, but lighter.

**Current plan:** Feature84 (GitHub OAuth) and Feature85 (verified publisher badges) already cover this. No changes needed to the plan, but this analysis confirms these features are important — they're the kinnoo equivalent of APT's developer verification step.

### 4.3 Embed Archive Hash in a Signed Manifest INSIDE the Archive (MEDIUM priority, future)

**The idea:** Currently, kinnoo's signature and checksum are **sidecar files** (`.kno.sig`, `.kno.sig.json`, `.kno.sha256`) that live alongside the archive. This is fine when archives are stored in a controlled registry, but becomes fragile when archives are shared via Slack, email, or a random URL — the sidecars can get lost or substituted.

**APT parallel:** The `InRelease` file bundles the signature WITH the hash list in a single file. The signature and data travel together.

**Recommendation:** Consider embedding a `KINNOO-INTEGRITY` file inside the `.kno` ZIP archive itself that contains:
- The SHA-256 of every file in the archive
- The publisher's public key fingerprint
- A timestamp
- An Ed25519 signature over all of the above

This way, integrity metadata travels WITH the archive and can't be separated from it. The external sidecars would remain for backward compatibility and registry use, but the embedded manifest adds defense-in-depth.

**Complexity:** Low-medium. Requires a change to the pack/install flow but no new cryptographic infrastructure.

**When:** Phase 8 or 9. Not urgent but would strengthen the trust story for out-of-registry distribution.

### 4.4 Checksum Verification Before Signature Verification (LOW priority, quick win)

**The idea:** APT's verification order is deliberate: verify the index signature first (cheap), then compare hashes (cheap), then only proceed to install. If either fails, abort immediately.

**Kinnoo's current flow** already does this correctly — `verify_detached_signature_artifacts()` checks `archive_sha256` before doing the cryptographic signature verification. This is already implemented well. No action needed.

### 4.5 Key Pinning and Rotation (LOW priority, future)

**The idea:** APT stores trusted keys on disk and refuses to install from repositories whose keys aren't pinned. If a key expires, `apt update` fails loudly until the user explicitly trusts a new key.

**Kinnoo could adopt a lighter version:** When a user installs from a verified publisher for the first time, pin that publisher's public key locally. On subsequent installs from the same publisher, verify that the key hasn't changed unexpectedly. If it has, warn the user ("Publisher key changed — this could indicate a compromised account").

**APT parallel:** First-use trust + key pinning + explicit rotation.

**Complexity:** Low. Store `{publisher_name: public_key_fingerprint}` in `~/.kinnoo/trusted-publishers.json`. Compare on each install.

**When:** Phase 9 (alongside Feature85 verified publisher badges).

---

## 5. What Kinnoo Should NOT Borrow

### 5.1 Clean-room builds

As discussed in section 3.1, kinnoo distributes source code, not compiled binaries. There's no compilation step that could inject hidden malicious behavior. A clean-room build would add significant infrastructure cost for minimal security benefit.

Additionally, AI agents are inherently harder to "rebuild" than traditional software: they often depend on API keys, model weights, configuration, and external services. A server-side rebuild would either fail (missing API keys) or produce a non-functional agent.

**Alternative already in place:** `kinnoo check` performs static security analysis on the agent source code, which is more appropriate for this ecosystem.

### 5.2 Centralized trust authority (single master key for all packages)

APT's "trust one key" model works for a curated distribution like Ubuntu. For an open registry like kinnoo, centralizing trust would either:
- Require kinnoo to manually review every published agent (doesn't scale), or
- Create a false sense of security (auto-signing everything with a master key adds no real trust signal)

**Alternative already in place:** Per-publisher signing + verified publisher badges (planned) + static security checks + permission declarations + sandbox execution.

### 5.3 GPG key infrastructure

GPG is powerful but notoriously bad for developer experience. Key management, key servers, web-of-trust, expiry, revocation — all of this adds friction for agent developers who just want to publish their work.

Kinnoo's choice of Ed25519 with simple PEM-encoded keys is the right call. It's simpler, faster, and sufficient for the threat model. If kinnoo ever needs keyless signing (tying signatures to identity providers rather than long-lived keys), the planned Sigstore migration (post-launch) is the modern answer — not GPG.

---

## 6. Priority Ranking

| Recommendation | Priority | Phase | Effort |
|---------------|----------|-------|--------|
| Registry index signing | High | Post-launch (Phase 9+) | Medium |
| Publisher identity verification | Medium | Phase 9 (Feature84-85, already planned) | Already scoped |
| Embedded integrity manifest in .kno | Medium | Phase 8-9 | Low-medium |
| Publisher key pinning | Low | Phase 9 | Low |
| Key rotation protocol | Low | Post-launch | Medium |

---

## 7. Summary

APT's security model is impressive for its domain (curated OS-level package distribution), but much of its complexity exists to solve problems kinnoo doesn't have (compiled binary trust, mirror network integrity, 50,000+ maintainer key management).

**What kinnoo should take away:**
1. **Signed index** — the registry itself should have a signed manifest, not just individual packages.
2. **Trust consolidation via verified publishers** — already planned, confirmed important.
3. **Embedded integrity data** — make the archive self-verifying, not dependent on sidecars.
4. **Key pinning** — defend against publisher account compromise.

**What kinnoo should keep doing differently:**
1. **Per-agent security** (permissions, sandbox, monitoring) matters MORE than delivery-channel security for an open registry.
2. **Ed25519 over GPG** — simpler, sufficient, better DX.
3. **Source distribution over binary distribution** — the user CAN inspect what they're installing, which is a trust advantage APT doesn't have.
4. **No centralized gatekeeper** — trust signals (badges, verification, reputation) rather than centralized review.

The overall takeaway: APT optimizes for "trust the channel, trust the authority." Kinnoo should optimize for "trust but verify the agent itself" — which is actually a stronger model for an open ecosystem where anyone can publish.

----

## My Response 1

Let’s dig a little deeper into these:Your Recommendation 1. Registry index signing (high priority, future) — biggest gap. If the registry is compromised, attackers could swap package listings even though individual archives are signed.

(My thoughts)
After a long conversation with a cybersecurity-expert agent, here is the suggested workflow:

1. I store a root private key on some local hardware device. The associated root public key is compiled directly into the kinnoo CLI so an end-user machine has machine access to the root public key since its compiled into the CLI, but no hacker would be able to isolate and potentially steal this root public key.

2. On the registry server, there is a “registry.json” that looks like this:{
  "signed": {
    "type": "root_delegation",
    "expires": "2027-04-03T12:00:00Z",
    "registry_public_key": "ed25519:abcd1234...", 
    "permissions": ["install", "publish", "search"]
  }
}

3. Every so often (let’s say every 6 months), I use my root private key to sign a SHA-256 hash of the “signed” block within registry.json, thereby encrypting that hash and creating a signature “f8e2a1c93b765…”.4. This signature is added to the JSON block, and we save a new “registry-auth.json” on the server that looks like this:
{
  "signed": {
    "type": "root_delegation",
    "expires": "2027-04-03T12:00:00Z",
    "registry_public_key": "ed25519:abcd1234...", 
    "permissions": ["install", "publish", "search"]
  },
  "signatures": [
    {
      "key_id": "my_root_key_id",
      "sig": "f8e2a1c93b765..." 
    }
  ]
}
OR we save a separate registry.json.sig that contains the signature. Question - is this a cleaner, simpler way to save the signature?5. Now when an end-user runs “kinnoo install <agent-package>”, the CLI will first download “registry-auth.json” (or registry.json and registry.json.sig, and then will use the root public key embedded within the kinnoo CLI (possibly ROOT_PUB_KEY in my private codebase, and ROOT_PUB_KEY value is on my local machine and used only when I compile the kinnoo CLI binary) to verify that the hash derived from the signature "f8e2a1c93b765..." matches the hash of the “signed” block in registry-auth.json. If it’s a match, then the registry_public_key that is in registry-auth.json (or registry.json if we go with registry.json.sig) is now “trusted” and the end user’s machine can then use this registry_public_key. (I assume this registry public / private key needs to be rotated every 90 days or so).6. On the server side, there is an up-to-date packages.json that lists every agent, every version, and the SHA-256 hash of every .kno file in the registry. Along side this packages.json, there is a packages.json.sig that is a SHA-256 hash of the packages.json file itself.7. A registry_private_key is used to encrypt packages.json.sig - this signature string is saved in a file packages.json.sig

8. The subsequent step of “kinnoo install <agent-package>” is to download the current packages.json (+packages.json.sig), use the trusted registry_public_key from registry-auth.json to then verify the hash derived from the signature within packages.json (which was signed by the registry_private_key) MATCHES the hash of packages.json.sig. If this is a match, then the end-user machine knows that the registry has not been tampered with, and proceeds to download the agent package.
9. The registry_private_key is stored within AWS KMS and there is a let’s say 90-day rotation period for the registry private/public key pair, upon which an updated registry.json (or registry-auth.json) would be created, and I would need to use my root private key to generate a new registry.json.sig signature.10. packages.json includes a timestamp field (that also serves as the version). This will help prevent “swapping” of an older packages.json by a hacker.

Your Recommendation 2. Embedded integrity manifest inside .kno (medium priority) — make archives self-verifying so sidecars can't get separated when shared outside the registry.
(My thoughts)
Regarding “Self-verifying”(suggested by another agent): There is a clever trick to this, because you can’t hash a file that contains its own hash (it creates a circular logic loop). The standard approach is
1. Hash the files: Calculate the SHA-256 for every file in the project (the code, the assets, the config).
2. Create the Manifest: Write those hashes into a file (e.g., integrity.json).
3. Pack it: Put the code AND the integrity.json into the .kno zip.
4. Verify: When kinnoo install is called, it opens the zip, looks at integrity.json, and re-hashes the files inside to see if they match the "proof" inside the manifest.
In this way, the integrity manifest is embedded in the archive.

Pro Tip: If you implement this, you should follow the JAR Manifest style. Put your hashes in a directory called META-INF/ inside your zip. It’s a decades-old standard that security auditors immediately recognize and respect.

Question: For kinnoo pack logic, should we have a way to exclude certain files from being hashed (e.g., they are “assets” that are too large), or should we hash the entire directory as one big block, or some other approach?
---

## Tech Lead Agent Response — Security Hardening Suggestions

_Date: April 3, 2026_

Great thinking here, Jerry. Your 10-step registry signing workflow is very close to what the industry calls **TUF (The Update Framework)** — which is the formal, peer-reviewed specification behind exactly this kind of root-key-delegates-to-registry-key-delegates-to-package pattern. The fact that you arrived at essentially the same architecture independently validates the design. Let me walk through each piece with grounded feedback based on our actual codebase state.

---

### On Your Registry Index Signing Workflow (Steps 1–10)

**Overall assessment: Architecturally sound.** The two-tier trust chain (root key → registry key → packages.json) is the right model. A few notes and refinements:

#### Step 1 — Root Public Key Embedded in CLI

This is correct and necessary. Today, no `ROOT_PUB_KEY` exists anywhere in the kinnoo codebase. When we implement this, it would live as a constant in something like `src/kinnoo/trust.py` or `src/kinnoo/constants.py`. The key point you raised — "no hacker would be able to isolate and potentially steal this root public key" — needs a small clarification: the root **public** key is inherently public; embedding it in the CLI binary is not about hiding it, it's about **pinning** it. The threat we're defending against is an attacker substituting a *different* root public key, not stealing ours. So the defense is: the binary ships with the correct key baked in, and no network request can override it. This is exactly how APT works (`/usr/share/keyrings/ubuntu-archive-keyring.gpg`).

**Implementation detail:** Since kinnoo is currently distributed as a pip package (not a compiled binary), the root public key would be a Python constant in the source. This is fine — pip packages are signed/verified by PyPI's own trust chain, so the delivery of the key itself is protected by PyPI's infrastructure. If we ever ship a standalone binary (via PyInstaller, Nuitka, etc.), the key gets compiled in automatically.

#### Steps 2–4 — registry-auth.json Structure

Your JSON structure is almost exactly TUF's `root.json` role. A few refinements:

**Answering your question: Separate `.sig` file vs. embedded signature?**

I recommend the **embedded signature format** (your `registry-auth.json` with the `"signatures"` array). Here's why:

1. **Atomicity** — One file download, one verification. No risk of the `.sig` getting separated from the data, no race condition where one file updates before the other.
2. **Multi-signature support** — The `"signatures"` array naturally supports multiple signers (e.g., if you ever want a co-signer or a transition period with both old and new keys). A separate `.sig` file would need to become `.sigs` or get awkward.
3. **TUF compatibility** — TUF uses exactly this pattern: `{"signed": {...}, "signatures": [...]}`. If we ever want to align with TUF tooling or claim TUF compliance, we're already structured correctly.
4. **Precedent** — Sigstore's Rekor transparency log, npm's `package-lock.json` integrity fields, and PEP 480 (Python's TUF proposal) all use embedded signatures over sidecars for metadata files.

The separate `.sig` file pattern is better suited for *content* files where you don't want to modify the original (which is why we use `.kno.sig` for archives — you can't embed a signature inside a ZIP without changing the ZIP). For JSON metadata that you control the schema of, embed the signatures.

#### Step 5 — CLI Verification Flow

Correct. One important addition: **cache the verified registry-auth.json locally** (e.g., `~/.kinnoo/cache/registry-auth.json`) with the expiry timestamp. The CLI should only re-download it if:
- The cached copy has expired
- The user forces a refresh (`--refresh-keys` or similar)
- No cached copy exists

This avoids hitting the server for the root delegation on every single `kinnoo install`. APT does the same thing — `apt update` refreshes the index, but `apt install` uses the cached verified index.

#### Steps 5–6 — Registry Key Rotation Period

**Your question: Should the registry key rotate every 90 days?**

90 days is reasonable for the registry key, but let me break this into two separate rotation schedules because they have different risk profiles:

| Key | Rotation Period | Reasoning |
|-----|----------------|-----------|
| **Root key** (your hardware device) | **Never** (or only if compromised) | This key is offline, never touches a network. Rotation means every CLI installation worldwide needs a new embedded key. Only rotate in an emergency. |
| **Registry signing key** (signs packages.json) | **180 days** (your 6-month suggestion) | This key lives on the server (ideally in AWS KMS as you noted). More exposure = more frequent rotation, but 90 days is unnecessarily aggressive for a KMS-managed key. 180 days is the sweet spot — aligns with your root delegation re-signing cadence. |

The reason I'd push back slightly on 90 days: each rotation requires you to manually re-sign `registry-auth.json` with your root private key (which is on a hardware device, presumably not always accessible). If the registry key rotates every 90 days, you're doing this ceremony 4 times a year. At 180 days, it's twice a year, which is manageable. AWS KMS rotation can happen more frequently for the actual underlying key material without changing the logical public key (KMS supports automatic key rotation that's transparent to callers).

#### Steps 6–8 — packages.json Signing

The flow is correct. One important design decision to flag:

**Do we need a full `packages.json` listing every agent, every version?** Today, `remote_client.py` uses per-package HTTP endpoints (`/api/agents/{tenant}/{name}/{version}/download`) — there is no global index endpoint. Introducing `packages.json` would be a new server-side feature that lists the entire registry catalog.

Two approaches:

1. **Full index** (`packages.json` lists everything) — Simpler trust model, but grows linearly with registry size. At 10,000 agents with 5 versions each = 50,000 entries. Could be several MB. APT's `Packages.gz` files are 20-40MB for large repos.
2. **Scoped index** (signed per-package metadata) — Each package gets its own signed metadata block. On `kinnoo install foo`, the CLI fetches `foo/metadata.json` (signed by registry key) which lists versions + hashes. Smaller downloads, but more complex.

**My recommendation:** Start with the **full index** approach (your `packages.json`). It's simpler, and kinnoo's registry will be small for a long time. We can compress it (`packages.json.gz`) and add scoped indexes later if scaling demands it. The signature covers the compressed file.

#### Step 9 — AWS KMS for Registry Private Key

Good choice. KMS means the private key never leaves AWS's HSM boundary — even your own server code never sees the raw key bytes. The signing operation happens inside KMS. This is materially stronger than a key stored as an environment variable or in a file on disk.

#### Step 10 — Timestamp / Version in packages.json

**Critical.** This prevents **rollback attacks** (serving a legitimately-signed but outdated index). The CLI should reject any `packages.json` whose timestamp is older than the previously-seen timestamp (stored locally in `~/.kinnoo/cache/`). This is exactly TUF's "snapshot" role.

Add a `"version"` integer that monotonically increases, in addition to the human-readable timestamp. Numeric comparison is simpler and less error-prone than timestamp parsing.

---

### On Your Embedded Integrity Manifest (Recommendation 2)

**Your understanding is exactly right.** The hash-the-files-then-embed-the-manifest approach is the standard technique, and you've described it correctly. Let me add some grounded details based on our actual pack flow:

#### Current .kno Archive Structure (from pack_command.py)

Today, `pack_agent()` writes files into the ZIP in this deterministic order:
1. `kinnoo.yaml` (always first)
2. Entrypoint (e.g., `run.py`)
3. `requirements.txt`
4. Additional files (from `additional_files` in kinnoo.yaml)
5. Asset files (from `assets/`)
6. State snapshot files
7. Node metadata files
8. OpenClaw files
9. Wheel files (`.whl`)

There is **no internal integrity manifest** today. Adding `META-INF/integrity.json` would slot in as the **last file written** to the ZIP (so all other files are already in place and hashable).

#### Proposed META-INF/integrity.json Structure

```json
{
  "schema_version": 1,
  "algorithm": "sha256",
  "created_at": "2026-04-03T12:00:00Z",
  "files": {
    "kinnoo.yaml": "a1b2c3d4...",
    "run.py": "e5f6a7b8...",
    "requirements.txt": "c9d0e1f2...",
    "assets/model.bin": "3a4b5c6d..."
  }
}
```

The `files` dict maps every file in the archive (except `META-INF/integrity.json` itself) to its SHA-256 hash. During `kinnoo install`, the CLI:
1. Opens the ZIP
2. Reads `META-INF/integrity.json`
3. For every other file in the ZIP, computes SHA-256 and compares to the manifest
4. If any mismatch → abort with a clear error
5. If any file exists in the ZIP but NOT in the manifest → abort (prevents file injection)
6. If any file exists in the manifest but NOT in the ZIP → abort (prevents file removal)

#### Answering Your Question: Should We Exclude Files from Hashing?

**No. Hash everything.** Here's my reasoning:

1. **No file is too large to hash.** SHA-256 is streaming — it processes data in chunks, so even a 2GB model weight file takes only a few seconds and ~constant memory. The bottleneck is disk I/O, not the hash computation. If a file is large enough that hashing it takes noticeable time, the user is already waiting for the ZIP extraction anyway.

2. **Exclusions create attack surface.** If `assets/model.bin` is excluded from hashing, an attacker can replace it with a malicious file and the integrity check won't catch it. Model weight files are actually a *high-value* target for supply chain attacks (model poisoning, backdoored weights).

3. **Exclusions add complexity.** You'd need an exclusion list, validation rules for what can be excluded, a way to communicate to the user what IS and ISN'T verified. All of this for zero security benefit.

4. **The JAR Manifest standard hashes everything.** Java's `META-INF/MANIFEST.MF` includes a digest for every file in the JAR with no exclusion mechanism. This is battle-tested across billions of deployments.

**One nuance:** The hash should be per-file, not "the entire directory as one big block." Per-file hashing lets you give precise error messages ("integrity check failed for `run.py`") rather than a generic "archive is corrupted." It also enables future features like partial verification or delta updates.

#### The META-INF/ Convention

Agree with the JAR-style `META-INF/` directory. It's immediately recognizable to security reviewers and auditors. Additional benefit: `META-INF/` sorts early alphabetically in the ZIP, making manual inspection easy with `unzip -l`.

One small addition: consider placing the **signature** inside the archive too as `META-INF/signature.json` (in addition to the external `.sig.json` sidecar). This would make the archive fully self-verifying even without sidecar files:
- `META-INF/integrity.json` — hashes of all content files
- `META-INF/signature.json` — Ed25519 signature over `integrity.json` + publisher public key fingerprint

The external sidecars (`.kno.sig`, `.kno.sig.json`, `.kno.sha256`) continue to exist for backward compatibility and registry use. The embedded versions add defense-in-depth for out-of-registry sharing.

---

### Summary of Answers to Your Specific Questions

| Question | Answer |
|----------|--------|
| Separate `.sig` file vs. embedded in `registry-auth.json`? | **Embed the signature** in the `{"signed": ..., "signatures": [...]}` structure. Atomic downloads, multi-sig support, TUF-aligned. |
| Registry key rotation — 90 days? | **180 days** for the registry signing key (aligned with root re-signing cadence). Root key: never rotate unless compromised. AWS KMS can rotate underlying material more frequently transparently. |
| Exclude files from integrity hashing? | **No — hash every file.** SHA-256 is cheap (streaming, constant memory). Exclusions create attack surface with no performance benefit. Per-file hashing gives precise error reporting. |

---

### Design Pattern Recognition: You've Reinvented TUF

I want to highlight something important for your interview prep: the architecture you've described across steps 1–10 is essentially **The Update Framework (TUF)**, which is a CNCF graduated project used by PyPI (PEP 458), Docker/Notary, and Sigstore. The key concepts map directly:

| Your Concept | TUF Role |
|-------------|----------|
| Root private key on hardware | `root` role (offline key) |
| registry-auth.json | `root.json` (key delegation) |
| registry_public_key delegation | `targets` key delegation |
| packages.json | `snapshot.json` + `targets.json` |
| packages.json timestamp/version | `timestamp.json` role |
| AWS KMS for registry key | Online key storage for `timestamp` and `snapshot` roles |

This is worth studying for AI Engineer interviews because **supply chain security** is increasingly relevant for AI/ML model distribution (model poisoning, dataset tampering). Frameworks like TUF, Sigstore, and SLSA (Supply-chain Levels for Software Artifacts) are becoming standard knowledge.

**Key resource:** https://theupdateframework.io/overview/ — the specification is readable and the Python reference implementation (`python-tuf`) is used by PyPI in production.

---

### Implementation Priority (Revised)

Based on your detailed design and our current codebase state, here's my revised implementation order:

| Order | Feature | Rationale |
|-------|---------|-----------|
| 1 | `META-INF/integrity.json` in `kinnoo pack` | **Do this first.** It's a contained change to `pack_command.py` (add hash computation + write `META-INF/integrity.json` as the last ZIP entry) and `install_command.py` (verify hashes on extract). No server-side changes, no key management, no new infrastructure. Immediate security value. |
| 2 | `META-INF/signature.json` embedded signing | Small extension of #1 — after computing integrity.json, sign it and embed the signature. Reuses existing `sign_payload()` from `signing.py`. |
| 3 | `root.json` + root key embedding | Requires: defining the root keypair, embedding the public key in the CLI, building the delegation JSON structure. Server-side work needed. |
| 4 | `targets.json` + signed index | Requires: new server-side endpoint to generate the index, integrating with AWS KMS for signing, CLI-side verification. Largest piece. |

This order gives us incremental security improvements at each step, with the simplest and most self-contained work first.

---

## Addendum: TUF Standard Alignment

_Date: April 3, 2026_

To reduce friction if we ever migrate to the `python-tuf` library and to make our design immediately recognizable to security auditors familiar with the TUF spec, the following three adjustments should be adopted.

### A1. Adopt TUF Role Terminology

Rename our metadata files to match TUF's standard role names:

| Our Current Name | TUF Standard Name | TUF Role |
|-----------------|-------------------|----------|
| `registry-auth.json` | `root.json` | Root — defines trusted keys and delegates authority |
| `packages.json` | `targets.json` | Targets — lists every package with its hash |

**Why this matters:** Anyone who has worked with TUF (PyPI maintainers, Docker/Notary users, Sigstore contributors) will instantly understand our trust architecture. It also means our JSON schemas can align with TUF's spec, so a future migration to `python-tuf` is a drop-in replacement rather than a rewrite.

The implementation priority table above has been updated to reflect this renaming.

### A2. Add Threshold Field for Multi-Signature Support

Even though kinnoo uses a single signing key today, the `root.json` delegation should include a `threshold` field from day one:

```json
{
  "signed": {
    "type": "root",
    "version": 1,
    "expires": "2027-04-03T12:00:00Z",
    "keys": {
      "abcd1234...": {
        "keytype": "ed25519",
        "keyval": {"public": "abcd1234..."}
      }
    },
    "roles": {
      "targets": {
        "key_ids": ["abcd1234..."],
        "threshold": 1
      }
    }
  },
  "signatures": [
    {
      "key_id": "root_key_id",
      "sig": "f8e2a1c93b765..."
    }
  ]
}
```

**Why add `threshold` now?** If we add it later, every existing CLI installation will be parsing a schema without `threshold` and will need a migration path to handle the new field. By including `threshold: 1` from the start:

- The CLI always checks `threshold` during verification — no code change needed when we eventually bump it to 2.
- If kinnoo brings on a co-maintainer or partner, changing `threshold` to 2 and adding a second key is a metadata-only change, not a CLI release.
- It's a single integer field — zero implementation cost today, avoids a breaking schema change later.

This is a textbook example of **forward-compatible schema design**: include optional/extensibility fields at v1 so v2 doesn't break existing clients.

### A3. Formalize Snapshot Consistency (Anti-Rollback)

TUF defines a dedicated `snapshot.json` role whose sole job is to record the version number and hash of `targets.json`. This prevents an attacker from serving a stale-but-legitimately-signed `targets.json` (rollback attack).

**Our simplified approach:** Instead of a separate `snapshot.json` file (which adds another download + verification step), we embed snapshot-like properties directly into `targets.json`:

```json
{
  "signed": {
    "type": "targets",
    "version": 42,
    "expires": "2026-10-03T12:00:00Z",
    "targets": {
      "myagent/1.0.0": {"sha256": "a1b2c3..."},
      "myagent/1.1.0": {"sha256": "d4e5f6..."}
    }
  },
  "signatures": [...]
}
```

The CLI enforces anti-rollback by:

1. Storing `last_seen_version` in `~/.kinnoo/cache/targets-meta.json` after every successful verification.
2. On each `kinnoo install` / `kinnoo search`, comparing the downloaded `targets.json` version against `last_seen_version`.
3. **Refusing to accept any `targets.json` with a version < `last_seen_version`.** This is a hard failure, not a warning.
4. The `expires` field provides a secondary defense: even if an attacker replays a current-version file, it will eventually expire and the CLI will reject it.

**Why not a full separate `snapshot.json`?** For kinnoo's scale (single registry, single targets file), the added complexity of a separate snapshot role doesn't pay for itself yet. The monotonic version + expiry embedded in `targets.json` provides the same rollback protection with one fewer network round-trip. If kinnoo ever needs multiple target delegation files (e.g., separate indexes per namespace), we can introduce `snapshot.json` at that point — and the version/expiry fields we're adding now will still be valid.

** Final note** (added by Jerry): If the versions are the same (105 == 105) but the SHA-256 hash of the file is different, the kinnoo CLI should also reject an install. That means someone modified the file without bumping the version number—a huge red flag for tampering!

### Updated File Naming in Implementation Priority

With the TUF role renaming, the implementation steps from the previous section become:

| Order | Feature | Files Involved |
|-------|---------|---------------|
| 1 | `META-INF/integrity.json` | `pack_command.py`, `install_command.py` |
| 2 | `META-INF/signature.json` | `signing.py`, `pack_command.py`, `install_command.py` |
| 3 | `root.json` + root key embedding | New `trust.py`, `constants.py`, server-side |
| 4 | `targets.json` + signed index | Server-side endpoint, `remote_client.py`, `install_command.py` |
