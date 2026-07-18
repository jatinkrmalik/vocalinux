"use client";

import React, { useCallback, useEffect, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { motion, useReducedMotion } from "framer-motion";
import {
  Check,
  ChevronRight,
  Copy,
  Github,
  Menu,
  Star,
  X,
} from "lucide-react";
import { LiveDemo } from "@/components/live-demo";
import { ThemeToggle } from "@/components/theme-toggle";
import { VocalinuxLogo } from "@/components/optimized-image";

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

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  const handleCopy = useCallback(() => {
    void navigator.clipboard.writeText(text);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 2000);
  }, [text]);

  return (
    <button
      type="button"
      onClick={handleCopy}
      className="inline-flex items-center gap-1.5 rounded-md border border-white/10 bg-white/5 px-2.5 py-1.5 font-mono text-xs text-zinc-200 transition-colors hover:bg-white/10"
      aria-label={copied ? "Copied to clipboard" : "Copy to clipboard"}
    >
      {copied ? <Check className="h-3.5 w-3.5 text-primary" /> : <Copy className="h-3.5 w-3.5" />}
      {copied ? "Copied" : "Copy"}
    </button>
  );
}

function TerminalBlock({
  command,
  display,
  label,
}: {
  command: string;
  display: string;
  label: string;
}) {
  return (
    <div className="overflow-hidden rounded-[10px] border border-zinc-800 bg-[#0a0a0c]">
      <div className="flex items-center justify-between border-b border-zinc-800/80 px-4 py-2.5">
        <div className="flex items-center gap-3">
          <div className="flex gap-1.5" aria-hidden>
            <span className="h-2.5 w-2.5 rounded-full bg-zinc-700" />
            <span className="h-2.5 w-2.5 rounded-full bg-zinc-700" />
            <span className="h-2.5 w-2.5 rounded-full bg-zinc-700" />
          </div>
          <span className="font-mono text-[11px] tracking-wide text-zinc-500">
            {label}
          </span>
        </div>
        <CopyButton text={command} />
      </div>
      <pre className="overflow-x-auto p-4 font-mono text-[13px] leading-relaxed text-emerald-400 sm:p-5 sm:text-sm">
        <span className="select-none text-zinc-600">$ </span>
        {display}
      </pre>
    </div>
  );
}

function Reveal({
  children,
  className = "",
  delay = 0,
}: {
  children: React.ReactNode;
  className?: string;
  delay?: number;
}) {
  const reduce = useReducedMotion();
  return (
    <motion.div
      className={className}
      initial={reduce ? false : { opacity: 0, y: 18 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, amount: 0.2 }}
      transition={{
        duration: 0.55,
        delay,
        ease: [0.16, 1, 0.3, 1],
      }}
    >
      {children}
    </motion.div>
  );
}

const navLinks = [
  { href: "#demo", label: "Demo" },
  { href: "#features", label: "Features" },
  { href: "#install", label: "Install" },
  { href: "#guides", label: "Guides" },
  { href: "#faq", label: "FAQ" },
];

const featureRows = [
  {
    title: "Stays on your machine",
    body: "Local engines process audio on-device. No cloud upload, no telemetry, no account.",
    href: "/offline/",
    link: "Offline privacy",
  },
  {
    title: "Works where you type",
    body: "Terminals, browsers, IDEs, office apps, and any focused text field on X11 or Wayland.",
    href: "/use-cases/",
    link: "Use cases",
  },
  {
    title: "Fast by default",
    body: "whisper.cpp with Vulkan acceleration on AMD, Intel, and NVIDIA. Tiny model is ~74MB.",
    href: "/gpu-acceleration/",
    link: "GPU acceleration",
  },
  {
    title: "Your shortcuts",
    body: "Toggle or push-to-talk. Bind modifiers the way your hands already work.",
    href: "/shortcuts/",
    link: "Shortcuts",
  },
  {
    title: "Desktop reliability",
    body: "Suspend recovery, IBus hardening, layout preservation, non-ASCII injection fallbacks.",
    href: "/desktop-reliability/",
    link: "Reliability notes",
  },
  {
    title: "Neural silence filter",
    body: "Silero VAD drops empty buffers before recognition, with amplitude fallback if needed.",
    href: "/voice-activity-detection/",
    link: "Voice activity detection",
  },
];

