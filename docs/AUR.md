# AUR

## Users

```bash
yay -S vocalinux          # latest release tag
yay -S vocalinux-git      # community package, tracks main
```

`vocalinux` and `vocalinux-git` conflict. Install only one.

## Maintainers (one-time)

Release tags auto-push `packaging/aur/vocalinux/PKGBUILD` when these secrets exist:

| Secret | Value |
|--------|--------|
| `AUR_SSH_PRIVATE_KEY` | Private key whose public half is on your AUR account |
| `AUR_USERNAME` | AUR username (git author) |
| `AUR_EMAIL` | AUR account email |

```bash
# 1. AUR account + SSH pubkey: https://aur.archlinux.org/register
ssh-keygen -t ed25519 -C "vocalinux-aur" -f ./aur_ed25519 -N ""
# upload aur_ed25519.pub on AUR; put aur_ed25519 in AUR_SSH_PRIVATE_KEY

# 2. Create empty package once
git clone ssh://aur@aur.archlinux.org/vocalinux.git

# 3. Next v* tag runs Publish to AUR (skipped if secret missing)
```

Sources: `packaging/aur/vocalinux/PKGBUILD`. Community git package: https://aur.archlinux.org/packages/vocalinux-git
