# Product (vocalinux.com)

## Platform

web (Next.js marketing site under `web/`)

## Users

Linux desktop users who want voice dictation that stays on their machine: developers, writers, and people reducing keyboard strain. They already live in terminals, browsers, IDEs, and GTK/Qt apps.

## Product purpose

Vocalinux is free, open-source offline voice dictation for Linux. It turns speech into typed text in whatever app has focus, using local engines (whisper.cpp default, Whisper, VOSK) or an optional user-configured remote API. Success is: install once, dictate in any app, without cloud transcription or telemetry.

## Positioning

Offline-first Linux voice typing with real desktop integration (system tray, X11 and Wayland text injection, toggle and push-to-talk, Silero VAD, suspend recovery). A cloud SaaS voice product cannot truthfully claim local-only models plus no usage telemetry from the installed app.

## Operating context

- Install via a one-line shell installer, then run from PATH or app menu
- System tray indicator and settings GUI (GTK)
- Dictation into terminals, browsers, IDEs, office apps
- Engines and models chosen for hardware (CPU, optional Vulkan GPU)
- Guides and comparison pages on vocalinux.com; source on GitHub

## Capabilities and constraints

- Engines: whisper.cpp (default), OpenAI Whisper, VOSK, optional Remote API
- Display servers: X11 and Wayland
- Shortcut modes: toggle and push-to-talk; left/right modifier distinction
- Optional voice commands; Silero neural VAD with amplitude fallback
- No usage telemetry in the installed app
- GPL-3.0; marketing version string is tracked in site package/version surfaces
- Website is Next.js marketing + SEO guides (static export)

## Brand commitments

- Name: Vocalinux (also part of the "Voca" family with VocaMac / VocaWin)
- Mark: microphone logo assets under `public/`
- Emerald accent in the project green family (not purple SaaS defaults)
- Voice: practical, specific, Linux-native; not hype-first SaaS copy

## Evidence on hand

- Real app screenshots in `public/screenshots/`
- Install/uninstall commands pointing at GitHub raw install scripts
- JSON-LD on the home page (software application, FAQ, how-to)
- Do not invent user counts, testimonials, or benchmarks

## Product principles

1. Privacy is default: local engines process audio on-device; remote only when the user opts in.
2. Ship the install path and real desktop proof, not abstract feature theater.
3. Stay honest about engines, hardware, and what runs offline vs remote.
4. Prefer Linux craft and clarity over generic AI-startup marketing patterns.

## Accessibility

- Respect `prefers-reduced-motion`
- Body text contrast at least 4.5:1; large text at least 3:1
- Keyboard-reachable install copy controls and navigation
