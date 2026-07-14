import Link from "next/link";
import { type Metadata } from "next";
import {
  BookOpen,
  CheckCircle2,
  ChevronRight,
  Clock,
  Download,
  Sparkles,
  Tag,
  Zap,
} from "lucide-react";
import { SeoSubpageShell } from "@/components/seo-subpage-shell";
import { absoluteUrl, buildPageMetadata } from "@/lib/seo";

const releases = [
  {
    version: "v0.14.0-beta",
    date: "2026-07-13",
    type: "beta",
    highlights: [
      "Configurable modifier+key hotkeys: set custom shortcuts with any combination of Ctrl, Alt, Shift, and Super plus a letter/number key, e.g. Alt+R or Ctrl+Shift+V (PR #493)",
      "Remote API engine now supports FunASR/SenseVoice models via OpenAI-compatible endpoints; SenseVoice metadata labels are stripped before text injection (PR #468)",
      "GNOME Wayland IBus text injection restored when only a bare xkb engine is configured; engine restore fallback now picks the correct IM engine (PR #506, #500)",
      "KDE Plasma Wayland IBus text-injection path restored after recent compositor-detection regressions (PR #502)",
      "Wayland text injection now waits for held modifiers to release before typing, preventing accidental shortcut triggers and garbled output (PR #494)",
      "whisper.cpp no longer defaults to all CPU cores on hybrid processors, improving UI responsiveness and battery life (PR #492)",
      "Fixed a crash on recording start when the selected audio device index no longer matches the current system enumeration (PR #499)",
      "Installer includes xsel as a fallback for the Wayland clipboard path when xclip is unavailable (PR #496)",
      "Removed an outdated long comment about whisper.cpp default thread counts (PR #505)",
    ],
  },
  {
    version: "v0.13.0-beta",
    date: "2026-06-30",
    type: "beta",
    highlights: [
      "Guided whisper.cpp model selection: pick a size plus a specialization (English-only, quantized Q5/Q8, or Large v3 Turbo) through split Model Size and Specialization dropdowns with in-app guidance; the --model flag also accepts exact IDs like medium.en-q5_0 and large-v3-turbo (PR #465)",
      "Dictation now keeps a space between segments spoken with a pause in between, so words no longer run together after a silence (PR #464)",
      "Keyboard shortcuts now work on keyboards hotplugged after Vocalinux starts, with the evdev backend rescanning for new devices and recovering from disconnects (PR #467)",
      "Vocalinux now detects KDE Plasma Wayland sessions and points you to enable IBus Wayland for reliable text injection, surfaced during install and when wtype injection fails (PR #466)",
      "Wayland: fixed garbled text on non-US keyboard layouts (AZERTY/QWERTZ/Dvorak) and a clipboard-copy hang; ydotool now pastes through the clipboard, which is layout-independent (PR #480)",
      "Wayland: use wtype/ydotool instead of IBus on compositors that don't bridge it to native apps like COSMIC, Sway, and Hyprland, fixing silent text drops (PR #486)",
      "Wayland/IBus: require a real IM engine before using IBus, so a bare xkb layout no longer causes silent text drops on GNOME/Mutter and other compositors (#478)",
      "Wayland: keep the keyboard layout intact by not running setxkbmap, which was flipping XWayland apps to us after dictation (#474)",
      "Faster ydotool text injection via an explicit --key-delay (PR #488)",
      "Settings dialog height capped on high-resolution displays (PR #465)",
      "Refreshed website docs with new feature pages for Remote API, Silero VAD, advanced whisper.cpp settings, and desktop reliability, plus responsive layout polish (PR #470)",
    ],
  },
  {
    version: "v0.12.0-beta",
    date: "2026-06-07",
    type: "beta",
    highlights: [
      "Remote API speech recognition engine with installation and configuration support (PR #335)",
      "Silero VAD drops silence-only buffers for cleaner dictation when ONNX Runtime support is available (PR #447)",
      "Thread safety hardening for Remote API, IBus, and text injection paths (PR #452)",
      "IBus preserves user engines for dead keys and captures the current engine during scoped activation (PR #457, #458)",
      "Remote Server settings now respect the Advanced toggle and the settings dialog fits lower-resolution screens (PR #454, #456)",
      "CUDA diagnostics now include auto-remediation and behavioral tests (PR #451)",
      "Corrected whisper.cpp and VOSK model download size metadata (PR #453)",
      "Startup now works without the pynput backend (PR #448)",
      "Remote API developer test server documentation (PR #455)",
      "Website speech demo browser support clarification (PR #449) and GitHub Sponsors funding configuration",
    ],
  },
  {
    version: "v0.11.0-beta",
    date: "2026-05-30",
    type: "beta",
    highlights: [
      "New Advanced Settings tab with whisper.cpp anti-hallucination parameters - temperature, no_speech_threshold, max segment length, and more (PR #415)",
      "IBus engine readiness probe at startup with hardened retries (PR #391)",
      "IBus runtime failure recovery without app restart (PR #411)",
      "IBus engine instance destruction handled on keyboard layout switch (fixes #388, closes #389)",
      "Preserve final speech on stop - no more truncated transcriptions (fixes #401)",
      "Play stop sound immediately on release and after audio thread joins (PR #426, #436)",
      "Repair pywhispercpp library loading in installer (PR #433)",
      "Reduce whisper.cpp CPU threads and ensure GPU backend builds in dev mode (PR #439)",
      "Correct openSUSE Tumbleweed dependencies with fallback handling (PR #418, #420)",
      "Harden Debian compatibility layer in installer (PR #437)",
      "Add Python 3.14 support and bump lxml>=6.1.0 (fixes #404)",
      "Validate pyproject.toml/setup.py content before entering local repo mode (fixes #396)",
      "Reuse existing whispercpp builds during install (PR #421)",
      "Refresh ldconfig after openSUSE typelib install, clarify python3XY placeholder convention (PR #438)",
      "Clean up runtime log noise and cache hardware detection",
      "Test coverage: recognition internals, IBus edge cases, CI notification suppression (PR #410, #414)",
      "Clarify PyPI installation requirements (PR #423)",
      "Dependency bumps: Next.js security updates (PR #399, #429), PostCSS",
    ],
  },
  {
    version: "v0.10.2-beta",
    date: "2026-04-08",
    type: "beta",
    highlights: [
      "Handle non-ASCII characters (á, é, ñ, etc.) with ydotool via clipboard paste fallback (fixes #362, PR #376)",
      "Detect IBus on Wayland without legacy env vars and fix text injection (PR #381)",
      "Start IBus engine process before checking registration to fix startup on some systems (fixes #360, PR #361)",
      "Add missing dependencies for Pop!_OS and Ubuntu 24.04+ including cmake, libcairo2-dev, libgirepository (PR #379)",
      "Systematic code quality refactor across 20 dimensions (PR #377)",
      "Clarify missing GNOME AppIndicator support on Debian (PR #385)",
      "Redesigned OG image for vocalinux.com - cleaner, professional, text-based layout (PR #392)",
      "Test coverage improvements: mock Notify module, tray degraded-startup, IBus socket-readiness branches (PR #384, #386, #390)",
    ],
  },
  {
    version: "v0.10.1-beta",
    date: "2026-03-30",
    type: "beta",
    highlights: [
      "Bundled package resources to prevent missing system tray icons (fixes #349, PR #354)",
      "Stopped recognition before engine switches to prevent segfaults (fixes #350, PR #355)",
      "Added a dedicated Close button in Settings for better WM compatibility (fixes #323, PR #356)",
      "Preserved XKB layout state during Vocalinux IBus activation (fixes #292, PR #343)",
      "Auto-recover speech recognition after system suspend/resume via new D-Bus handler (fixes #367, PR #369)",
      "Restart keyboard shortcut backend after resume to keep shortcuts working (PR #371)",
      "Delayed keyboard restart to allow USB re-enumeration after resume (PR #372)",
      "Fixed premature transcription during push-to-talk silence (fixes #358, PR #359)",
      "Disabled copy-to-clipboard by default in Settings (PR #370)",
      "Maintenance updates: npm/yarn dependency refresh and brace-expansion dev dependency bump (PR #346, #357)",
    ],
  },
  {
    version: "v0.10.0-beta",
    date: "2026-03-25",
    type: "beta",
    highlights: [
      "Generalized keyboard modifier alias matching across layouts for more reliable shortcuts",
      "Audio channel probing now validates device-supported sample rates before selection",
      "evdev now handles SYN_DROPPED to prevent stale modifier state",
      "IBus engine activation now uses register_component for stronger text-injection startup",
      "Settings dialog forces window decorations to prevent missing-titlebar behavior",
      "Tray icon refresh now uses icon names for better AppIndicator compatibility",
      "Coverage increased to 80%+ with additional IBus launch/main-entry tests",
      "Installer and CI polish: latest-tag fallback via GitHub API, Node 24 deploy, and path-filtered workflows",
    ],
  },
  {
    version: "v0.9.0-beta",
    date: "2026-03-14",
    type: "beta",
    highlights: [
      "Left/right modifier key distinction - choose Left Ctrl vs Right Ctrl for your shortcut",
      "Sound effects toggle - enable or disable audio feedback from Settings",
      "Wayland clipboard fallback - auto-copies text when virtual keyboard injection isn't available",
      "Display availability check - graceful error when running in headless environments",
      "Fixed unwanted leading space at the start of each new transcription session",
      "Fixed shortcut mode (toggle/push-to-talk) not applying on startup",
      "Improved Debian/pipx installation guidance and cross-distro error messages",
      "Grouped shortcut selector UI - shortcuts organised by Either/Left/Right side",
    ],
  },
  {
    version: "v0.8.0-beta",
    date: "2026-03-01",
    type: "beta",
    highlights: [
      "Push-to-talk shortcut mode (hold to speak, release to stop)",
      "Optional voice commands with VOSK auto-enable behavior",
      "Improved shortcut mode switching and callback reliability",
      "IBus active-method detection before text injection",
      "Audio hardware compatibility fixes (sample rate and channel count)",
      "Fedora startup dialog stability fix",
      "Web SEO expansion and homepage visual refresh",
    ],
  },
  {
    version: "v0.7.0-beta",
    date: "2026-02-22",
    type: "beta",
    highlights: [
      "Autostart on login support (XDG autostart)",
      "Tabbed settings dialog (Speech Engine, Recognition, Text Injection, Audio Feedback, General)",
      "Intel GPU compatibility detection - auto fallback to CPU for incompatible GPUs",
      "Single instance prevention - prevents multiple Vocalinux running",
      "Evdev device management - removes disconnected devices to prevent CPU spin",
      "Improved GPU detection - avoids false positives on systems without dev libraries",
      "IBus fallback - skip setup when daemon not running",
      "Fedora dnf check-update fix",
      "Web SEO - 7 new optimized pages",
    ],
  },
  {
    version: "v0.6.3-beta",
    date: "2026-02-19",
    type: "beta",
    highlights: [
      "Fixed installer default tag pointing to correct version",
      "Added missing psutil dependency for fresh installs",
      "Process check and interactive prompts in install/uninstall",
      "Removed leading space from first speech transcription",
    ],
  },
  {
    version: "v0.6.2-beta",
    date: "2026-02-18",
    type: "beta",
    highlights: [
      "Interactive backend selection (GPU/CPU)",
      "Enhanced welcome message",
      "Simplified install commands",
      "Better GPU support and Vulkan detection",
    ],
  },
  {
    version: "v0.6.0-beta",
    date: "2026-02-12",
    type: "beta",
    highlights: [
      "whisper.cpp as default engine",
      "Multi-language support with auto-detection",
      "System tray indicator",
      "Full Wayland support",
      "IBus text injection engine",
    ],
  },
  {
    version: "v0.5.0-beta",
    date: "2026-02-06",
    type: "beta",
    highlights: [
      "First beta release",
      "Stable core functionality",
      "Multiple speech engine support",
      "Improved text injection",
    ],
  },
  {
    version: "v0.4.1-alpha",
    date: "2026-01-29",
    type: "alpha",
    highlights: [
      "Language selector UI",
      "App drawer launch fix",
      "Better commit handling",
      "Improved update mechanism",
    ],
  },
  {
    version: "v0.4.0-alpha",
    date: "2026-01-29",
    type: "alpha",
    highlights: [
      "Multi-language support (French, German, Russian)",
      "Debian 13+ compatibility",
      "Python 3.12+ support",
      "Tag-based version selection in installer",
    ],
  },
  {
    version: "v0.3.0-alpha",
    date: "2026-01-21",
    type: "alpha",
    highlights: [
      "Initial public alpha",
      "Basic speech recognition",
      "X11 text injection",
      "VOSK engine support",
    ],
  },
];

