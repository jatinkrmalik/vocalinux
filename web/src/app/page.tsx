"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { LiveDemo } from "@/components/live-demo";
import {
  Terminal,
  Activity,
  Lock,
  Zap,
  Laptop,
  Keyboard,
  Settings,
  Github,
  Star,
  Download,
  ChevronRight,
  CheckCircle2,
  Menu,
  X,
  Copy,
  Check,
  Play,
  Shield,
  ShieldCheck,
  Server,
  Globe,
  Cpu,
  Volume2,
  Heart,
} from "lucide-react";
import { ThemeToggle } from "@/components/theme-toggle";
import { VocalinuxLogo } from "@/components/optimized-image";

// Always uses main/install.sh. The installer dynamically resolves the latest release tag via GitHub API
const installCommands = {
  interactiveInstallCommand: `curl -fsSL https://raw.githubusercontent.com/jatinkrmalik/vocalinux/main/install.sh -o /tmp/vl.sh && bash /tmp/vl.sh --interactive`,
  interactiveInstallDisplayCommand: `curl -fsSL \\
  https://raw.githubusercontent.com/jatinkrmalik/vocalinux/main/install.sh \\
  -o /tmp/vl.sh && \\
bash /tmp/vl.sh --interactive`,

  uninstallCommand: `curl -fsSL https://raw.githubusercontent.com/jatinkrmalik/vocalinux/main/uninstall.sh -o /tmp/vul.sh && bash /tmp/vul.sh`,
  uninstallDisplayCommand: `curl -fsSL \\
  https://raw.githubusercontent.com/jatinkrmalik/vocalinux/main/uninstall.sh \\
  -o /tmp/vul.sh && \\
bash /tmp/vul.sh`,
};

const homeJsonLd = [
  {
    "@context": "https://schema.org",
    "@type": "SoftwareApplication",
    "@id": "https://vocalinux.com/#softwareapplication",
    name: "Vocalinux",
    applicationCategory: "UtilitiesApplication",
    operatingSystem: "Linux",
    isAccessibleForFree: true,
    license: "https://github.com/jatinkrmalik/vocalinux/blob/main/LICENSE",
    offers: {
      "@type": "Offer",
      price: "0",
      priceCurrency: "USD",
    },
    description:
      "Offline voice dictation and speech-to-text for Linux with whisper.cpp and VOSK.",
    softwareVersion: "0.14.2",
    author: {
      "@type": "Person",
      name: "Jatin K Malik",
      url: "https://github.com/jatinkrmalik",
    },
    url: "https://vocalinux.com/",
    downloadUrl: "https://github.com/jatinkrmalik/vocalinux",
    screenshot: "https://vocalinux.com/og-image.png",
    featureList: [
      "100% offline speech recognition",
      "Remote API speech recognition for compatible self-hosted transcription servers",
      "Silero neural voice activity detection with amplitude fallback",
      "Works with X11 and Wayland",
      "Toggle and push-to-talk shortcut modes",
      "Left/right modifier key distinction for shortcuts",
      "Optional voice commands with VOSK-aware defaults",
      "Adaptive audio and IBus-aware text injection",
      "Clipboard fallback for unsupported Wayland compositors",
      "Sound effects toggle for audio feedback",
      "whisper.cpp, Whisper, VOSK, and Remote API support",
      "Advanced whisper.cpp anti-hallucination settings",
      "Auto-recover speech recognition after system suspend/resume",
      "Safe engine switching without segfaults",
      "Keyboard layout preserved during IBus activation",
      "IBus runtime recovery and non-ASCII text injection fallback",
      "Push-to-talk mode with improved silence detection",
      "Linux desktop integration",
    ],
  },
  {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: [
      {
        "@type": "Question",
        name: "Is Vocalinux really 100% offline?",
        acceptedAnswer: {
          "@type": "Answer",
          text: "Yes for local engines. All local speech recognition runs on your Linux machine. Vocalinux also offers an optional Remote API engine for user-configured servers.",
        },
      },
      {
        "@type": "Question",
        name: "Does Vocalinux collect usage telemetry?",
        acceptedAnswer: {
          "@type": "Answer",
          text: "No. The installed app does not send usage telemetry, analytics events, or background usage pings. Even the project maintainer cannot see how many people install or actively use Vocalinux.",
        },
      },
      {
        "@type": "Question",
        name: "Which Linux distributions are supported?",
        acceptedAnswer: {
          "@type": "Answer",
          text: "Vocalinux supports Ubuntu, Fedora, Debian, Arch, Linux Mint, Pop!_OS, and other modern Linux distributions across X11 and Wayland.",
        },
      },
      {
        "@type": "Question",
        name: "How do I switch between speech engines?",
        acceptedAnswer: {
          "@type": "Answer",
          text: "Use the settings GUI or CLI flags for whisper.cpp, Whisper, VOSK, or Remote API. Remote API settings live under Advanced settings.",
        },
      },
      {
        "@type": "Question",
        name: "What happens when I close my laptop lid?",
        acceptedAnswer: {
          "@type": "Answer",
          text: "Vocalinux v0.10.1+ automatically recovers speech recognition and keyboard shortcuts after system suspend/resume. No manual restart needed.",
        },
      },
      {
        "@type": "Question",
        name: "Does Vocalinux preserve my keyboard layout?",
        acceptedAnswer: {
          "@type": "Answer",
          text: "Yes. v0.10.1+ preserves your XKB keyboard layout when activating IBus, so you won't unexpectedly switch to US layout mid-dictation.",
        },
      },
    ],
  },
  {
    "@context": "https://schema.org",
    "@type": "HowTo",
    name: "Install Vocalinux on Linux",
    description: "Install offline voice dictation on Linux in a few minutes.",
    totalTime: "PT10M",
    step: [
      {
        "@type": "HowToStep",
        name: "Run the install command",
        text: "Copy the install command from vocalinux.com and run it in terminal.",
        url: "https://vocalinux.com/#install",
      },
      {
        "@type": "HowToStep",
        name: "Complete the guided setup",
        text: "Pick your speech engine and model size in the interactive installer.",
        url: "https://vocalinux.com/#install",
      },
      {
        "@type": "HowToStep",
        name: "Start dictating",
        text: "Launch vocalinux and use toggle or push-to-talk shortcut mode to begin dictation.",
        url: "https://vocalinux.com/#install",
      },
    ],
  },
];

