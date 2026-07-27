# Codeberg mirror setup

Vocalinux keeps **GitHub as the primary forge** for issues, pull requests, CI, and releases. A **read-only mirror** on [Codeberg](https://codeberg.org/) provides a second place to clone source if GitHub is unavailable.

This follows the redundancy plan discussed in [Discussion #434](https://github.com/jatinkrmalik/vocalinux/discussions/434).

## What syncs vs. what does not

| Synced to Codeberg | Stays on GitHub only |
|--------------------|----------------------|
| Branches, commits, tags | New issues and PRs (open on GitHub) |
| `README`, source tree, packaging | GitHub Actions runs and CI badges |
| `.github/workflows` files (as files) | Release binaries attached to GitHub Releases |
| Optional: one-time migration of issues/labels | GitHub Discussions, Pages deploy (`vocalinux.com`) |

## Important: Codeberg pull mirrors are disabled

Codeberg no longer offers **pull mirrors** from GitHub (automatic fetch from another host). See the [Codeberg FAQ](https://docs.codeberg.org/getting-started/faq/#why-cant-i-mirror-repositories-from-other-code-hosting-websites).

The practical approach for a GitHub-primary project:

1. **One-time migration** — create `codeberg.org/jatinkrmalik/vocalinux` with full git history (Step 1 below).
2. **Ongoing sync** — either enable the optional GitHub Action in this repo (Step 3) or push updates manually (Step 4).

## Step 1 — One-time migration (maintainer, ~5 minutes)

Do this once to create the mirror repository.

1. Sign in at [codeberg.org](https://codeberg.org/) (create an account if needed).
2. Click **+** (top right) → **New Migration**.
3. Select **GitHub**.
4. Fill in:
   - **Repository URL:** `https://github.com/jatinkrmalik/vocalinux`
   - **Access token:** a short-lived GitHub fine-grained PAT with read access to this repository (`Contents: Read-only` is enough for a public repo).
5. Migration options (recommended for a **read-only backup mirror**):
   - **Migrate repository data:** yes
   - **Mirror issues / PRs / wiki / releases:** optional (one-time snapshot only; new activity stays on GitHub)
   - **Repository name:** `vocalinux`
   - **Owner:** your user or a `vocalinux` organization if you create one
6. Click **Migrate Repository** and wait for completion.
7. On the new Codeberg repo → **Settings** → **Repository**:
   - Consider disabling **Issues** and **Pull Requests** so contributors know GitHub is canonical.
   - Add a short description, e.g. *Read-only mirror of https://github.com/jatinkrmalik/vocalinux*

**Delete the GitHub PAT** after migration succeeds.

Verify:

```bash
git ls-remote https://codeberg.org/jatinkrmalik/vocalinux.git HEAD
```

## Step 2 — Link the mirror in the repo (this documentation)

After Step 1, the mirror URL is listed in the root [README.md](../README.md) under **Repository mirrors**.

## Step 3 — Ongoing sync via GitHub Actions (recommended)

The workflow [`.github/workflows/codeberg-mirror.yml`](../.github/workflows/codeberg-mirror.yml) pushes `main` and tags to Codeberg whenever they change on GitHub. It is **inactive until you add a secret**.

### 3a. Create an SSH deploy key on Codeberg

1. On the Codeberg repo → **Settings** → **Deploy keys** → **Add deploy key**
2. Generate a new key pair locally (or use `ssh-keygen -t ed25519 -C "github-mirror-vocalinux" -f codeberg-mirror -N ""`)
3. Paste the **public** key into Codeberg; enable **Write access**
4. Store the **private** key securely

### 3b. Add the secret on GitHub

1. GitHub repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**
2. Name: `CODEBERG_MIRROR_SSH_KEY`
3. Value: entire private key file (including `-----BEGIN ...` / `-----END ...` lines)

The next push to `main` (or a manual **workflow_dispatch** run) will sync to Codeberg.

### 3c. Manual sync trigger

**Actions** → **Mirror to Codeberg** → **Run workflow**

## Step 4 — Manual sync (no Actions)

If you prefer not to use GitHub Actions:

```bash
git clone --mirror https://github.com/jatinkrmalik/vocalinux.git
cd vocalinux.git
git remote set-url --push origin git@codeberg.org:jatinkrmalik/vocalinux.git
git push --mirror
```

Re-run after large releases or when you want the mirror refreshed.

## Clone URLs

```bash
# Primary (contributions, issues, PRs)
git clone https://github.com/jatinkrmalik/vocalinux.git

# Read-only mirror (source backup)
git clone https://codeberg.org/jatinkrmalik/vocalinux.git
```

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Migration returns 500 / broken repo | Delete repo at `https://codeberg.org/.../vocalinux/settings` and retry migration |
| Action fails with "permission denied" | Deploy key on Codeberg must have **write** access; secret must be the matching private key |
| Mirror is behind `main` | Run the workflow manually or push with Step 4 |
| "Pull mirror" checkbox missing on Codeberg | Expected — use migration + push sync instead |

## Related links

- [Codeberg: Migrating repositories](https://docs.codeberg.org/advanced/migrating-repos/)
- [Discussion #434 — platform redundancy](https://github.com/jatinkrmalik/vocalinux/discussions/434)
