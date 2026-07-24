# Web deslop notes (`fm/vlx-web-deslop`)

Local-only marketing site redesign against [impeccable slop](https://impeccable.style/slop/) and the installed impeccable skill. Base: `main` (not PR #546). No push / no PR until captain says otherwise.

## Direction

**Creative north star:** “Linux desk utility” — cool green paper, ink, one emerald signal color, terminal install as first-class proof. Persuade mode with craft restraint, not SaaS purple.

Artifacts: `PRODUCT.md`, `DESIGN.md` (repo root). Assumptions in PRODUCT.md labeled (unattended init).

## Detector

- `npx impeccable detect web/` (Node v20.19.4): source scan OK; found gradient-text on old hero before rewrite.
- URL scan against vocalinux.com failed (puppeteer not installed). Deferred.
- Post-edit: `detect.mjs` on changed landing files returned `[]`.

## Findings → fixes (home + shell)

| Slop / issue | Where | Status |
|---|---|---|
| Gradient text | Hero “Finally Done Right” | Fixed: solid ink headline |
| Animated mesh / cyan+green orbs | Hero background | Fixed: removed |
| Hero eyebrow / Sparkles pill | Beta badge | Fixed: single short kicker line |
| Overused Geist whole-page | layout | Fixed: Bricolage Grotesque + Source Sans 3 |
| Feature cardocalypse / icon tiles | Features grid | Fixed: editorial feature rows |
| Identical fade-up on every section | framer-motion + FadeInSection | Fixed: content static by default |
| Multi-color trust / engine icon rainbow | Hero + engines | Fixed: one signal green |
| Hype copy (“Finally Done Right”, “ditch your keyboard”, “real deal”) | Hero, CTA, live-demo | Fixed: humanized, product-true |
| Hairline + soft shadow ghost cards | Various | Fixed: border OR shadow on terminal only |
| Page bg zinc gradient | Home + seo-subpage-shell | Fixed: cool paper tokens |
| Sparkles icon as decoration | live-demo, engines | Fixed / reduced |
| Purple Whisper engine tile | Engines | Fixed: monochrome card system |

## Deferred (reason)

| Item | Reason |
|---|---|
| Full SEO subpage copy rewrite | Out of scope for landing-first pass; shell tokens inherit new system |
| Screenshot gallery polish | Real assets already; minor hover scale left |
| Remove framer-motion entirely | Still used by live-demo, theme-toggle, dictation-overlay |
| Live URL detector + puppeteer | Env missing puppeteer; captain can re-run after review |
| OG image / favicon rebrand | Keep existing product marks until design assets brief |
| Voca family section visual depth | Simplified cards; further craft optional |
| `.impeccable/design.json` sidecar | Optional tooling; DESIGN.md is source of truth |

## Ponytail notes

- Dropped unused `geist` and `react-intersection-observer` deps after home rewrite.
- Removed `FeatureCard` / `FadeInSection` wrappers; plain markup.
- Shared `TerminalBlock` + CSS button utilities instead of one-off motion shells.

## Review URL

Dev server (bind all interfaces, port 3456):

`http://127.0.0.1:3456`