const features = [
  {
    icon: Shield,
    title: "Offline and private",
    description:
      "Local engines process speech on your machine. Audio does not leave the computer unless you point Remote API at a server you chose.",
    href: "/offline/",
  },
  {
    icon: Laptop,
    title: "Works in any focused app",
    description:
      "Type into terminals, browsers, IDEs, office apps, and any text field on your Linux desktop.",
    href: "/use-cases/",
  },
  {
    icon: Zap,
    title: "whisper.cpp by default",
    description:
      "C++ inference with optional Vulkan GPU support for AMD, Intel, and NVIDIA. Tiny model is about 74MB.",
    href: "/gpu-acceleration/",
  },
  {
    icon: Keyboard,
    title: "Toggle or push-to-talk",
    description:
      "Double-tap to toggle, or hold a modifier for push-to-talk. Left and right keys can be distinguished.",
    href: "/shortcuts/",
  },
  {
    icon: Globe,
    title: "X11 and Wayland",
    description:
      "Text injection paths for both display servers, with clipboard fallback on unsupported Wayland compositors.",
    href: "/wayland/",
  },
  {
    icon: Settings,
    title: "Configurable",
    description:
      "Engine, model size, language, shortcuts, and voice commands. GUI settings or config file.",
    href: "/advanced-settings/",
  },
  {
    icon: Server,
    title: "Remote API engine",
    description:
      "Optional OpenAI-compatible or whisper.cpp server when another machine should transcribe.",
    href: "/remote-api/",
  },
  {
    icon: Activity,
    title: "Silero voice activity detection",
    description:
      "Neural VAD drops silence-only buffers when ONNX Runtime is available, with amplitude fallback.",
    href: "/voice-activity-detection/",
  },
  {
    icon: ShieldCheck,
    title: "Desktop reliability",
    description:
      "Suspend/resume recovery, IBus hardening, keyboard layout preservation, non-ASCII injection fallbacks.",
    href: "/desktop-reliability/",
  },
] as const;

const CopyButton = ({
  text,
  className = "",
}: {
  text: string;
  className?: string;
}) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = useCallback(() => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }, [text]);

  return (
    <button
      onClick={handleCopy}
      className={`flex items-center gap-2 rounded bg-zinc-800 px-3 py-1.5 text-sm text-zinc-100 transition-colors hover:bg-zinc-700 ${className}`}
      aria-label={copied ? "Copied to clipboard" : "Copy to clipboard"}
    >
      {copied ? (
        <>
          <Check className="h-4 w-4" />
          Copied
        </>
      ) : (
        <>
          <Copy className="h-4 w-4" />
          Copy
        </>
      )}
    </button>
  );
};

function TerminalBlock({
  command,
  displayCommand,
  title,
  subtitle,
}: {
  command: string;
  displayCommand: string;
  title?: string;
  subtitle?: string;
}) {
  return (
    <div className="terminal-panel">
      <div className="flex items-center justify-between border-b border-zinc-800 px-4 py-2.5">
        <div className="flex min-w-0 items-center gap-2 text-left">
          <Terminal className="h-4 w-4 shrink-0 text-[color:var(--terminal-fg)]" />
          {title ? (
            <div className="min-w-0">
              <p className="truncate text-sm font-medium text-zinc-100">{title}</p>
              {subtitle ? (
                <p className="truncate text-xs text-zinc-500">{subtitle}</p>
              ) : null}
            </div>
          ) : (
            <span className="text-xs text-zinc-500">terminal</span>
          )}
        </div>
        <CopyButton text={command} />
      </div>
      <div className="p-4 sm:p-5">
        <pre className="whitespace-pre-wrap text-left font-mono text-sm text-[color:var(--terminal-fg)] sm:text-[0.9375rem]">
          <span className="select-none text-zinc-500">$ </span>
          {displayCommand}
        </pre>
      </div>
    </div>
  );
}

