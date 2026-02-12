# Vocalinux Release Process

This document outlines the step-by-step process for creating a new release of Vocalinux.

## Overview

Vocalinux uses [Semantic Versioning](https://semver.org/) with pre-release suffixes:
- **Alpha**: Early testing phase (e.g., `0.4.1-alpha`)
- **Beta**: Feature-complete, testing phase (e.g., `0.5.0-beta`)
- **RC** (Release Candidate): Final testing before stable (e.g., `0.5.0-rc1`)
- **Stable**: Production-ready (e.g., `1.0.0`)

## Quick Release Checklist

Use this checklist for every release:

```markdown
## Version Bump Checklist for X.Y.Z-PHASE

### Core Version Files
- [ ] `src/vocalinux/version.py` - Update `__version__` and `__version_info__`
- [ ] `pyproject.toml` - Update classifiers (Alpha→Beta→Stable)
- [ ] `setup.py` - Update classifiers

### Documentation
- [ ] `README.md` - Update badges, install commands, and announcements
- [ ] `docs/INSTALL.md` - Update version references in curl commands
- [ ] `docs/UPDATE.md` - Add "What's New" section for new version
- [ ] `SECURITY.md` - Update supported versions table

### Website
- [ ] `web/src/app/layout.tsx` - Update `softwareVersion` in schema
- [ ] `web/src/app/page.tsx` - Update version badge (e.g., "v0.5.0 Beta")
- [ ] `web/package.json` - Update version field

### Testing & Verification
- [ ] Run `make test` - All tests pass
- [ ] Run `make lint` - No linting errors
- [ ] Run `make typecheck` - No type errors
- [ ] Run `make build` - Package builds successfully

### Git Operations
- [ ] Create release branch: `git checkout -b release/vX.Y.Z-PHASE`
- [ ] Commit all version changes
- [ ] Push branch and create PR
- [ ] After PR merge, create tag: `git tag -a vX.Y.Z-PHASE -m "Release X.Y.Z-PHASE"`
- [ ] Push tag: `git push origin vX.Y.Z-PHASE`
```

## Detailed Release Steps

### Step 1: Determine Version Number

Follow semantic versioning:

```
Given version MAJOR.MINOR.PATCH-PHASE:

MAJOR - Breaking changes (for 1.0.0: public API stable)
MINOR - New features, backwards compatible
PATCH - Bug fixes, backwards compatible
PHASE - alpha, beta, rc1, rc2, etc. (omit for stable releases)
```

**Examples:**
- Alpha → Beta: `0.4.1-alpha` → `0.5.0-beta` (new features, phase change)
- Beta → RC: `0.5.0-beta` → `0.5.0-rc1` (same features, testing phase)
- RC → Stable: `0.5.0-rc1` → `1.0.0` (first stable release)
- Stable patch: `1.0.0` → `1.0.1` (bug fixes only)
- Stable minor: `1.0.0` → `1.1.0` (new features)

### Step 2: Update Core Version Files

#### 2.1 Update `src/vocalinux/version.py`

```python
__version__ = "0.5.0-beta"
__version_info__ = (0, 5, 0, "beta")
```

#### 2.2 Update `pyproject.toml`

Change the Development Status classifier:

```toml
# For Alpha:
"Development Status :: 3 - Alpha",

# For Beta:
"Development Status :: 4 - Beta",

# For Stable:
"Development Status :: 5 - Production/Stable",
```

### Step 3: Update Documentation

#### 3.1 Update `README.md`

**Status Badge (line ~6):**
```markdown
<!-- Alpha -->
[![Status: Alpha](https://img.shields.io/badge/Status-Alpha-orange)]

<!-- Beta -->
[![Status: Beta](https://img.shields.io/badge/Status-Beta-blue)]

<!-- Stable -->
[![Status: Stable](https://img.shields.io/badge/Status-Stable-brightgreen)]
```

**Install Commands:**
Update all curl commands to use the new tag:
```bash
curl -fsSL https://raw.githubusercontent.com/jatinkrmalik/vocalinux/v0.6.0-beta/install.sh | bash
```

**Release Announcement (lines ~31-34):**
```markdown
> 🎉 **Beta Release!**
>
> We're excited to share Vocalinux Beta with the community.
> This release is feature-complete and ready for broader testing.
```

#### 3.2 Update `docs/INSTALL.md`

Update all curl command examples with the new version tag.

#### 3.3 Update `docs/UPDATE.md`

Add a new "What's New" section at the top:

```markdown
## What's New in v0.5.0-beta

- Feature 1
- Feature 2
- Bug fix 1

See the [full changelog](https://github.com/jatinkrmalik/vocalinux/releases/tag/v0.5.0-beta).

---

## Previous Versions

### v0.4.1-alpha
...
```

#### 3.4 Update `SECURITY.md`

Update the supported versions table:

```markdown
| Version | Supported          |
| ------- | ------------------ |
| 0.5.x   | :white_check_mark: |
| 0.4.x   | :x:                |
| < 0.4   | :x:                |
```

### Step 4: Update Website

#### 4.1 Update `web/src/app/layout.tsx`

Update the schema.org softwareVersion (around line 123):

```typescript
"softwareVersion": "0.5.0-beta",
```

#### 4.2 Update `web/src/app/page.tsx`

Update the version badge in the header (around line 207):

```tsx
<span className="hidden sm:inline-block text-xs bg-gradient-to-r from-primary/20 to-green-500/20 text-primary border border-primary/30 px-2.5 py-1 rounded-full font-semibold shadow-sm shadow-primary/20">
  v0.5.0 Beta
</span>
```

Update the hero badge (around line 310):

```tsx
<span className="text-sm font-medium text-primary">
  Beta Release — Try it now!
</span>
```

#### 4.3 Update `web/package.json`

```json
{
  "name": "vocalinux-website",
  "version": "0.5.0"
}
```

### Step 5: Verify Everything Works

Run the full verification suite:

```bash
# Run tests
make test

# Run linting
make lint

# Run type checking
make typecheck

# Build package
make build

# Test install script (optional but recommended)
./install.sh --tag=v0.5.0-beta --dry-run 2>/dev/null || true
```

### Step 6: Create Release Branch and PR

```bash
# Create branch
git checkout -b release/v0.5.0-beta

# Stage all changes
git add -A

# Commit with conventional commit format
git commit -m "chore(release): prepare v0.5.0-beta

- Update version from 0.4.1-alpha to 0.5.0-beta
- Update status badges from Alpha to Beta
- Update documentation version references
- Update website schema and badges
- Update pyproject.toml classifiers
- Update SECURITY.md supported versions table"

# Push branch
git push origin release/v0.5.0-beta

# Create PR (use GitHub CLI or web interface)
gh pr create --title "chore(release): prepare v0.5.0-beta" \
  --body "This PR prepares the repository for the v0.5.0-beta release.

## Changes
- Bumped version to 0.5.0-beta
- Updated status badges from Alpha to Beta
- Updated all documentation version references
- Updated website version info
- Updated SECURITY.md supported versions

## Checklist
- [x] All tests passing
- [x] Linting clean
- [x] Type checking clean
- [x] Package builds successfully"
```

### Step 7: Create and Push Tag (After PR Merge)

Once the PR is merged to main:

```bash
# Checkout main
git checkout main
git pull origin main

# Create annotated tag
git tag -a v0.5.0-beta -m "Vocalinux Beta Release 0.5.0

Key changes since 0.4.1-alpha:
- Feature 1
- Feature 2
- Bug fix 1

Full changelog: https://github.com/jatinkrmalik/vocalinux/releases"

# Push tag
git push origin v0.5.0-beta
```

### Step 8: Monitor Release

After pushing the tag, the GitHub Actions workflow will automatically:

1. Build the Python package (wheel and sdist)
2. Create a GitHub Release with auto-generated notes
3. Publish to PyPI
4. Deploy the website to vocalinux.com
5. Mark as pre-release if version contains alpha/beta/rc

Monitor at: https://github.com/jatinkrmalik/vocalinux/actions

### Step 9: Post-Release Tasks

- [ ] Verify GitHub Release was created correctly
- [ ] Verify PyPI package was published (if applicable)
- [ ] Verify website was deployed (check vocalinux.com)
- [ ] Announce on social media/communities
- [ ] Update any pinned issues or discussions

## Emergency Hotfix Process

For critical bugs in a released version:

```bash
# Create hotfix branch from the tag
git checkout -b hotfix/v0.5.1-beta v0.5.0-beta

# Make fix, commit, push
git add -A
git commit -m "fix: critical bug description"
git push origin hotfix/v0.5.1-beta

# Create PR targeting main
# After merge, tag new version
git tag -a v0.5.1-beta -m "Hotfix release v0.5.1-beta"
git push origin v0.5.1-beta
```

## Version History

| Version | Date | Phase | Notes |
|---------|------|-------|-------|
| 0.2.0-alpha | 2024 | Alpha | Initial alpha |
| 0.3.0-alpha | 2024 | Alpha | - |
| 0.4.0-alpha | 2024 | Alpha | Multi-language support |
| 0.4.1-alpha | 2024 | Alpha | Language selector UI |
| 0.5.0-beta | 2025 | Beta | First beta release |

## Questions?

If you're unsure about any step:
1. Check previous releases for examples
2. Review the GitHub Actions workflows in `.github/workflows/`
3. Ask in the project's discussions

---

**Note**: This document should be updated when the release process changes.