const getTypeStyles = (type: string) => {
  switch (type) {
    case "stable":
      return {
        badge:
          "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400",
        label: "Stable",
      };
    case "beta":
      return {
        badge:
          "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400",
        label: "Beta",
      };
    case "alpha":
      return {
        badge:
          "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400",
        label: "Alpha",
      };
    default:
      return {
        badge: "bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-400",
        label: type,
      };
  }
};

export const metadata: Metadata = buildPageMetadata({
  title: "Vocalinux Changelog - Release History",
  description:
    "Track Vocalinux release history and version updates. See what's new in each version of our Linux voice dictation software.",
  path: "/changelog",
  keywords: [
    "vocalinux changelog",
    "vocalinux release notes",
    "voice dictation linux updates",
    "speech to text linux versions",
  ],
});

export default function ChangelogPage() {
  const articleJsonLd = {
    "@context": "https://schema.org",
    "@type": "Article",
    headline: "Vocalinux Changelog - Release History",
    description:
      "Complete release history for Vocalinux, the offline voice dictation software for Linux.",
    dateModified: "2026-06-30",
    author: {
      "@type": "Person",
      name: "Jatin K Malik",
      url: "https://github.com/jatinkrmalik",
    },
    publisher: {
      "@type": "Organization",
      name: "Vocalinux",
      logo: {
        "@type": "ImageObject",
        url: absoluteUrl("/vocalinux.png"),
      },
    },
    mainEntityOfPage: absoluteUrl("/changelog"),
  };

  return (
    <SeoSubpageShell>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(articleJsonLd) }}
      />

      <section>
        <p className="border-primary/30 bg-primary/10 mb-4 inline-flex items-center gap-2 rounded-full border px-4 py-1.5 text-sm font-medium text-primary">
          <Clock className="h-4 w-4" />
          Release History
        </p>
        <h1 className="mb-5 text-4xl font-bold tracking-tight sm:text-5xl md:text-6xl">
          Vocalinux Changelog
        </h1>
        <p className="mb-8 max-w-4xl text-lg text-muted-foreground">
          Track every release and see how Vocalinux has evolved. From initial
          alpha to stable releases, follow the journey of Linux voice dictation.
        </p>
      </section>

      <section className="space-y-6">
        {releases.map((release, index) => {
          const styles = getTypeStyles(release.type);
          return (
            <article
              key={release.version}
              className="rounded-2xl border border-zinc-200 bg-white p-6 dark:border-zinc-700 dark:bg-zinc-800"
            >
              <div className="mb-4 flex flex-wrap items-center gap-3">
                <div className="flex items-center gap-2">
                  <Tag className="h-5 w-5 text-primary" />
                  <span className="text-2xl font-bold">{release.version}</span>
                </div>
                <span
                  className={`rounded-full px-3 py-1 text-xs font-semibold ${styles.badge}`}
                >
                  {styles.label}
                </span>
                {index === 0 && (
                  <span className="bg-primary/10 rounded-full px-3 py-1 text-xs font-semibold text-primary">
                    Latest
                  </span>
                )}
                <span className="text-sm text-muted-foreground">
                  {release.date}
                </span>
              </div>

              <ul className="space-y-2">
                {release.highlights.map((highlight) => (
                  <li
                    key={highlight}
                    className="flex items-start gap-2 text-muted-foreground"
                  >
                    <CheckCircle2 className="mt-0.5 h-4 w-4 flex-shrink-0 text-green-500" />
                    {highlight}
                  </li>
                ))}
              </ul>

              {index === 0 && (
                <div className="mt-5 flex flex-wrap gap-3">
                  {[
                    { href: "/remote-api/", label: "Remote API guide" },
                    {
                      href: "/voice-activity-detection/",
                      label: "Silero VAD guide",
                    },
                    { href: "/advanced-settings/", label: "Advanced settings" },
                    {
                      href: "/desktop-reliability/",
                      label: "Reliability overview",
                    },
                  ].map((link) => (
                    <Link
                      key={link.href}
                      href={link.href}
                      className="border-primary/30 bg-primary/10 hover:bg-primary/15 inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-sm font-semibold text-primary"
                    >
                      {link.label}
                      <ChevronRight className="h-3.5 w-3.5" />
                    </Link>
                  ))}
                </div>
              )}

              <div className="mt-4 border-t border-zinc-100 pt-4 dark:border-zinc-700">
                <a
                  href={`https://github.com/jatinkrmalik/vocalinux/releases/tag/${release.version}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 text-sm font-medium text-primary hover:underline"
                >
                  <Download className="h-4 w-4" />
                  View release on GitHub
                  <ChevronRight className="h-4 w-4" />
                </a>
              </div>
            </article>
          );
        })}
      </section>

      <section className="mt-12 rounded-2xl border border-zinc-200 bg-zinc-50 p-8 dark:border-zinc-700 dark:bg-zinc-900/60">
        <h2 className="mb-4 text-2xl font-bold">Stay Updated</h2>
        <ul className="space-y-3 text-muted-foreground">
          <li className="flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-primary" />
            Watch the repository on GitHub for release notifications
          </li>
          <li className="flex items-center gap-2">
            <Zap className="h-4 w-4 text-primary" />
            Re-run the installer to update to the latest version
          </li>
          <li className="flex items-center gap-2">
            <BookOpen className="h-4 w-4 text-primary" />
            Check the{" "}
            <Link
              href="/install/"
              className="font-semibold text-primary hover:underline"
            >
              install guide
            </Link>{" "}
            for update instructions
          </li>
        </ul>
      </section>
    </SeoSubpageShell>
  );
}
