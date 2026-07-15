# AUR Packaging

Vocalinux can be installed on Arch Linux and derivatives via the Arch User Repository (AUR).

## For users

### Stable / beta releases (recommended)

```bash
yay -S vocalinux
# or
paru -S vocalinux
```

This installs the latest tagged release published by the project.

### Development / git snapshot

A community-maintained package tracks `main`:

```bash
yay -S vocalinux-git
```

`vocalinux` and `vocalinux-git` conflict with each other — install only one.

### After install

```bash
vocalinux
# or
systemctl --user enable --now vocalinux
```

On Wayland, keyboard shortcuts may require membership in the `input` group:

```bash
sudo usermod -aG input "$USER"
# log out and back in
```

---

## For maintainers (one-time AUR setup)

AUR publish is wired into the release pipeline (`.github/workflows/release.yml`). It only runs when the repository secrets below are configured.

### 1. Create an AUR account

1. Register at https://aur.archlinux.org/register
2. Confirm your email
3. Add an SSH public key under **My Account → SSH Public Key**

Generate a dedicated deploy key (do not reuse your personal GitHub key):

```bash
ssh-keygen -t ed25519 -C "vocalinux-aur-deploy" -f ./aur_vocalinux_ed25519 -N ""
```

- Upload `aur_vocalinux_ed25519.pub` to your AUR account
- Keep `aur_vocalinux_ed25519` private for the GitHub secret

Test SSH:

```bash
ssh -i ./aur_vocalinux_ed25519 aur@aur.archlinux.org
# Expected: "Interactive shell is disabled" / welcome message from AUR
```

### 2. Create the empty AUR package (first time only)

```bash
git clone ssh://aur@aur.archlinux.org/vocalinux.git
cd vocalinux
# Leave empty; the release workflow will push PKGBUILD + .SRCINFO
```

If clone fails with "not found", ensure you are logged into the AUR website at least once and your SSH key is attached to the account.

Optional: seed the package manually once with the files under `packaging/aur/vocalinux/`, then `makepkg --printsrcinfo > .SRCINFO`, commit, and `git push`.

### 3. Add GitHub repository secrets

In **Settings → Secrets and variables → Actions** for `jatinkrmalik/vocalinux`, add:

| Secret | Value |
|--------|--------|
| `AUR_SSH_PRIVATE_KEY` | Full contents of the private key file (`aur_vocalinux_ed25519`) |
| `AUR_USERNAME` | Your AUR username (used as git commit author) |
| `AUR_EMAIL` | Email associated with your AUR account |

If `AUR_SSH_PRIVATE_KEY` is missing, the release job **skips** AUR publish instead of failing the whole release.

### 4. What happens on each release

When you push a tag matching `v*` (for example `v0.14.0-beta`):

1. The existing release job builds wheels/sdists and creates the GitHub release
2. The **Publish to AUR** job:
   - Rewrites `pkgver` / `_tag` in `packaging/aur/vocalinux/PKGBUILD`
   - Refreshes checksums (`updpkgsums`)
   - Pushes `PKGBUILD`, `.SRCINFO`, `vocalinux.install`, and `vocalinux.service` to `aur.archlinux.org/vocalinux.git`

### 5. Local dry-run (optional)

On an Arch system with `pacman`/`makepkg`:

```bash
cd packaging/aur/vocalinux
# edit pkgver / _tag if needed
updpkgsums
makepkg --printsrcinfo > .SRCINFO
makepkg -s   # build package locally
```

### Relationship to `vocalinux-git`

| Package | Source | Maintainer | Use when |
|---------|--------|------------|----------|
| `vocalinux` | Latest GitHub release tag | Project (this repo) | Normal installs via `yay` |
| `vocalinux-git` | Live `main` branch | Community (`adrianlzt` et al.) | Bleeding-edge testing |

You can request co-maintainership of `vocalinux-git` on the AUR package page if you want the project listed there too. That package stays optional and is not updated by our release workflow.

### Troubleshooting

| Problem | Fix |
|---------|-----|
| `yay -S vocalinux` not found | Package not pushed yet — finish steps 1–3, then re-run a release or push once manually |
| AUR job skipped in CI | `AUR_SSH_PRIVATE_KEY` secret not set |
| Permission denied (publickey) | Wrong private key, or public key not added on AUR account |
| Checksum mismatch | Re-run release after fixing `_tag`; action runs `updpkgsums` automatically |
| Dependency missing (`python-pynput`, `python-pywhispercpp-cpu`) | Those live on the AUR; AUR helpers install them transitively |

## References

- [Arch wiki: AUR submission guidelines](https://wiki.archlinux.org/title/AUR_submission_guidelines)
- [Arch wiki: Creating packages](https://wiki.archlinux.org/title/Creating_packages)
- In-repo packaging: `packaging/aur/vocalinux/`
- Existing community git package: https://aur.archlinux.org/packages/vocalinux-git