export default function HomePage() {
  const [stars, setStars] = useState<number | null>(null);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    fetch("https://api.github.com/repos/jatinkrmalik/vocalinux")
      .then((res) => res.json())
      .then((data) => {
        if (data.stargazers_count) {
          setStars(data.stargazers_count);
        }
      })
      .catch(() => {
        setStars(null);
      });
  }, []);

  const navLinks = [
    { href: "#demo", label: "Demo" },
    { href: "#features", label: "Features" },
    { href: "/screenshots/", label: "Screenshots" },
    { href: "#install", label: "Install" },
    { href: "#guides", label: "Guides" },
    { href: "#faq", label: "FAQ" },
  ];

  const {
    interactiveInstallCommand,
    interactiveInstallDisplayCommand,
    uninstallCommand,
    uninstallDisplayCommand,
  } = installCommands;

  return (
    <main className="min-h-screen bg-background text-foreground">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(homeJsonLd) }}
      />

      <header className="fixed left-0 right-0 top-0 z-50 border-b border-border bg-background/90 backdrop-blur-sm">
        <nav className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3 sm:px-6">
          <Link href="/" className="flex items-center gap-2.5">
            <VocalinuxLogo
              width={32}
              height={32}
              className="h-7 w-7 sm:h-8 sm:w-8"
              priority
            />
            <span className="font-display text-lg font-semibold tracking-tight sm:text-xl">
              Vocalinux
            </span>
            <span className="hidden rounded-full border border-border bg-card px-2 py-0.5 text-xs font-medium text-muted-foreground sm:inline-block">
              v0.14.2
            </span>
          </Link>

          <div className="hidden items-center gap-5 md:flex">
            {navLinks.map((link) =>
              link.href.startsWith("/") ? (
                <Link
                  key={link.href}
                  href={link.href}
                  className="text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
                >
                  {link.label}
                </Link>
              ) : (
                <a
                  key={link.href}
                  href={link.href}
                  className="text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
                >
                  {link.label}
                </a>
              ),
            )}
            <a
              href="https://github.com/jatinkrmalik/vocalinux"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 text-sm text-muted-foreground transition-colors hover:text-foreground"
            >
              <Star className="h-4 w-4" />
              {stars !== null && (
                <span className="tabular-nums">{stars.toLocaleString()}</span>
              )}
            </a>
            <ThemeToggle />
          </div>

          <div className="flex items-center gap-2 md:hidden">
            <ThemeToggle />
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="rounded-md p-2 text-foreground"
              aria-label="Toggle menu"
              aria-expanded={mobileMenuOpen}
            >
              {mobileMenuOpen ? (
                <X className="h-6 w-6" />
              ) : (
                <Menu className="h-6 w-6" />
              )}
            </button>
          </div>
        </nav>

        {mobileMenuOpen ? (
          <div className="border-t border-border bg-background md:hidden">
            <div className="space-y-1 px-4 py-3">
              {navLinks.map((link) =>
                link.href.startsWith("/") ? (
                  <Link
                    key={link.href}
                    href={link.href}
                    className="block py-2 text-foreground"
                    onClick={() => setMobileMenuOpen(false)}
                  >
                    {link.label}
                  </Link>
                ) : (
                  <a
                    key={link.href}
                    href={link.href}
                    className="block py-2 text-foreground"
                    onClick={() => setMobileMenuOpen(false)}
                  >
                    {link.label}
                  </a>
                ),
              )}
              <a
                href="https://github.com/jatinkrmalik/vocalinux"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 py-2 text-foreground"
                onClick={() => setMobileMenuOpen(false)}
              >
                <Github className="h-5 w-5" />
                GitHub
              </a>
            </div>
          </div>
        ) : null}
      </header>

      {/* Hero: asymmetric offer + install proof */}
      <section className="px-4 pb-16 pt-28 sm:px-6 sm:pb-20 sm:pt-32">
        <div className="mx-auto grid max-w-6xl items-start gap-12 lg:grid-cols-[minmax(0,1.05fr)_minmax(0,0.95fr)] lg:gap-14">
          <div>
            <p className="mb-4 text-sm font-medium text-primary">
              Offline voice typing for Linux
            </p>
            <h1 className="font-display text-4xl font-semibold tracking-tight text-foreground sm:text-5xl lg:text-[3.25rem] lg:leading-[1.08]">
              Speak. It types into the app you are using.
            </h1>
            <p className="mt-5 max-w-xl text-lg text-muted-foreground sm:text-xl">
              Free, open-source dictation that runs on your machine with
              whisper.cpp, Whisper, or VOSK. Toggle mode or push-to-talk. X11 and
              Wayland.
            </p>

            <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:flex-wrap">
              <a href="#install" className="btn-primary">
                <Download className="h-5 w-5" />
                Install on Linux
              </a>
              <a
                href="https://github.com/jatinkrmalik/vocalinux"
                target="_blank"
                rel="noopener noreferrer"
                aria-label="View Vocalinux source code on GitHub (opens in a new tab)"
                className="btn-ink"
              >
                <Github className="h-5 w-5" />
                Source on GitHub
              </a>
              <a href="#ecosystem" className="btn-ghost">
                <Laptop className="h-5 w-5" />
                macOS / Windows
              </a>
            </div>

            <ul className="mt-10 grid max-w-lg grid-cols-2 gap-x-6 gap-y-3 text-sm text-muted-foreground">
              <li className="flex items-center gap-2">
                <Shield className="h-4 w-4 text-primary" aria-hidden />
                Local engines offline
              </li>
              <li className="flex items-center gap-2">
                <Lock className="h-4 w-4 text-primary" aria-hidden />
                No usage telemetry
              </li>
              <li className="flex items-center gap-2">
                <Activity className="h-4 w-4 text-primary" aria-hidden />
                On-device models
              </li>
              <li className="flex items-center gap-2">
                <Globe className="h-4 w-4 text-primary" aria-hidden />
                X11 and Wayland
              </li>
            </ul>
          </div>

          <div className="lg:pt-2">
            <TerminalBlock
              command={interactiveInstallCommand}
              displayCommand={interactiveInstallDisplayCommand}
              title="Interactive install"
              subtitle="Hardware detection and engine choice"
            />
            <p className="mt-3 text-sm text-muted-foreground">
              Ubuntu, Fedora, Debian, Arch, openSUSE, and similar distros. Default
              path is about one to two minutes.
            </p>
          </div>
        </div>
      </section>

      {/* Demo */}
      <section id="demo" className="border-t border-border bg-card px-4 py-16 sm:px-6 sm:py-20">
        <div className="mx-auto max-w-6xl">
          <div className="mb-10 max-w-2xl">
            <h2 className="section-heading">Browser speech preview</h2>
            <p className="section-lede">
              This demo uses the browser SpeechRecognition API when available.
              After install, Vocalinux runs offline on your Linux desktop.
            </p>
          </div>

          <LiveDemo />

          <div className="mt-10 grid gap-px overflow-hidden rounded-[10px] border border-border bg-border sm:grid-cols-3">
            {[
              {
                icon: Keyboard,
                title: "Shortcut modes",
                description: "Toggle (double-tap) or push-to-talk (hold).",
                href: "/shortcuts/",
              },
              {
                icon: Zap,
                title: "Engine choices",
                description: "Compare latency and model size per engine.",
                href: "/compare/",
              },
              {
                icon: Volume2,
                title: "Audio feedback",
                description: "Optional sounds when recording starts and stops.",
                href: "/shortcuts/",
              },
            ].map((item) => (
              <Link
                key={item.title}
                href={item.href}
                className="group flex gap-3 bg-card p-5 transition-colors hover:bg-secondary/60"
              >
                <item.icon className="mt-0.5 h-5 w-5 shrink-0 text-primary" />
                <div>
                  <h3 className="font-semibold text-foreground group-hover:text-primary">
                    {item.title}
                  </h3>
                  <p className="mt-1 text-sm text-muted-foreground">
                    {item.description}
                  </p>
                </div>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* Features as editorial rows */}
      <section id="features" className="px-4 py-16 sm:px-6 sm:py-20">
        <div className="mx-auto max-w-6xl">
          <div className="mb-4 flex flex-col gap-4 sm:mb-10 sm:flex-row sm:items-end sm:justify-between">
            <div className="max-w-2xl">
              <h2 className="section-heading">What you get on the desktop</h2>
              <p className="section-lede">
                System tray app, local recognition, and text injection into
                whatever window has focus. No cloud account.
              </p>
            </div>
            <Link
              href="/screenshots/"
              className="inline-flex shrink-0 items-center gap-1 text-sm font-semibold text-primary hover:underline"
            >
              Screenshots of the UI
              <ChevronRight className="h-4 w-4" />
            </Link>
          </div>

          <div className="rounded-[10px] border border-border bg-card px-5 sm:px-6">
            {features.map((feature) => (
              <Link
                key={feature.href}
                href={feature.href}
                className="feature-row group items-start transition-colors hover:bg-secondary/40 sm:items-center"
              >
                <feature.icon
                  className="mt-0.5 h-5 w-5 shrink-0 text-primary sm:mt-0"
                  aria-hidden
                />
                <div className="min-w-0 flex-1 sm:grid sm:grid-cols-[13rem_minmax(0,1fr)] sm:gap-6">
                  <h3 className="font-semibold text-foreground group-hover:text-primary">
                    {feature.title}
                  </h3>
                  <p className="mt-1 text-sm text-muted-foreground sm:mt-0 sm:text-base">
                    {feature.description}
                  </p>
                </div>
                <ChevronRight className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100 sm:mt-0" />
              </Link>
            ))}
          </div>

          <div className="mt-12 grid gap-8 rounded-[10px] border border-border bg-secondary/50 p-6 sm:p-8 md:grid-cols-2 md:items-center">
            <div>
              <h3 className="font-display text-2xl font-semibold tracking-tight">
                Built for the Linux desktop gap
              </h3>
              <p className="mt-3 text-muted-foreground">
                macOS and Windows ship voice typing. On Linux you still need a
                tray app that injects text reliably. That is this project.
              </p>
              <ul className="mt-5 space-y-2.5 text-sm sm:text-base">
                {[
                  "Local engines by default; remote only if you configure it",
                  "Works beyond a single editor or IDE plugin",
                  "Interactive installer instead of a long dependency ritual",
                ].map((item) => (
                  <li key={item} className="flex items-start gap-2.5">
                    <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-primary" />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>
            <div className="rounded-[10px] border border-border bg-card p-6">
              <div className="mb-5 flex items-center gap-3">
                <VocalinuxLogo width={48} height={48} className="h-12 w-12" />
                <div>
                  <div className="font-display text-xl font-semibold">
                    Vocalinux
                  </div>
                  <div className="text-sm text-muted-foreground">
                    System tray voice dictation
                  </div>
                </div>
              </div>
              <dl className="grid grid-cols-2 gap-3 text-center">
                <div className="rounded-md bg-secondary p-3">
                  <dt className="text-xs text-muted-foreground">Cloud calls</dt>
                  <dd className="font-display text-2xl font-semibold text-primary">
                    0
                  </dd>
                </div>
                <div className="rounded-md bg-secondary p-3">
                  <dt className="text-xs text-muted-foreground">License</dt>
                  <dd className="font-display text-2xl font-semibold text-primary">
                    GPL-3
                  </dd>
                </div>
              </dl>
            </div>
          </div>
        </div>
      </section>

      {/* Install */}
      <section
        id="install"
        className="border-t border-border bg-card px-4 py-16 sm:px-6 sm:py-20"
      >
        <div className="mx-auto max-w-3xl">
          <div className="mb-10 max-w-2xl">
            <h2 className="section-heading">Install on Linux</h2>
            <p className="section-lede">
              One command for the guided installer. It detects your system, lets
              you pick an engine, and sets up the desktop app.
            </p>
          </div>

          <TerminalBlock
            command={interactiveInstallCommand}
            displayCommand={interactiveInstallDisplayCommand}
            title="Recommended: interactive installer"
            subtitle="Creates a venv, downloads models, adds PATH and launcher"
          />

          <div className="mt-6 rounded-[10px] border border-border bg-background p-5">
            <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <h3 className="font-semibold">Engines during setup</h3>
                <p className="text-sm text-muted-foreground">
                  Pick what fits your hardware. You can switch later in Settings.
                </p>
              </div>
              <Link
                href="/compare/"
                className="inline-flex items-center gap-1 text-sm font-semibold text-primary hover:underline"
              >
                Compare engines <ChevronRight className="h-4 w-4" />
              </Link>
            </div>
            <div className="mt-4 grid gap-3 sm:grid-cols-3">
              {[
                {
                  title: "whisper.cpp",
                  description: "Default. Fast, Vulkan-capable.",
                },
                {
                  title: "Whisper",
                  description: "PyTorch / CUDA workflow.",
                },
                {
                  title: "VOSK",
                  description: "Small footprint for older machines.",
                },
              ].map((engine) => (
                <div
                  key={engine.title}
                  className="rounded-md border border-border bg-card p-3"
                >
                  <h4 className="font-semibold">{engine.title}</h4>
                  <p className="mt-1 text-sm text-muted-foreground">
                    {engine.description}
                  </p>
                </div>
              ))}
            </div>
          </div>

          <div className="mt-6 rounded-[10px] border border-border bg-background p-5">
            <h3 className="mb-3 font-semibold">What the installer does</h3>
            <ul className="grid gap-2 text-sm text-muted-foreground sm:grid-cols-2">
              {[
                "Installs system dependencies",
                "Creates an isolated virtual environment",
                "Downloads speech recognition models",
                "Sets up desktop integration",
                "Adds vocalinux to your PATH",
                "Creates an application launcher",
              ].map((item) => (
                <li key={item} className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-primary" />
                  {item}
                </li>
              ))}
            </ul>
          </div>

          <div className="mt-6 rounded-[10px] border border-primary/30 bg-accent/40 p-5">
            <h3 className="mb-2 flex items-center gap-2 font-semibold">
              <Play className="h-4 w-4 text-primary" />
              After install
            </h3>
            <p className="mb-3 text-sm text-muted-foreground">
              Launch from a terminal or your application menu:
            </p>
            <code className="block rounded-md bg-[color:var(--terminal)] px-4 py-2 font-mono text-sm text-[color:var(--terminal-fg)]">
              vocalinux
            </code>
          </div>

          <div className="mt-8 space-y-6">
            <div className="rounded-[10px] border border-border bg-background p-5">
              <h3 className="mb-3 flex items-center gap-2 font-semibold">
                <Cpu className="h-5 w-5 text-primary" />
                System requirements
              </h3>
              <ul className="grid gap-2 text-sm text-muted-foreground sm:grid-cols-2">
                <li>Ubuntu, Debian, Fedora, Arch, openSUSE, or equivalent</li>
                <li>Python 3.9+ with GTK 3 / PyGObject</li>
                <li>4GB RAM minimum; 8GB+ for larger models</li>
                <li>Microphone plus X11 or Wayland session</li>
                <li>~200MB disk for the default whisper.cpp setup</li>
                <li>Optional Vulkan GPU for acceleration</li>
              </ul>
            </div>

            <div>
              <h3 className="mb-3 font-semibold">Uninstall</h3>
              <TerminalBlock
                command={uninstallCommand}
                displayCommand={uninstallDisplayCommand}
                title="Clean removal"
              />
            </div>
          </div>
        </div>
      </section>

      {/* Distro guides */}
      <section id="guides" className="px-4 py-16 sm:px-6 sm:py-20">
        <div className="mx-auto max-w-6xl">
          <div className="mb-10 max-w-2xl">
            <h2 className="section-heading">Guides by distribution</h2>
            <p className="section-lede">
              Distro-specific notes for Ubuntu, Fedora, and Arch, including
              post-install checks.
            </p>
          </div>

          <div className="grid gap-4 md:grid-cols-3">
            {[
              {
                href: "/install/ubuntu/",
                title: "Ubuntu",
                description:
                  "Ubuntu 22.04+ for GNOME, KDE, X11, and Wayland.",
              },
              {
                href: "/install/fedora/",
                title: "Fedora",
                description:
                  "Fedora Workstation setup with distro-specific notes.",
              },
              {
                href: "/install/arch/",
                title: "Arch",
                description:
                  "Arch, Manjaro, and EndeavourOS with injection checks.",
              },
            ].map((guide) => (
              <Link
                key={guide.href}
                href={guide.href}
                className="group rounded-[10px] border border-border bg-card p-5 transition-colors hover:border-primary/40 hover:bg-secondary/40"
              >
                <h3 className="text-lg font-semibold group-hover:text-primary">
                  {guide.title}
                </h3>
                <p className="mt-2 text-sm text-muted-foreground">
                  {guide.description}
                </p>
                <span className="mt-4 inline-flex items-center gap-1 text-sm font-semibold text-primary">
                  Read guide <ChevronRight className="h-4 w-4" />
                </span>
              </Link>
            ))}
          </div>

          <div className="mt-8 flex flex-col gap-3 rounded-[10px] border border-border bg-secondary/40 p-5 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h3 className="font-semibold">Choosing an engine</h3>
              <p className="text-sm text-muted-foreground">
                Speed, hardware support, and model size for whisper.cpp, Whisper,
                and VOSK.
              </p>
            </div>
            <Link
              href="/compare/"
              className="inline-flex shrink-0 items-center gap-1 text-sm font-semibold text-primary hover:underline"
            >
              Engine comparison <ChevronRight className="h-4 w-4" />
            </Link>
          </div>
        </div>
      </section>

      {/* Engines */}
      <section className="border-t border-border bg-card px-4 py-16 sm:px-6 sm:py-20">
        <div className="mx-auto max-w-6xl">
          <div className="mb-10 max-w-2xl">
            <h2 className="section-heading">Speech engines</h2>
            <p className="section-lede">
              Local engines process audio on-device. Remote API is optional for a
              server you control.
            </p>
          </div>

          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            {[
              {
                title: "whisper.cpp",
                badge: "Default",
                description:
                  "C++ port of Whisper with Vulkan GPU support. Fast install and true multi-threading.",
                points: [
                  "About 1–2 min default install",
                  "AMD / Intel / NVIDIA via Vulkan",
                  "Tiny model ~74MB",
                ],
                highlight: true,
              },
              {
                title: "Whisper (OpenAI)",
                description:
                  "Original PyTorch Whisper. Best when you already use CUDA on NVIDIA.",
                points: [
                  "PyTorch implementation",
                  "NVIDIA CUDA",
                  "Larger download (~2.3GB stack)",
                ],
              },
              {
                title: "VOSK",
                description:
                  "Lightweight streaming recognition for lower-powered systems.",
                points: [
                  "Small memory footprint",
                  "CPU-only, minimal resources",
                  "~40MB models available",
                ],
              },
              {
                title: "Remote API",
                description:
                  "Send audio to an OpenAI-compatible or whisper.cpp server you configure.",
                points: [
                  "Bearer token auth optional",
                  "Local VAD and injection stay local",
                  "LAN or trusted remote backends",
                ],
              },
            ].map((engine) => (
              <div
                key={engine.title}
                className={`flex h-full flex-col rounded-[10px] border bg-background p-5 ${
                  engine.highlight
                    ? "border-primary"
                    : "border-border"
                }`}
              >
                <div className="mb-3 flex items-start justify-between gap-2">
                  <h3 className="text-lg font-semibold">{engine.title}</h3>
                  {engine.badge ? (
                    <span className="rounded-full bg-primary px-2 py-0.5 text-xs font-semibold text-primary-foreground">
                      {engine.badge}
                    </span>
                  ) : null}
                </div>
                <p className="mb-4 text-sm text-muted-foreground">
                  {engine.description}
                </p>
                <ul className="mt-auto space-y-2">
                  {engine.points.map((point) => (
                    <li
                      key={point}
                      className="flex items-start gap-2 text-sm"
                    >
                      <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
                      {point}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>

          <div className="mt-8">
            <Link
              href="/compare/"
              className="inline-flex items-center gap-1.5 text-sm font-medium text-primary hover:underline"
            >
              Full engine comparison <ChevronRight className="h-4 w-4" />
            </Link>
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section id="faq" className="px-4 py-16 sm:px-6 sm:py-20">
        <div className="mx-auto max-w-3xl">
          <h2 className="section-heading mb-8">FAQ</h2>

          <div className="space-y-3">
            {(
              [
                {
                  question: "Is Vocalinux really 100% offline?",
                  answer: (
                    <>
                      Yes for local engines: whisper.cpp, Whisper, and VOSK
                      process speech on your machine. Remote API is optional and
                      only talks to servers you configure.{" "}
                      <Link
                        href="/offline/"
                        className="font-medium text-primary hover:underline"
                      >
                        Offline details
                      </Link>
                      .
                    </>
                  ),
                },
                {
                  question: "Does Vocalinux collect usage telemetry?",
                  answer:
                    "No. The installed app does not send usage telemetry, analytics events, or background usage pings. The project maintainer cannot see how many people install or actively use it. You can verify by watching for external network calls after install.",
                },
                {
                  question: "Which Linux distributions are supported?",
                  answer: (
                    <>
                      Ubuntu 22.04+, Debian 11+, Fedora 39+, Arch Linux, and
                      openSUSE Tumbleweed are well tested. Experimental support
                      exists for Gentoo, Alpine, Void, Solus, and others. X11 and
                      Wayland are both supported.{" "}
                      <Link
                        href="/install/"
                        className="font-medium text-primary hover:underline"
                      >
                        Install guides
                      </Link>
                      .
                    </>
                  ),
                },
                {
                  question: "How do I switch between speech engines?",
                  answer: (
                    <>
                      Settings dialog or CLI:{" "}
                      <code className="rounded bg-secondary px-1.5 py-0.5 font-mono text-sm">
                        --engine whisper_cpp
                      </code>
                      ,{" "}
                      <code className="rounded bg-secondary px-1.5 py-0.5 font-mono text-sm">
                        whisper
                      </code>
                      ,{" "}
                      <code className="rounded bg-secondary px-1.5 py-0.5 font-mono text-sm">
                        vosk
                      </code>
                      , or{" "}
                      <code className="rounded bg-secondary px-1.5 py-0.5 font-mono text-sm">
                        remote_api
                      </code>
                      .{" "}
                      <Link
                        href="/compare/"
                        className="font-medium text-primary hover:underline"
                      >
                        Compare engines
                      </Link>
                      .
                    </>
                  ),
                },
                {
                  question: "Can Vocalinux use a remote transcription server?",
                  answer: (
                    <>
                      Yes. v0.12.0+ supports OpenAI-compatible Whisper servers and
                      the whisper.cpp server endpoint under Settings → Advanced →
                      Remote Server.{" "}
                      <Link
                        href="/remote-api/"
                        className="font-medium text-primary hover:underline"
                      >
                        Remote API guide
                      </Link>
                      .
                    </>
                  ),
                },
                {
                  question: "What is Silero VAD?",
                  answer: (
                    <>
                      Neural voice activity detection. When ONNX Runtime is
                      available, silence-only buffers are dropped before
                      recognition; amplitude VAD is the fallback.{" "}
                      <Link
                        href="/voice-activity-detection/"
                        className="font-medium text-primary hover:underline"
                      >
                        VAD notes
                      </Link>
                      .
                    </>
                  ),
                },
                {
                  question: "What happens when I close my laptop lid?",
                  answer: (
                    <>
                      v0.10.1+ recovers speech recognition and shortcuts after
                      suspend/resume without a manual restart.{" "}
                      <Link
                        href="/desktop-reliability/"
                        className="font-medium text-primary hover:underline"
                      >
                        Reliability notes
                      </Link>
                      .
                    </>
                  ),
                },
                {
                  question: "Does Vocalinux preserve my keyboard layout?",
                  answer:
                    "Yes. v0.10.1+ keeps your XKB layout when activating IBus, so dictation does not silently switch you to US layout.",
                },
                {
                  question: "What are the system requirements?",
                  answer: (
                    <>
                      4GB RAM minimum, Python 3.9+, about 200MB disk for the
                      default setup. 8GB+ RAM helps larger Whisper models. Vulkan
                      GPU acceleration is optional.{" "}
                      <Link
                        href="/install/"
                        className="font-medium text-primary hover:underline"
                      >
                        Full requirements
                      </Link>
                      .
                    </>
                  ),
                },
                {
                  question: "Can I use languages other than English?",
                  answer: (
                    <>
                      whisper.cpp and Whisper cover many languages with varying
                      accuracy. VOSK ships models for English, Hindi, Spanish,
                      French, German, Italian, Portuguese, Russian, Chinese, and
                      more.{" "}
                      <Link
                        href="/languages/"
                        className="font-medium text-primary hover:underline"
                      >
                        Languages
                      </Link>
                      .
                    </>
                  ),
                },
                {
                  question: "How do I customize the activation shortcut?",
                  answer: (
                    <>
                      Default is toggle with double-tap Ctrl. Settings can switch
                      to push-to-talk and other modifiers, or edit{" "}
                      <code className="rounded bg-secondary px-1.5 py-0.5 font-mono text-sm">
                        ~/.config/vocalinux/config.json
                      </code>
                      .{" "}
                      <Link
                        href="/shortcuts/"
                        className="font-medium text-primary hover:underline"
                      >
                        Shortcuts
                      </Link>
                      .
                    </>
                  ),
                },
                {
                  question: "Can I disable voice commands?",
                  answer: (
                    <>
                      Yes, in Settings. Commands default on for VOSK and off for
                      Whisper/whisper.cpp; you can override either way.{" "}
                      <Link
                        href="/shortcuts/"
                        className="font-medium text-primary hover:underline"
                      >
                        Voice commands
                      </Link>
                      .
                    </>
                  ),
                },
                {
                  question: "Is Vocalinux free?",
                  answer: (
                    <>
                      Yes. GPL-3.0, no premium tiers, no subscriptions.{" "}
                      <Link
                        href="/open-source/"
                        className="font-medium text-primary hover:underline"
                      >
                        About the project
                      </Link>
                      .
                    </>
                  ),
                },
              ] as { question: string; answer: React.ReactNode }[]
            ).map((item) => (
              <details
                key={item.question}
                className="group rounded-[10px] border border-border bg-card"
              >
                <summary className="flex cursor-pointer list-none items-center justify-between gap-4 p-5">
                  <h3 className="pr-2 font-semibold">{item.question}</h3>
                  <ChevronRight className="h-5 w-5 shrink-0 text-muted-foreground transition-transform group-open:rotate-90" />
                </summary>
                <div className="px-5 pb-5 text-muted-foreground">{item.answer}</div>
              </details>
            ))}
          </div>
        </div>
      </section>

      {/* Ecosystem */}
      <section
        id="ecosystem"
        className="border-t border-border bg-card px-4 py-16 sm:px-6 sm:py-20"
      >
        <div className="mx-auto max-w-6xl">
          <div className="mb-10 max-w-2xl">
            <h2 className="section-heading">Voca on other platforms</h2>
            <p className="section-lede">
              Related projects for macOS and Windows. This site is about the
              Linux app.
            </p>
          </div>

          <div className="grid gap-4 md:grid-cols-3">
            <div className="rounded-[10px] border border-border bg-background p-5">
              <div className="mb-3 flex items-center justify-between">
                <h3 className="text-lg font-semibold">VocaMac</h3>
                <span className="rounded bg-secondary px-2 py-0.5 text-xs font-semibold text-foreground">
                  Beta
                </span>
              </div>
              <p className="mb-4 text-sm text-muted-foreground">
                Native macOS menu bar app. Offline voice-to-text with WhisperKit
                and CoreML on Apple Silicon.
              </p>
              <div className="flex flex-wrap gap-2">
                <a
                  href="https://vocamac.com"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 rounded-md bg-primary px-3 py-2 text-sm font-medium text-primary-foreground"
                >
                  Website
                </a>
                <a
                  href="https://github.com/jatinkrmalik/vocamac"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 rounded-md border border-border px-3 py-2 text-sm font-medium"
                >
                  GitHub
                </a>
              </div>
            </div>

            <div className="rounded-[10px] border-2 border-primary bg-background p-5">
              <div className="mb-3 flex items-center justify-between">
                <h3 className="text-lg font-semibold">VocaLinux</h3>
                <span className="rounded bg-primary px-2 py-0.5 text-xs font-semibold text-primary-foreground">
                  You are here
                </span>
              </div>
              <p className="mb-4 text-sm text-muted-foreground">
                System tray app with whisper.cpp, Vulkan, and full offline
                support on Linux.
              </p>
              <div className="flex flex-wrap gap-2">
                <a
                  href="#install"
                  className="inline-flex items-center gap-1.5 rounded-md bg-primary px-3 py-2 text-sm font-medium text-primary-foreground"
                >
                  Install
                </a>
                <a
                  href="https://github.com/jatinkrmalik/vocalinux"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 rounded-md border border-border px-3 py-2 text-sm font-medium"
                >
                  GitHub
                </a>
              </div>
            </div>

            <div className="rounded-[10px] border border-border bg-background p-5">
              <div className="mb-3 flex items-center justify-between">
                <h3 className="text-lg font-semibold">VocaWin</h3>
                <span className="rounded bg-secondary px-2 py-0.5 text-xs font-semibold text-muted-foreground">
                  Planned
                </span>
              </div>
              <p className="mb-4 text-sm text-muted-foreground">
                Windows tray app with an offline-first design. Still in planning.
              </p>
              <div className="flex flex-wrap gap-2">
                <a
                  href="https://vocawin.com"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 rounded-md bg-primary px-3 py-2 text-sm font-medium text-primary-foreground"
                >
                  Website
                </a>
                <a
                  href="https://github.com/jatinkrmalik/vocawin"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 rounded-md border border-border px-3 py-2 text-sm font-medium"
                >
                  GitHub
                </a>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Close CTA */}
      <section className="border-t border-border px-4 py-16 sm:px-6 sm:py-20">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="section-heading">Install and try a real dictation session</h2>
          <p className="section-lede mx-auto">
            Free under GPL-3.0. Local engines by default. Star the repo if it
            helps your setup.
          </p>
          <div className="mt-8 flex flex-col justify-center gap-3 sm:flex-row">
            <a href="#install" className="btn-primary">
              <Download className="h-5 w-5" />
              Install Vocalinux
            </a>
            <a
              href="https://github.com/jatinkrmalik/vocalinux"
              target="_blank"
              rel="noopener noreferrer"
              className="btn-ink"
            >
              <Star className="h-5 w-5" />
              Star on GitHub
            </a>
          </div>
        </div>
      </section>

      <footer className="border-t border-border bg-[color:var(--ink)] px-4 py-12 text-[color:var(--paper)] sm:px-6 dark:bg-card dark:text-foreground">
        <div className="mx-auto max-w-6xl">
          <div className="mb-12 grid grid-cols-2 gap-8 md:grid-cols-3 lg:grid-cols-6">
            <div className="col-span-2 mb-4 lg:col-span-1 lg:mb-0">
              <Link href="/" className="mb-4 flex items-center gap-2">
                <VocalinuxLogo width={32} height={32} className="h-8 w-8" />
                <span className="font-display text-xl font-semibold">
                  Vocalinux
                </span>
              </Link>
              <p className="mb-4 max-w-xs text-sm text-zinc-400 dark:text-muted-foreground">
                Free open-source voice dictation for Linux. Offline by default.
              </p>
              <a
                href="https://github.com/jatinkrmalik/vocalinux"
                target="_blank"
                rel="noopener noreferrer"
                className="text-zinc-400 transition-colors hover:text-white dark:hover:text-foreground"
                aria-label="GitHub"
              >
                <Github className="h-6 w-6" />
              </a>
            </div>

            {(
              [
                {
                  title: "Get started",
                  links: [
                    { href: "#features", label: "Features", external: false },
                    { href: "/install/", label: "Install guide" },
                    { href: "/screenshots/", label: "Screenshots" },
                    { href: "/changelog/", label: "Changelog" },
                    { href: "/autostart/", label: "Autostart" },
                  ],
                },
                {
                  title: "Recognition",
                  links: [
                    { href: "/compare/", label: "Engine comparison" },
                    { href: "/remote-api/", label: "Remote API" },
                    { href: "/whisper-model-guide/", label: "Whisper models" },
                    { href: "/advanced-settings/", label: "Advanced settings" },
                    { href: "/voice-activity-detection/", label: "Silero VAD" },
                    { href: "/vs-nerd-dictation/", label: "vs Nerd Dictation" },
                  ],
                },
                {
                  title: "Desktop",
                  links: [
                    { href: "/wayland/", label: "Wayland" },
                    { href: "/gpu-acceleration/", label: "GPU acceleration" },
                    {
                      href: "/desktop-reliability/",
                      label: "Desktop reliability",
                    },
                    { href: "/shortcuts/", label: "Voice commands" },
                    { href: "/offline/", label: "Offline" },
                  ],
                },
                {
                  title: "Use cases",
                  links: [
                    { href: "/for-developers/", label: "Developers" },
                    { href: "/writers/", label: "Writers" },
                    { href: "/voice-typing-vscode/", label: "VS Code" },
                    { href: "/gnome-kde/", label: "GNOME vs KDE" },
                    { href: "/rsi-prevention/", label: "RSI prevention" },
                  ],
                },
                {
                  title: "Support",
                  links: [
                    { href: "/faq/", label: "FAQ" },
                    { href: "/troubleshooting/", label: "Troubleshooting" },
                    { href: "/alternatives/", label: "Alternatives" },
                    { href: "/privacy/", label: "Privacy" },
                  ],
                },
              ] as {
                title: string;
                links: { href: string; label: string; external?: boolean }[];
              }[]
            ).map((col) => (
              <div key={col.title}>
                <h3 className="mb-4 text-sm font-semibold text-zinc-300 dark:text-foreground">
                  {col.title}
                </h3>
                <ul className="space-y-2.5 text-sm">
                  {col.links.map((link) => (
                    <li key={link.href + link.label}>
                      {link.href.startsWith("#") ? (
                        <a
                          href={link.href}
                          className="text-zinc-400 transition-colors hover:text-white dark:text-muted-foreground dark:hover:text-foreground"
                        >
                          {link.label}
                        </a>
                      ) : (
                        <Link
                          href={link.href}
                          className="text-zinc-400 transition-colors hover:text-white dark:text-muted-foreground dark:hover:text-foreground"
                        >
                          {link.label}
                        </Link>
                      )}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>

          <div className="flex flex-col items-center justify-between gap-4 border-t border-zinc-800 pt-8 sm:flex-row dark:border-border">
            <p className="text-sm text-zinc-400 dark:text-muted-foreground">
              © {new Date().getFullYear()} Vocalinux. Open-source under GPL-3.0.
            </p>
            <p className="flex items-center gap-1 text-sm text-zinc-400 dark:text-muted-foreground">
              Made with <Heart className="h-4 w-4 text-primary" /> by{" "}
              <a
                href="https://x.com/intent/user?screen_name=jatinkrmalik"
                target="_blank"
                rel="noopener noreferrer"
                className="transition-colors hover:text-white dark:hover:text-foreground"
              >
                Jatin K Malik
              </a>
            </p>
          </div>
        </div>
      </footer>
    </main>
  );
}