const engines = [
  {
    name: "whisper.cpp",
    badge: "Default",
    summary: "C++ Whisper with Vulkan. Fast install, multi-vendor GPU.",
    points: [
      "About 1-2 min default setup",
      "AMD / Intel / NVIDIA via Vulkan",
      "Tiny model ~74MB",
    ],
  },
  {
    name: "Whisper",
    summary: "Original OpenAI PyTorch path for NVIDIA CUDA workflows.",
    points: [
      "Same model family accuracy",
      "CUDA when you already live in PyTorch",
      "Larger install footprint",
    ],
  },
  {
    name: "VOSK",
    summary: "Small footprint for older machines and tight RAM budgets.",
    points: [
      "CPU-friendly streaming",
      "Models around ~40MB",
      "Great on modest hardware",
    ],
  },
  {
    name: "Remote API",
    summary: "Offload to a server you trust while keeping desktop injection local.",
    points: [
      "OpenAI-compatible endpoints",
      "whisper.cpp server support",
      "Local VAD still applies",
    ],
  },
];

const faqItems: { question: string; answer: React.ReactNode }[] = [
  {
    question: "Is Vocalinux really 100% offline?",
    answer: (
      <>
        Yes for local engines: whisper.cpp, Whisper, and VOSK process speech on
        your machine. An optional Remote API engine exists for servers you
        configure yourself.{" "}
        <Link href="/offline/" className="font-medium text-primary hover:underline">
          Offline details
        </Link>
        .
      </>
    ),
  },
  {
    question: "Does Vocalinux collect usage telemetry?",
    answer:
      "No. The installed app does not send usage telemetry, analytics events, or background usage pings. Even the project maintainer cannot see how many people install or actively use Vocalinux.",
  },
  {
    question: "Which Linux distributions are supported?",
    answer: (
      <>
        Ubuntu 22.04+, Debian 11+, Fedora 39+, Arch, openSUSE Tumbleweed, and
        most modern desktops on X11 or Wayland.{" "}
        <Link href="/install/" className="font-medium text-primary hover:underline">
          Installation guides
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
        <code className="rounded bg-muted px-1.5 py-0.5 font-mono text-[0.85em]">
          --engine whisper_cpp
        </code>
        ,{" "}
        <code className="rounded bg-muted px-1.5 py-0.5 font-mono text-[0.85em]">
          whisper
        </code>
        ,{" "}
        <code className="rounded bg-muted px-1.5 py-0.5 font-mono text-[0.85em]">
          vosk
        </code>
        , or{" "}
        <code className="rounded bg-muted px-1.5 py-0.5 font-mono text-[0.85em]">
          remote_api
        </code>
        .{" "}
        <Link href="/compare/" className="font-medium text-primary hover:underline">
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
        Yes. OpenAI-compatible Whisper servers and whisper.cpp server endpoints
        are supported under Settings → Advanced → Remote Server.{" "}
        <Link href="/remote-api/" className="font-medium text-primary hover:underline">
          Remote API guide
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
        suspend/resume.{" "}
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
      "Yes. v0.10.1+ preserves your XKB layout when activating IBus, so you will not get bounced to US layout mid-dictation.",
  },
  {
    question: "What are the system requirements?",
    answer: (
      <>
        Minimum: 4GB RAM, Python 3.9+, ~200MB disk for the default setup. 8GB+
        recommended for larger Whisper models. Optional Vulkan GPU on AMD,
        Intel, or NVIDIA.{" "}
        <Link href="/install/" className="font-medium text-primary hover:underline">
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
        whisper.cpp and Whisper cover 99+ languages. VOSK ships models for major
        languages including English, Hindi, Spanish, French, German, and more.{" "}
        <Link href="/languages/" className="font-medium text-primary hover:underline">
          Language support
        </Link>
        .
      </>
    ),
  },
  {
    question: "Is Vocalinux free?",
    answer: (
      <>
        Completely free and open-source under GPL-3.0. No premium tiers, no
        subscriptions.{" "}
        <Link href="/open-source/" className="font-medium text-primary hover:underline">
          About the project
        </Link>
        .
      </>
    ),
  },
];

export default function HomePage() {
  const [stars, setStars] = useState<number | null>(null);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const reduce = useReducedMotion();
  const {
    interactiveInstallCommand,
    interactiveInstallDisplayCommand,
    uninstallCommand,
    uninstallDisplayCommand,
  } = installCommands;

  useEffect(() => {
    fetch("https://api.github.com/repos/jatinkrmalik/vocalinux")
      .then((res) => res.json())
      .then((data: { stargazers_count?: number }) => {
        if (data.stargazers_count) setStars(data.stargazers_count);
      })
      .catch(() => setStars(null));
  }, []);

  return (
    <main className="min-h-[100dvh] bg-background text-foreground">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(homeJsonLd) }}
      />

      {/* Nav */}
      <header className="fixed inset-x-0 top-0 z-50 border-b border-border/80 bg-background/85 backdrop-blur-md">
        <nav className="mx-auto flex h-14 max-w-6xl items-center justify-between px-4 sm:h-16 sm:px-6">
          <Link href="/" className="flex items-center gap-2.5">
            <VocalinuxLogo width={28} height={28} className="h-7 w-7" priority />
            <span className="text-[15px] font-semibold tracking-tight">
              Vocalinux
            </span>
          </Link>

          <div className="hidden items-center gap-7 md:flex">
            {navLinks.map((link) => (
              <a
                key={link.href}
                href={link.href}
                className="text-sm text-muted-foreground transition-colors hover:text-foreground"
              >
                {link.label}
              </a>
            ))}
            <a
              href="https://github.com/jatinkrmalik/vocalinux"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 text-sm text-muted-foreground transition-colors hover:text-foreground"
            >
              <Star className="h-3.5 w-3.5 fill-current" />
              {stars !== null ? stars.toLocaleString() : "GitHub"}
            </a>
            <ThemeToggle />
            <a
              href="#install"
              className="inline-flex h-9 items-center rounded-full bg-primary px-4 text-sm font-medium text-primary-foreground transition-transform active:scale-[0.98]"
            >
              Install
            </a>
          </div>

          <div className="flex items-center gap-2 md:hidden">
            <ThemeToggle />
            <button
              type="button"
              onClick={() => setMobileMenuOpen((v) => !v)}
              className="inline-flex h-9 w-9 items-center justify-center rounded-md border border-border"
              aria-label="Toggle menu"
              aria-expanded={mobileMenuOpen}
            >
              {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </button>
          </div>
        </nav>

        {mobileMenuOpen && (
          <div className="border-t border-border bg-background px-4 py-3 md:hidden">
            <div className="flex flex-col gap-1">
              {navLinks.map((link) => (
                <a
                  key={link.href}
                  href={link.href}
                  onClick={() => setMobileMenuOpen(false)}
                  className="rounded-md px-2 py-2.5 text-sm font-medium"
                >
                  {link.label}
                </a>
              ))}
              <a
                href="https://github.com/jatinkrmalik/vocalinux"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 rounded-md px-2 py-2.5 text-sm font-medium"
              >
                <Github className="h-4 w-4" />
                GitHub
              </a>
            </div>
          </div>
        )}
      </header>

      {/* Hero: asymmetric split */}
      <section className="relative overflow-hidden px-4 pb-16 pt-24 sm:px-6 sm:pb-20 sm:pt-28">
        <div
          className="pointer-events-none absolute inset-0 opacity-[0.55] dark:opacity-40"
          aria-hidden
          style={{
            background:
              "radial-gradient(60% 50% at 85% 20%, color-mix(in oklab, var(--primary) 18%, transparent), transparent 70%)",
          }}
        />
        <div className="relative mx-auto grid max-w-6xl items-center gap-10 lg:grid-cols-12 lg:gap-12">
          <motion.div
            className="lg:col-span-6"
            initial={reduce ? false : { opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.65, ease: [0.16, 1, 0.3, 1] }}
          >
            <p className="mb-5 font-mono text-[12px] uppercase tracking-[0.16em] text-primary">
              Offline on Linux
            </p>
            <h1 className="max-w-[14ch] text-[2.35rem] font-semibold leading-[1.08] tracking-[-0.03em] sm:text-5xl lg:text-[3.35rem]">
              Dictate into any app. Keep the audio home.
            </h1>
            <p className="mt-5 max-w-[36ch] text-base leading-relaxed text-muted-foreground sm:text-lg">
              System-wide voice typing with local models. X11 and Wayland. One
              install command.
            </p>
            <div className="mt-8 flex flex-wrap items-center gap-3">
              <a
                href="#install"
                className="inline-flex h-11 items-center justify-center rounded-full bg-primary px-6 text-sm font-semibold text-primary-foreground transition-transform active:scale-[0.98]"
              >
                Install Vocalinux
              </a>
              <a
                href="https://github.com/jatinkrmalik/vocalinux"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex h-11 items-center justify-center gap-2 rounded-full border border-border bg-background px-5 text-sm font-medium transition-colors hover:bg-muted"
              >
                <Github className="h-4 w-4" />
                Source
              </a>
            </div>
            <dl className="mt-10 grid grid-cols-2 gap-x-6 gap-y-4 border-t border-border pt-6 sm:grid-cols-4">
              {[
                ["Offline", "Local engines"],
                ["Display", "X11 + Wayland"],
                ["Default", "whisper.cpp"],
                ["License", "GPL-3.0"],
              ].map(([k, v]) => (
                <div key={k}>
                  <dt className="font-mono text-[11px] uppercase tracking-wider text-muted-foreground">
                    {k}
                  </dt>
                  <dd className="mt-1 text-sm font-medium">{v}</dd>
                </div>
              ))}
            </dl>
          </motion.div>

          <motion.div
            className="lg:col-span-6"
            initial={reduce ? false : { opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{
              duration: 0.7,
              delay: 0.08,
              ease: [0.16, 1, 0.3, 1],
            }}
          >
            <div className="relative">
              <div className="absolute -inset-3 rounded-2xl bg-primary/10 blur-2xl dark:bg-primary/15" aria-hidden />
              <figure className="relative overflow-hidden rounded-[12px] border border-border bg-card shadow-[0_24px_60px_-28px_rgba(0,0,0,0.45)]">
                <Image
                  src="/screenshots/00-transcription.png"
                  alt="Vocalinux tray overlay showing live speech transcription on Linux"
                  width={1280}
                  height={800}
                  priority
                  className="h-auto w-full"
                />
                <figcaption className="flex items-center justify-between border-t border-border px-4 py-3 text-xs text-muted-foreground">
                  <span>Live transcription overlay</span>
                  <Link
                    href="/screenshots/"
                    className="inline-flex items-center gap-1 font-medium text-foreground hover:text-primary"
                  >
                    More shots
                    <ChevronRight className="h-3.5 w-3.5" />
                  </Link>
                </figcaption>
              </figure>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Install strip */}
      <section id="install" className="border-y border-border bg-[#0a0a0c] px-4 py-14 text-zinc-100 sm:px-6 sm:py-16">
        <div className="mx-auto max-w-6xl">
          <div className="mb-8 grid gap-4 lg:grid-cols-12 lg:items-end">
            <div className="lg:col-span-7">
              <h2 className="text-2xl font-semibold tracking-tight sm:text-3xl">
                Install in one command
              </h2>
              <p className="mt-2 max-w-xl text-sm leading-relaxed text-zinc-400 sm:text-base">
                Interactive installer detects hardware, lets you pick an engine,
                and wires the desktop app.
              </p>
            </div>
            <p className="font-mono text-xs text-zinc-500 lg:col-span-5 lg:text-right">
              Ubuntu · Fedora · Debian · Arch · openSUSE
            </p>
          </div>
          <TerminalBlock
            command={interactiveInstallCommand}
            display={interactiveInstallDisplayCommand}
            label="install.sh --interactive"
          />
          <div className="mt-6 flex flex-wrap gap-x-6 gap-y-2 text-sm text-zinc-400">
            <span>Then launch: <code className="font-mono text-emerald-400">vocalinux</code></span>
            <Link href="/compare/" className="text-zinc-200 underline-offset-4 hover:underline">
              Compare engines
            </Link>
            <Link href="/install/" className="text-zinc-200 underline-offset-4 hover:underline">
              Distro notes
            </Link>
          </div>
        </div>
      </section>

      {/* Demo */}
      <section id="demo" className="px-4 py-16 sm:px-6 sm:py-20">
        <div className="mx-auto max-w-6xl">
          <Reveal>
            <div className="mb-8 max-w-2xl">
              <h2 className="text-3xl font-semibold tracking-tight sm:text-4xl">
                Try speech-to-text in the browser
              </h2>
              <p className="mt-3 text-muted-foreground">
                Browser preview when SpeechRecognition is available. The
                installed app runs offline on your machine.
              </p>
            </div>
          </Reveal>
          <Reveal delay={0.06}>
            <LiveDemo />
          </Reveal>
          <Reveal delay={0.1}>
            <div className="mt-10 grid gap-px overflow-hidden rounded-[12px] border border-border bg-border sm:grid-cols-3">
              {[
                {
                  title: "Toggle or push-to-talk",
                  body: "Double-tap or hold. Predictable control.",
                  href: "/shortcuts/",
                },
                {
                  title: "Engine choice",
                  body: "whisper.cpp, Whisper, VOSK, or Remote API.",
                  href: "/compare/",
                },
                {
                  title: "Audio cues",
                  body: "Optional tones when recording starts and stops.",
                  href: "/shortcuts/",
                },
              ].map((item) => (
                <Link
                  key={item.title}
                  href={item.href}
                  className="group bg-background p-5 transition-colors hover:bg-muted/60"
                >
                  <h3 className="text-sm font-semibold group-hover:text-primary">
                    {item.title}
                  </h3>
                  <p className="mt-1.5 text-sm text-muted-foreground">{item.body}</p>
                </Link>
              ))}
            </div>
          </Reveal>
        </div>
      </section>

      {/* Features bento */}
      <section id="features" className="border-t border-border bg-card/40 px-4 py-16 sm:px-6 sm:py-20">
        <div className="mx-auto max-w-6xl">
          <Reveal>
            <div className="mb-10 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
              <div>
                <h2 className="text-3xl font-semibold tracking-tight sm:text-4xl">
                  Built for real Linux desktops
                </h2>
                <p className="mt-3 max-w-xl text-muted-foreground">
                  Privacy, injection reliability, and engines that match your
                  hardware - not a cloud dashboard with a mic icon.
                </p>
              </div>
              <Link
                href="/screenshots/"
                className="inline-flex items-center gap-1 text-sm font-medium text-primary hover:underline"
              >
                App screenshots
                <ChevronRight className="h-4 w-4" />
              </Link>
            </div>
          </Reveal>

          <div className="grid gap-4 lg:grid-cols-12">
            <Reveal className="lg:col-span-7">
              <figure className="overflow-hidden rounded-[12px] border border-border bg-background">
                <Image
                  src="/screenshots/settings-speech-engine.png"
                  alt="Vocalinux settings dialog showing speech engine options"
                  width={1200}
                  height={800}
                  className="h-auto w-full"
                />
                <figcaption className="border-t border-border px-4 py-3 text-sm text-muted-foreground">
                  Engine and model controls in the settings GUI
                </figcaption>
              </figure>
            </Reveal>

            <div className="grid gap-4 sm:grid-cols-2 lg:col-span-5 lg:grid-cols-1">
              {featureRows.slice(0, 3).map((f, i) => (
                <Reveal key={f.title} delay={0.04 * i}>
                  <Link
                    href={f.href}
                    className="group flex h-full flex-col justify-between rounded-[12px] border border-border bg-background p-5 transition-colors hover:border-primary/40"
                  >
                    <div>
                      <h3 className="text-base font-semibold">{f.title}</h3>
                      <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                        {f.body}
                      </p>
                    </div>
                    <span className="mt-4 inline-flex items-center gap-1 text-sm font-medium text-primary">
                      {f.link}
                      <ChevronRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5" />
                    </span>
                  </Link>
                </Reveal>
              ))}
            </div>

            <div className="grid gap-4 sm:grid-cols-3 lg:col-span-12">
              {featureRows.slice(3).map((f, i) => (
                <Reveal key={f.title} delay={0.04 * i}>
                  <Link
                    href={f.href}
                    className="group block h-full rounded-[12px] border border-border bg-background p-5 transition-colors hover:border-primary/40"
                  >
                    <h3 className="text-base font-semibold">{f.title}</h3>
                    <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                      {f.body}
                    </p>
                    <span className="mt-4 inline-flex items-center gap-1 text-sm font-medium text-primary">
                      {f.link}
                      <ChevronRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5" />
                    </span>
                  </Link>
                </Reveal>
              ))}
            </div>

            <Reveal className="lg:col-span-5">
              <figure className="h-full overflow-hidden rounded-[12px] border border-border bg-background">
                <Image
                  src="/screenshots/02-system-tray.png"
                  alt="Vocalinux system tray icon and menu"
                  width={900}
                  height={700}
                  className="h-auto w-full object-cover"
                />
                <figcaption className="border-t border-border px-4 py-3 text-sm text-muted-foreground">
                  Tray status while you work
                </figcaption>
              </figure>
            </Reveal>
            <Reveal className="lg:col-span-7" delay={0.06}>
              <div className="flex h-full flex-col justify-between rounded-[12px] border border-border bg-background p-6 sm:p-8">
                <div>
                  <h3 className="text-2xl font-semibold tracking-tight">
                    The Linux voice gap, closed
                  </h3>
                  <p className="mt-3 max-w-prose text-muted-foreground">
                    macOS and Windows shipped system dictation years ago. Linux
                    users got fragments. Vocalinux is the full desktop path:
                    tray, hotkeys, injection, and local models.
                  </p>
                </div>
                <ul className="mt-8 grid gap-3 sm:grid-cols-2">
                  {[
                    "No cloud dependency for local engines",
                    "Works across apps, not one editor",
                    "Guided install, not a research project",
                    "Open source you can audit",
                  ].map((item) => (
                    <li key={item} className="flex items-start gap-2 text-sm">
                      <Check className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </Reveal>
          </div>
        </div>
      </section>

      {/* How it works - real sequence, numbers ok */}
      <section className="px-4 py-16 sm:px-6 sm:py-20">
        <div className="mx-auto max-w-6xl">
          <Reveal>
            <h2 className="text-3xl font-semibold tracking-tight sm:text-4xl">
              From install to first sentence
            </h2>
          </Reveal>
          <ol className="mt-10 grid gap-0 border-t border-border md:grid-cols-3">
            {[
              {
                n: "1",
                title: "Run the installer",
                body: "One curl. It pulls dependencies, models, and desktop integration.",
              },
              {
                n: "2",
                title: "Pick an engine",
                body: "Default whisper.cpp, or Whisper, VOSK, or a remote server you control.",
              },
              {
                n: "3",
                title: "Hold or toggle",
                body: "Activate the shortcut, speak, and text lands in the focused field.",
              },
            ].map((step, i) => (
              <Reveal key={step.n} delay={0.05 * i}>
                <li className="border-b border-border py-8 md:border-b-0 md:border-r md:px-6 md:py-10 md:first:pl-0 md:last:border-r-0 md:last:pr-0">
                  <span className="font-mono text-sm text-primary">{step.n}</span>
                  <h3 className="mt-3 text-xl font-semibold">{step.title}</h3>
                  <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                    {step.body}
                  </p>
                </li>
              </Reveal>
            ))}
          </ol>
        </div>
      </section>

      {/* Install details */}
      <section className="border-t border-border bg-card/40 px-4 py-16 sm:px-6 sm:py-20">
        <div className="mx-auto max-w-6xl">
          <div className="grid gap-10 lg:grid-cols-12">
            <Reveal className="lg:col-span-5">
              <h2 className="text-3xl font-semibold tracking-tight sm:text-4xl">
                What the installer does
              </h2>
              <ul className="mt-6 space-y-3 text-sm text-muted-foreground">
                {[
                  "Installs system dependencies",
                  "Creates an isolated virtual environment",
                  "Downloads speech models for your choice",
                  "Sets up desktop integration and PATH",
                  "Creates an application launcher",
                ].map((item) => (
                  <li key={item} className="flex items-start gap-2">
                    <Check className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
                    {item}
                  </li>
                ))}
              </ul>
              <div className="mt-8 rounded-[12px] border border-border bg-background p-5">
                <h3 className="text-sm font-semibold">System requirements</h3>
                <ul className="mt-3 space-y-1.5 text-sm text-muted-foreground">
                  <li>Ubuntu, Debian, Fedora, Arch, openSUSE, or equivalent</li>
                  <li>Python 3.9+ with GTK 3 / PyGObject</li>
                  <li>4GB RAM min · 8GB+ for larger models</li>
                  <li>Microphone + X11 or Wayland session</li>
                  <li>Optional Vulkan GPU for acceleration</li>
                </ul>
              </div>
            </Reveal>
            <Reveal className="space-y-6 lg:col-span-7" delay={0.06}>
              <div>
                <h3 className="mb-3 text-sm font-semibold">Uninstall</h3>
                <TerminalBlock
                  command={uninstallCommand}
                  display={uninstallDisplayCommand}
                  label="uninstall.sh"
                />
              </div>
              <div className="overflow-hidden rounded-[12px] border border-border bg-background">
                <Image
                  src="/screenshots/settings-general.png"
                  alt="Vocalinux general settings panel"
                  width={1100}
                  height={720}
                  className="h-auto w-full"
                />
              </div>
            </Reveal>
          </div>
        </div>
      </section>

      {/* Guides */}
      <section id="guides" className="px-4 py-16 sm:px-6 sm:py-20">
        <div className="mx-auto max-w-6xl">
          <Reveal>
            <h2 className="text-3xl font-semibold tracking-tight sm:text-4xl">
              Distro guides
            </h2>
            <p className="mt-3 max-w-2xl text-muted-foreground">
              Setup notes written for real desktop sessions, with post-install
              checks.
            </p>
          </Reveal>
          <div className="mt-8 grid gap-4 md:grid-cols-3">
            {[
              {
                href: "/install/ubuntu/",
                title: "Ubuntu",
                body: "GNOME, KDE, X11, and Wayland on 22.04+.",
              },
              {
                href: "/install/fedora/",
                title: "Fedora",
                body: "Workstation-focused notes for a stable dictation flow.",
              },
              {
                href: "/install/arch/",
                title: "Arch",
                body: "Arch, Manjaro, EndeavourOS with injection checks.",
              },
            ].map((g, i) => (
              <Reveal key={g.href} delay={0.04 * i}>
                <Link
                  href={g.href}
                  className="group flex h-full flex-col rounded-[12px] border border-border p-6 transition-colors hover:border-primary/40 hover:bg-card/60"
                >
                  <h3 className="text-lg font-semibold">{g.title}</h3>
                  <p className="mt-2 flex-1 text-sm text-muted-foreground">
                    {g.body}
                  </p>
                  <span className="mt-4 inline-flex items-center gap-1 text-sm font-medium text-primary">
                    Read guide
                    <ChevronRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5" />
                  </span>
                </Link>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      {/* Engines - dense list, one accent */}
      <section className="border-t border-border bg-card/40 px-4 py-16 sm:px-6 sm:py-20">
        <div className="mx-auto max-w-6xl">
          <Reveal>
            <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
              <div>
                <h2 className="text-3xl font-semibold tracking-tight sm:text-4xl">
                  Speech engines
                </h2>
                <p className="mt-3 max-w-xl text-muted-foreground">
                  Match latency, footprint, and privacy boundary to your
                  hardware.
                </p>
              </div>
              <Link
                href="/compare/"
                className="inline-flex items-center gap-1 text-sm font-medium text-primary hover:underline"
              >
                Full comparison
                <ChevronRight className="h-4 w-4" />
              </Link>
            </div>
          </Reveal>
          <div className="mt-10 divide-y divide-border border-y border-border">
            {engines.map((engine, i) => (
              <Reveal key={engine.name} delay={0.03 * i}>
                <div className="grid gap-4 py-7 md:grid-cols-12 md:items-start">
                  <div className="md:col-span-3">
                    <div className="flex flex-wrap items-center gap-2">
                      <h3 className="text-lg font-semibold">{engine.name}</h3>
                      {engine.badge && (
                        <span className="rounded-full bg-primary/15 px-2 py-0.5 font-mono text-[11px] font-medium text-primary">
                          {engine.badge}
                        </span>
                      )}
                    </div>
                  </div>
                  <p className="text-sm text-muted-foreground md:col-span-4">
                    {engine.summary}
                  </p>
                  <ul className="space-y-1.5 text-sm md:col-span-5">
                    {engine.points.map((p) => (
                      <li key={p} className="flex items-start gap-2">
                        <Check className="mt-0.5 h-3.5 w-3.5 shrink-0 text-primary" />
                        {p}
                      </li>
                    ))}
                  </ul>
                </div>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section id="faq" className="px-4 py-16 sm:px-6 sm:py-20">
        <div className="mx-auto max-w-3xl">
          <Reveal>
            <h2 className="text-3xl font-semibold tracking-tight sm:text-4xl">
              Questions
            </h2>
          </Reveal>
          <div className="mt-8 divide-y divide-border border-y border-border">
            {faqItems.map((item) => (
              <details key={item.question} className="group py-1">
                <summary className="flex cursor-pointer list-none items-center justify-between gap-4 py-5 text-left font-medium">
                  <span>{item.question}</span>
                  <ChevronRight className="h-4 w-4 shrink-0 text-muted-foreground transition-transform group-open:rotate-90" />
                </summary>
                <div className="pb-5 pr-8 text-sm leading-relaxed text-muted-foreground">
                  {item.answer}
                </div>
              </details>
            ))}
          </div>
        </div>
      </section>

      {/* Ecosystem */}
      <section id="ecosystem" className="border-t border-border bg-card/40 px-4 py-16 sm:px-6 sm:py-20">
        <div className="mx-auto max-w-6xl">
          <Reveal>
            <h2 className="text-3xl font-semibold tracking-tight sm:text-4xl">
              The Voca family
            </h2>
            <p className="mt-3 text-muted-foreground">
              Same privacy idea, platform-native implementations.
            </p>
          </Reveal>
          <div className="mt-8 grid gap-4 md:grid-cols-3">
            {[
              {
                name: "VocaMac",
                status: "Beta",
                body: "Native macOS menu bar app with WhisperKit and CoreML on Apple Silicon.",
                primary: { href: "https://vocamac.com", label: "Website" },
                secondary: {
                  href: "https://github.com/jatinkrmalik/vocamac",
                  label: "GitHub",
                },
                current: false,
              },
              {
                name: "VocaLinux",
                status: "You are here",
                body: "Tray app for Linux with whisper.cpp, Vulkan, and full offline support.",
                primary: { href: "#install", label: "Install" },
                secondary: {
                  href: "https://github.com/jatinkrmalik/vocalinux",
                  label: "GitHub",
                },
                current: true,
              },
              {
                name: "VocaWin",
                status: "Coming soon",
                body: "Windows port of the same offline dictation approach.",
                primary: null,
                secondary: null,
                current: false,
              },
            ].map((p, i) => (
              <Reveal key={p.name} delay={0.04 * i}>
                <div
                  className={`flex h-full flex-col rounded-[12px] border p-6 ${
                    p.current
                      ? "border-primary bg-background"
                      : "border-border bg-background"
                  }`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <h3 className="text-lg font-semibold">{p.name}</h3>
                    <span className="font-mono text-[11px] text-muted-foreground">
                      {p.status}
                    </span>
                  </div>
                  <p className="mt-3 flex-1 text-sm text-muted-foreground">
                    {p.body}
                  </p>
                  {(p.primary || p.secondary) && (
                    <div className="mt-5 flex gap-2">
                      {p.primary && (
                        <a
                          href={p.primary.href}
                          target={
                            p.primary.href.startsWith("http")
                              ? "_blank"
                              : undefined
                          }
                          rel={
                            p.primary.href.startsWith("http")
                              ? "noopener noreferrer"
                              : undefined
                          }
                          className="inline-flex h-9 items-center rounded-full bg-primary px-4 text-sm font-medium text-primary-foreground"
                        >
                          {p.primary.label}
                        </a>
                      )}
                      {p.secondary && (
                        <a
                          href={p.secondary.href}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex h-9 items-center rounded-full border border-border px-4 text-sm font-medium"
                        >
                          {p.secondary.label}
                        </a>
                      )}
                    </div>
                  )}
                </div>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border px-4 py-12 sm:px-6">
        <div className="mx-auto flex max-w-6xl flex-col gap-8 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <div className="flex items-center gap-2">
              <VocalinuxLogo width={24} height={24} className="h-6 w-6" />
              <span className="font-semibold">Vocalinux</span>
            </div>
            <p className="mt-3 max-w-xs text-sm text-muted-foreground">
              Offline voice dictation for Linux. Free and open source.
            </p>
          </div>
          <div className="grid grid-cols-2 gap-8 text-sm sm:grid-cols-3">
            <div>
              <p className="font-medium">Product</p>
              <ul className="mt-3 space-y-2 text-muted-foreground">
                <li>
                  <a href="#install" className="hover:text-foreground">
                    Install
                  </a>
                </li>
                <li>
                  <Link href="/screenshots/" className="hover:text-foreground">
                    Screenshots
                  </Link>
                </li>
                <li>
                  <Link href="/compare/" className="hover:text-foreground">
                    Engines
                  </Link>
                </li>
                <li>
                  <Link href="/changelog/" className="hover:text-foreground">
                    Changelog
                  </Link>
                </li>
              </ul>
            </div>
            <div>
              <p className="font-medium">Guides</p>
              <ul className="mt-3 space-y-2 text-muted-foreground">
                <li>
                  <Link href="/install/ubuntu/" className="hover:text-foreground">
                    Ubuntu
                  </Link>
                </li>
                <li>
                  <Link href="/wayland/" className="hover:text-foreground">
                    Wayland
                  </Link>
                </li>
                <li>
                  <Link href="/troubleshooting/" className="hover:text-foreground">
                    Troubleshooting
                  </Link>
                </li>
                <li>
                  <Link href="/faq/" className="hover:text-foreground">
                    FAQ
                  </Link>
                </li>
              </ul>
            </div>
            <div>
              <p className="font-medium">Project</p>
              <ul className="mt-3 space-y-2 text-muted-foreground">
                <li>
                  <a
                    href="https://github.com/jatinkrmalik/vocalinux"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="hover:text-foreground"
                  >
                    GitHub
                  </a>
                </li>
                <li>
                  <Link href="/open-source/" className="hover:text-foreground">
                    Open source
                  </Link>
                </li>
                <li>
                  <Link href="/privacy/" className="hover:text-foreground">
                    Privacy
                  </Link>
                </li>
              </ul>
            </div>
          </div>
        </div>
        <div className="mx-auto mt-10 max-w-6xl border-t border-border pt-6 text-xs text-muted-foreground">
          GPL-3.0 · Maintained by{" "}
          <a
            href="https://github.com/jatinkrmalik"
            target="_blank"
            rel="noopener noreferrer"
            className="text-foreground hover:underline"
          >
            Jatin K Malik
          </a>
        </div>
      </footer>
    </main>
  );
}
