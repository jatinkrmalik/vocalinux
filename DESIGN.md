---
name: Vocalinux
description: Offline Linux voice dictation marketing site — workstation craft, not SaaS chrome
colors:
  ink: "#121916"
  paper: "#f1f4f2"
  paper-raised: "#ffffff"
  surface-muted: "#e4ebe6"
  primary: "#2f9a6a"
  primary-deep: "#1f6f4c"
  primary-soft: "#d8f0e4"
  terminal: "#0d1411"
  terminal-fg: "#8fdfb5"
  muted: "#4a5750"
  border: "#c8d4cc"
  dark-bg: "#0c1210"
  dark-raised: "#151c19"
  dark-muted: "#8a9a91"
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
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "#ffffff"
    rounded: "{rounded.md}"
    padding: "0.875rem 1.5rem"
  button-secondary:
    backgroundColor: "{colors.ink}"
    textColor: "#ffffff"
    rounded: "{rounded.md}"
    padding: "0.875rem 1.5rem"
  button-ghost:
    backgroundColor: "transparent"
    textColor: "{colors.ink}"
    rounded: "{rounded.md}"
    padding: "0.875rem 1.5rem"
---

# Design System: Vocalinux

## Overview

**Creative North Star: "The Linux desk utility"**

Hybrid of the deslop pass and closed PR #546 craft language: pure white / near-black iron surfaces, committed emerald, real app screenshots as proof, full-bleed install strip, asymmetric hero. Refuses generic AI SaaS (purple mesh, gradient text, icon-card grids, browser SpeechRecognition demos).

Marketing surfaces use **Persuade** mode: first viewport shows product + screenshot; conversion lives in the install strip; then desktop proof.

**Key Characteristics:**
- Pure white / zinc iron surfaces (not cream, not purple)
- Display (Bricolage Grotesque) + body (Source Sans 3); mono for install only
- Real `/public/screenshots/` in hero and feature bento
- Full-bleed dark install strip as primary conversion
- Spec rail + dense engine list instead of rainbow icon cards

## Colors

Committed emerald on pure iron neutrals (from PR #546 palette).

### Primary
- **Signal Green** (#2f9e5f light / #50c878 dark): buttons, focus, success marks, key links
- **Deep Canopy** (#1f6f4c): hover/pressed primary

### Neutral
- **Ink** (#09090b / #fafafa dark): primary text
- **Iron White** (#ffffff): page background (light)
- **Surface** (#f4f4f5 / #16161a): elevated panels
- **Muted** (#52525b / #a1a1aa): secondary text
- **Seam** (#e4e4e7 / #27272a): borders
- **Terminal Night** (#0a0a0c) / **Terminal Leaf** (#6ee7a8): install command surfaces

### Named Rules
**The One Signal Rule.** Emerald is the only chromatic accent. No purple, cyan glow pairs, multi-colored metric chips, or rainbow icon tiles.

**The Iron Surface Rule.** Backgrounds stay pure white or near-black iron. Never warm cream/beige as the tasteful default, and never purple-to-blue AI gradients.

## Typography

**Display Font:** Bricolage Grotesque  
**Body Font:** Source Sans 3  
**Mono:** system UI monospace stack for install commands only

**Character:** Display is slightly industrial and condensed enough to feel tool-like; body is clear and long-reading. No Geist/Inter as the whole-page face.

### Hierarchy
- **Display** (600, clamp 2.25–3.75rem, ~1.08 lh, -0.03em): hero only
- **Headline** (600, clamp 1.75–2.5rem): section titles
- **Title** (600, 1.125–1.25rem): card/row titles
- **Body** (400, ~17px, 1.65 lh, max ~70ch): paragraphs
- **Label** (600, 0.8125rem): nav, meta, short tags — sentence case preferred; short uppercase only in footer column heads if needed

### Named Rules
**The No Costume Mono Rule.** Monospace is for shell commands, paths, and config keys — not for marketing labels.

## Layout

- Content max width ~72rem; reading columns ~40–48rem for long prose
- Section vertical rhythm ~4–6rem; more space above a heading than below it
- Home first viewport: asymmetric when wide (offer + CTAs left, install terminal right); stacked on small screens
- Prefer definition lists / horizontal feature rows over 3×3 identical cards

## Elevation & Depth

Flat-by-default. Depth comes from surface tone (paper vs raised) and a single hairline border. Soft shadows only on the install terminal or primary elevated panel — never hairline + wide glow together (ghost card ban).

## Shapes

- Controls and panels: 6–14px radius (sm/md/lg)
- Cards never exceed ~14px radius
- Pills only for small status chips (version, default engine)

## Components

### Buttons
- Primary: solid signal green, white text, md radius, no scale-on-hover bounce
- Secondary: ink fill, white text
- Ghost: border seam, ink text
- Focus: 2px ring in primary

### Feature rows
- Icon optional, inline with title (no oversized icon tile stacked above heading)
- Border or surface change for hover; no side-tab accent borders

### Terminal panel
- Near-black surface, leaf green command text, copy control in the chrome bar
- Traffic-light dots optional but muted; not required decoration

### Navigation
- Sticky translucent paper bar with seam border; no heavy glassmorphism stack

## Do's and Don'ts

### Do:
- **Do** lead with install command and product proof (screenshots, demo labeled as browser preview)
- **Do** keep product claims accurate (offline local engines; remote only when configured)
- **Do** humanize marketing copy: short, specific, no "finally done right" swagger

### Don't:
- **Don't** use gradient text, animated mesh/orb backgrounds, or cyan+green dual glows
- **Don't** structure the page as repeated icon-in-rounded-square feature cards
- **Don't** put tracked uppercase eyebrows above every section
- **Don't** scatter identical fade-up motion on every block
- **Don't** invent metrics, testimonials, or "blazing" claims without product truth
