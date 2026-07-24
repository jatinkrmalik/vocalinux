---
name: Vocalinux website
description: Offline Linux voice dictation marketing site — workstation craft, not SaaS chrome
colors:
  ink: "#09090b"
  paper: "#ffffff"
  paper-raised: "#f4f4f5"
  surface-muted: "#f4f4f5"
  primary: "#1a7f4e"
  primary-deep: "#14663e"
  primary-soft: "#ecfdf3"
  terminal: "#0a0a0c"
  terminal-fg: "#6ee7a8"
  muted: "#52525b"
  border: "#e4e4e7"
  status-no: "#c45c5c"
  status-no-dark: "#e08b8b"
  dark-bg: "#0c0c0e"
  dark-raised: "#16161a"
  dark-muted: "#a1a1aa"
typography:
  display:
    fontFamily: "var(--font-display), ui-sans-serif, system-ui, sans-serif"
    fontSize: "clamp(2.25rem, 5vw, 3.75rem)"
    fontWeight: 600
    lineHeight: 1.08
    letterSpacing: "-0.03em"
  headline:
    fontFamily: "var(--font-display), ui-sans-serif, system-ui, sans-serif"
    fontSize: "clamp(1.75rem, 3vw, 2.5rem)"
    fontWeight: 600
    lineHeight: 1.15
    letterSpacing: "-0.025em"
  body:
    fontFamily: "var(--font-body), ui-sans-serif, system-ui, sans-serif"
    fontSize: "1.0625rem"
    fontWeight: 400
    lineHeight: 1.65
  label:
    fontFamily: "var(--font-body), ui-sans-serif, system-ui, sans-serif"
    fontSize: "0.8125rem"
    fontWeight: 600
    lineHeight: 1.4
    letterSpacing: "0.02em"
  mono:
    fontFamily: "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"
    fontSize: "0.875rem"
rounded:
  sm: "6px"
  md: "10px"
  lg: "14px"
spacing:
  section-y: "5rem"
  gutter: "1.5rem"
  content-max: "72rem"
---

# Design system: vocalinux.com

## Overview

**Creative north star: "The Linux desk utility"**

Pure white / near-black iron surfaces, committed emerald, real app screenshots as proof, full-bleed install strip, asymmetric home hero. Not generic AI SaaS (purple mesh, gradient text, icon-card grids, browser-fake demos).

Home is a persuade surface: first viewport shows product + screenshot; conversion lives in the install strip; then desktop proof. Child pages share the same shell and tokens via `SeoSubpageShell`.

**Key characteristics**
- Pure white / zinc iron surfaces (not cream, not purple)
- Display (Bricolage Grotesque) + body (Source Sans 3); mono for install only
- Real `public/screenshots/` on the home feature section
- Full-bleed dark install strip as primary conversion
- Feature rail + dense engine list instead of rainbow icon cards

## Colors

Committed emerald on pure iron neutrals.

### Primary
- **Signal green** (`#1a7f4e` light / `#50c878` dark): buttons, focus, success marks, key links
- **Deep canopy** (`#14663e`): hover/pressed primary

### Neutral
- **Ink** (`#09090b` / `#fafafa` dark): primary text
- **Iron white** (`#ffffff`): page background (light)
- **Surface** (`#f4f4f5` / `#16161a`): elevated panels
- **Muted** (`#52525b` / `#a1a1aa`): secondary text
- **Seam** (`#e4e4e7` / `#27272a`): borders
- **Terminal night** (`#0a0a0c`) / **Terminal leaf** (`#6ee7a8`): install command surfaces

### Status (comparison tables)
- **Yes:** primary emerald
- **No:** soft rose `#c45c5c` light / `#e08b8b` dark (distinct without form-error noise)

### Named rules
**The one signal rule.** Emerald is the only chromatic accent on marketing pages (except status-no rose on comparison marks). No purple, cyan glow pairs, multi-colored metric chips, or rainbow icon tiles.

**The iron surface rule.** Backgrounds stay pure white or near-black iron. Never warm cream/beige as the default, and never purple-to-blue gradients.

## Typography

**Display:** Bricolage Grotesque  
**Body:** Source Sans 3  
**Mono:** system UI monospace for install commands only

No Geist/Inter as the whole-page face.

### Hierarchy
- **Display** (600, clamp 2.25–3.75rem): home hero
- **Headline** (600, clamp 1.75–2.5rem): section titles
- **Title** (600, ~1.125rem): card/row titles
- **Body** (400, ~17px, 1.65 lh, max ~70ch)
- **Label** (600, ~0.8125rem): nav, meta; mono uppercase only for short kickers

### Named rules
**The no costume mono rule.** Monospace is for shell commands, paths, and config keys, not marketing labels.

## Layout

- Content max width ~72rem
- Section vertical rhythm ~4–6rem; more space above a heading than below it
- Home first viewport: asymmetric offer + screenshot when wide; stacked on small screens
- Install strip full-bleed dark band
- Features: settings shot paired with a stretched feature rail (matched heights)
- Child pages: breadcrumbs + content in `max-w-6xl`, shared shell chrome

## Elevation and shapes

Flat by default. Soft shadows only on terminal / primary elevated panels, not hairline + wide glow together.

- Panels and cards: 6–14px radius (use 12px as the common surface radius)
- Pills only for small controls (Install nav chip, default engine badge)

## Components

### Buttons
- Primary: solid signal green, white text, full-pill on marketing CTAs
- Secondary/ghost: border + background, no scale-bounce hover
- Focus: 2px ring in primary

### Feature rail
- Single bordered panel, divided rows, link affordance on the row
- No oversized icon tiles stacked above headings

### Terminal panel
- Near-black surface, leaf green command text, copy in chrome
- Long URLs wrap (`break-all` / `overflow-wrap`) so mobile never overflows

### Navigation
- Fixed translucent bar, seam border
- Home: simple links + Install pill
- Child: category dropdowns + Install pill + theme toggle

## Do's and don'ts

### Do
- Lead with install and real product proof (screenshots)
- Keep product claims accurate (offline local engines; remote only when configured)
- Keep marketing copy short and specific

### Don't
- Gradient text, animated mesh/orb backgrounds, or cyan+green dual glows
- Repeated icon-in-rounded-square feature cards as the page structure
- Tracked uppercase eyebrows on every section
- Scatter identical fade-up motion on every block
- Invent metrics, testimonials, or "blazing" claims
