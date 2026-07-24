# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Linux desktop users who want voice dictation that stays on their machine: developers, writers, and people reducing keyboard strain. They already live in terminals, browsers, IDEs, and GTK/Qt apps.

## Product Purpose

Vocalinux is free, open-source offline voice dictation for Linux. It turns speech into typed text in whatever app has focus, using local engines (whisper.cpp default, Whisper, VOSK) or an optional user-configured remote API. Success is: install once, dictate in any app, without cloud transcription or telemetry.

## Positioning

Offline-first Linux voice typing with real desktop integration (system tray, X11 and Wayland text injection, toggle and push-to-talk, Silero VAD, suspend recovery). A neighboring SaaS voice product cannot truthfully claim local-only models plus no usage telemetry from the installed app.

## Operating Context

- Install via a one-line shell installer, then run from PATH or app menu
- System tray indicator and settings GUI (GTK)
- Dictation into terminals, browsers, IDEs, office apps
- Engines and models chosen for hardware (CPU, optional Vulkan GPU)
- Guides and comparison pages on vocalinux.com; source on GitHub

## Capabilities and Constraints

- Engines: whisper.cpp (default), OpenAI Whisper, VOSK, optional Remote API
- Display servers: X11 and Wayland
- Shortcut modes: toggle and push-to-talk; left/right modifier distinction
- Optional voice commands; Silero neural VAD with amplitude fallback
- No usage telemetry in the installed app
- GPL-3.0; current marketing version string in the site is v0.14.2
- Website is Next.js marketing + SEO guides under `web/`

## Brand Commitments

- Name: Vocalinux (also referenced as part of the "Voca" family with VocaMac / VocaWin)
- Existing mark: microphone logo assets under `web/public/`
- Green accent is historically associated with the project (#3CB371-range emerald); redesign may refine it but should stay in that family rather than purple SaaS defaults
- Voice: practical, specific, Linux-native; not hype-first SaaS copy

## Evidence on Hand

- Real app screenshots in `web/public/screenshots/`
- Interactive browser SpeechRecognition demo (preview only; product itself is offline after install)
- Install/uninstall commands pointing at GitHub raw install scripts
- JSON-LD software application, FAQ, and how-to on the home page
- No fabricated user counts, testimonials, or benchmarks unless sourced from the repo

## Product Principles

1. Privacy is default: local engines process audio on-device; remote only when the user opts in.
2. Ship the install path and real desktop proof, not abstract feature theater.
3. Stay honest about engines, hardware, and what runs offline vs remote.
4. Prefer Linux craft and clarity over generic AI-startup marketing patterns.

## Accessibility & Inclusion

- Prefer reduced-motion respect (site already gates animation via `prefers-reduced-motion`)
- Body text contrast at least 4.5:1; large text at least 3:1
- Keyboard-reachable install copy controls and navigation

## Assumptions (unattended init)

Inferred from repo + task brief without a live product interview. Label: not user-confirmed. Open: exact brand personality wording beyond "practical Linux tool"; whether Voca family should stay prominent on the home page (kept for product truth).
