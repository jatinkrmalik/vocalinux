"use client";

import React, { useState, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
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
  Sparkles,
  Heart,
} from "lucide-react";
import { ThemeToggle } from "@/components/theme-toggle";
import { VocalinuxLogo } from "@/components/optimized-image";
import { useInView } from "react-intersection-observer";

// The one-liner install command (split into three lines for display)
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
    softwareVersion: "0.14.0-beta",
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
          text: "Yes! v0.10.1+ preserves your XKB keyboard layout when activating IBus, so you won't unexpectedly switch to US layout mid-dictation.",
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

const FeatureCard = ({
  icon,
  title,
  description,
  href,
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
  href?: string;
}) => {
  const [ref, inView] = useInView({
    triggerOnce: true,
    threshold: 0.1,
  });

  const card = (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 20 }}
      animate={inView ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
      transition={{ duration: 0.5 }}
      className={`flex h-full flex-col rounded-xl border border-zinc-100 bg-white p-6 shadow-md transition-all hover:shadow-xl dark:border-zinc-700 dark:bg-zinc-800 ${href ? "group cursor-pointer" : ""}`}
    >
      <div className="mb-4 flex items-center gap-4">
        <div className="bg-primary/10 rounded-lg p-3">{icon}</div>
        <h3 className="text-lg font-semibold sm:text-xl">{title}</h3>
      </div>
      <p className="flex-1 text-sm text-muted-foreground sm:text-base">
        {description}
      </p>
      {href && (
        <div className="mt-4 flex items-center gap-1 text-sm font-medium text-primary group-hover:underline">
          Learn more{" "}
          <ChevronRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5" />
        </div>
      )}
    </motion.div>
  );

  if (href) {
    return <Link href={href}>{card}</Link>;
  }
  return card;
};

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
      className={`flex items-center gap-2 rounded bg-zinc-700 px-3 py-1.5 text-sm text-white transition-all hover:bg-zinc-600 ${className}`}
      aria-label={copied ? "Copied to clipboard" : "Copy to clipboard"}
    >
      {copied ? (
        <>
          <Check className="h-4 w-4" />
          Copied!
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

const FadeInSection = ({
  children,
  delay = 0,
}: {
  children: React.ReactNode;
  delay?: number;
}) => {
  const [ref, inView] = useInView({
    triggerOnce: true,
    threshold: 0.1,
    rootMargin: "0px 0px -50px 0px",
  });
  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 20 }}
      animate={inView ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
      transition={{ duration: 0.5, delay }}
      className="w-full"
    >
      {children}
    </motion.div>
  );
};

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
        // Fallback if API fails
        setStars(null);
      });
  }, []);

  const navLinks = [
    { href: "#demo", label: "Demo" },
    { href: "#features", label: "Features" },
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
    <main className="min-h-screen bg-gradient-to-b from-zinc-50 to-white dark:from-zinc-900 dark:to-zinc-950">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(homeJsonLd) }}
      />

      {/* Header */}
      <header className="bg-background/80 fixed left-0 right-0 top-0 z-50 border-b border-border backdrop-blur-md">
        <nav className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6">
          <Link href="/" className="group flex items-center gap-2">
            <VocalinuxLogo
              width={32}
              height={32}
              className="h-7 w-7 transition-transform group-hover:scale-110 sm:h-8 sm:w-8"
              priority
            />
            <span className="text-lg font-bold sm:text-xl">Vocalinux</span>
            <span className="from-primary/20 border-primary/30 shadow-primary/20 hidden rounded-full border bg-gradient-to-r to-green-500/20 px-2.5 py-1 text-xs font-semibold text-primary shadow-sm sm:inline-block">
              v0.14.0 Beta
            </span>
          </Link>

          {/* Desktop navigation */}
          <div className="hidden items-center gap-6 md:flex">
            {navLinks.map((link) => (
              <a
                key={link.href}
                href={link.href}
                className="text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
              >
                {link.label}
              </a>
            ))}
            <a
              href="https://github.com/jatinkrmalik/vocalinux"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 text-muted-foreground transition-colors hover:text-foreground"
            >
              <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
              {stars !== null && (
                <span className="rounded-full bg-zinc-100 px-2 py-0.5 text-xs font-medium dark:bg-zinc-800">
                  {stars.toLocaleString()}
                </span>
              )}
            </a>
            <ThemeToggle />
          </div>

          {/* Mobile navigation toggle */}
          <div className="flex items-center gap-3 md:hidden">
            <ThemeToggle />
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 text-foreground focus:outline-none"
              aria-label="Toggle menu"
            >
              {mobileMenuOpen ? (
                <X className="h-6 w-6" />
              ) : (
                <Menu className="h-6 w-6" />
              )}
            </button>
          </div>
        </nav>

        {/* Mobile menu */}
        <motion.div
          initial={{ height: 0, opacity: 0 }}
          animate={{
            height: mobileMenuOpen ? "auto" : 0,
            opacity: mobileMenuOpen ? 1 : 0,
          }}
          transition={{ duration: 0.3 }}
          className="overflow-hidden border-b border-border bg-background md:hidden"
        >
          <div className="space-y-2 px-4 py-3">
            {navLinks.map((link) => (
              <a
                key={link.href}
                href={link.href}
                className="block py-2 text-foreground transition-colors hover:text-primary"
                onClick={() => setMobileMenuOpen(false)}
              >
                {link.label}
              </a>
            ))}
            <a
              href="https://github.com/jatinkrmalik/vocalinux"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 py-2 text-foreground transition-colors hover:text-primary"
              onClick={() => setMobileMenuOpen(false)}
            >
              <Github className="h-5 w-5" />
              GitHub
            </a>
          </div>
        </motion.div>
      </header>

      {/* Hero Section */}
      <section className="relative overflow-hidden px-4 pb-16 pt-28 sm:px-6 sm:pb-24 sm:pt-36">
        <div className="from-primary/5 dark:from-primary/10 absolute inset-0 bg-gradient-to-br via-transparent to-cyan-500/5 dark:to-cyan-500/10" />

        {/* Full-width shifting wave gradient */}
        <div className="pointer-events-none absolute inset-0 overflow-hidden [mask-image:linear-gradient(to_bottom,transparent,black_10%,black_84%,transparent)]">
          <div className="absolute inset-0 bg-white/[0.015] backdrop-blur-[1px] dark:bg-white/[0.008]" />
          <motion.div
            className="absolute inset-x-[-18%] top-[-12%] h-[90%] mix-blend-multiply blur-3xl dark:hidden"
            style={{
              background:
                "radial-gradient(70% 48% at 16% 46%, hsl(var(--primary) / 0.28), transparent 64%), radial-gradient(64% 44% at 82% 44%, rgb(6 182 212 / 0.3), transparent 66%), linear-gradient(105deg, transparent 8%, rgb(20 184 166 / 0.2) 36%, rgb(6 182 212 / 0.24) 55%, transparent 86%)",
              backgroundSize: "170% 170%",
            }}
            animate={{
              backgroundPosition: ["0% 46%", "100% 54%", "0% 46%"],
              opacity: [0.82, 1, 0.82],
            }}
            transition={{ duration: 18, repeat: Infinity, ease: "easeInOut" }}
          />
          <motion.div
            className="absolute inset-x-[-18%] top-[-12%] hidden h-[90%] blur-3xl dark:block"
            style={{
              background:
                "radial-gradient(70% 48% at 16% 46%, hsl(var(--primary) / 0.13), transparent 68%), radial-gradient(64% 44% at 82% 44%, rgb(6 182 212 / 0.13), transparent 70%), linear-gradient(105deg, transparent 8%, rgb(20 184 166 / 0.08) 36%, rgb(6 182 212 / 0.1) 55%, transparent 86%)",
              backgroundSize: "170% 170%",
            }}
            animate={{
              backgroundPosition: ["0% 46%", "100% 54%", "0% 46%"],
              opacity: [0.58, 0.82, 0.58],
            }}
            transition={{ duration: 18, repeat: Infinity, ease: "easeInOut" }}
          />
          <motion.div
            className="absolute inset-x-[-12%] top-[16%] h-[52%] mix-blend-multiply blur-2xl dark:hidden"
            style={{
              background:
                "linear-gradient(100deg, transparent 4%, hsl(var(--primary) / 0.34) 30%, rgb(20 184 166 / 0.3) 48%, rgb(6 182 212 / 0.34) 68%, transparent 94%)",
              clipPath:
                "polygon(0 44%, 10% 36%, 24% 43%, 39% 34%, 55% 42%, 72% 32%, 88% 39%, 100% 34%, 100% 72%, 86% 65%, 70% 73%, 54% 63%, 38% 72%, 22% 62%, 8% 69%, 0 64%)",
            }}
            animate={{
              x: ["-4%", "4%", "-4%"],
              y: [0, -16, 0],
              opacity: [0.84, 1, 0.84],
              scale: [1, 1.05, 1],
            }}
            transition={{ duration: 15, repeat: Infinity, ease: "easeInOut" }}
          />
          <motion.div
            className="absolute inset-x-[-12%] top-[16%] hidden h-[52%] blur-3xl dark:block"
            style={{
              background:
                "linear-gradient(100deg, transparent 4%, hsl(var(--primary) / 0.13) 30%, rgb(20 184 166 / 0.12) 48%, rgb(6 182 212 / 0.14) 68%, transparent 94%)",
              clipPath:
                "polygon(0 44%, 10% 36%, 24% 43%, 39% 34%, 55% 42%, 72% 32%, 88% 39%, 100% 34%, 100% 72%, 86% 65%, 70% 73%, 54% 63%, 38% 72%, 22% 62%, 8% 69%, 0 64%)",
            }}
            animate={{
              x: ["-4%", "4%", "-4%"],
              y: [0, -16, 0],
              opacity: [0.54, 0.76, 0.54],
              scale: [1, 1.05, 1],
            }}
            transition={{ duration: 15, repeat: Infinity, ease: "easeInOut" }}
          />
        </div>

        <div className="relative mx-auto max-w-7xl">
          <div className="mx-auto max-w-4xl text-center">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
            >
              {/* Badge */}
              <div className="bg-primary/10 mb-6 inline-flex items-center gap-2 rounded-full px-4 py-2">
                <Sparkles className="h-4 w-4 text-primary" />
                <span className="text-sm font-medium text-primary">
                  Beta Release: Try it now!
                </span>
              </div>

              <h1 className="mb-6 text-4xl font-bold tracking-tight sm:text-5xl md:text-6xl lg:text-7xl">
                Voice Dictation for Linux,{" "}
                <motion.span
                  className="inline-block bg-gradient-to-r from-primary via-teal-500 to-cyan-600 bg-clip-text text-transparent"
                  style={{
                    backgroundSize: "220% 100%",
                  }}
                  animate={{
                    backgroundPosition: ["0% 50%", "100% 50%", "0% 50%"],
                  }}
                  transition={{
                    duration: 14,
                    repeat: Infinity,
                    ease: "easeInOut",
                  }}
                >
                  Finally Done Right
                </motion.span>
              </h1>

              <p className="mx-auto mb-2 max-w-3xl text-lg text-muted-foreground sm:text-xl md:text-2xl">
                100% offline voice dictation for Linux.
              </p>
              <p className="mx-auto mb-8 max-w-3xl text-lg text-muted-foreground sm:text-xl md:text-2xl">
                Use toggle mode or push-to-talk and start speaking.
              </p>

              {/* CTA Buttons */}
              <div className="mb-12 flex flex-col justify-center gap-4 sm:flex-row">
                <a
                  href="#install"
                  className="hover:bg-primary/90 shadow-primary/25 inline-flex items-center justify-center gap-2 rounded-xl bg-primary px-8 py-4 text-lg font-semibold text-white shadow-lg transition-all hover:scale-105 dark:text-zinc-900"
                >
                  <Download className="h-5 w-5" />
                  Install Now
                </a>
                <a
                  href="https://github.com/jatinkrmalik/vocalinux"
                  target="_blank"
                  rel="noopener noreferrer"
                  aria-label="View Vocalinux source code on GitHub (opens in a new tab)"
                  className="inline-flex items-center justify-center gap-2 rounded-xl border border-zinc-700 bg-zinc-900 px-8 py-4 text-lg font-semibold text-white transition-all hover:scale-105 hover:bg-zinc-800 hover:shadow-md dark:border-zinc-300 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-white"
                >
                  <Github className="h-5 w-5" />
                  We&apos;re Open Source
                </a>
                <a
                  href="#ecosystem"
                  className="inline-flex items-center justify-center gap-2 rounded-xl border border-zinc-300 px-8 py-4 text-lg font-semibold text-zinc-600 transition-all hover:border-zinc-500 hover:text-zinc-900 hover:shadow-sm dark:border-zinc-600 dark:text-zinc-400 dark:hover:border-zinc-400 dark:hover:text-zinc-200"
                >
                  <Laptop className="h-5 w-5" />
                  Use Windows or Mac?
                </a>
              </div>
            </motion.div>

            {/* One-Click Install Box - Redesigned */}
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
              className="mx-auto w-full max-w-6xl px-4"
            >
              <div className="rounded-2xl border border-zinc-800/50 bg-gradient-to-br from-zinc-900 to-zinc-950 p-6 shadow-2xl backdrop-blur sm:p-8">
                {/* Header */}
                <div className="mb-5 flex items-center gap-3">
                  <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full bg-green-500/20">
                    <Terminal className="h-5 w-5 text-green-400" />
                  </div>
                  <div className="text-left">
                    <h2 className="text-left text-lg font-semibold text-white">
                      Quick Install (Interactive)
                    </h2>
                    <p className="text-left text-xs text-zinc-400">
                      Guided installation with hardware detection
                    </p>
                  </div>
                </div>

                {/* Command box */}
                <div className="overflow-hidden rounded-xl border border-zinc-800 bg-zinc-950/80">
                  <div className="flex items-center justify-between border-b border-zinc-800 bg-zinc-900/50 px-4 py-2.5">
                    <div className="flex items-center gap-2">
                      <div className="h-2.5 w-2.5 rounded-full bg-red-500/70" />
                      <div className="h-2.5 w-2.5 rounded-full bg-yellow-500/70" />
                      <div className="h-2.5 w-2.5 rounded-full bg-green-500/70" />
                    </div>
                    <CopyButton text={interactiveInstallCommand} />
                  </div>
                  <div className="p-4 sm:p-5">
                    <pre className="whitespace-pre-wrap text-left font-mono text-sm text-green-400 sm:text-base">
                      <span className="select-none text-zinc-500">$ </span>
                      {interactiveInstallDisplayCommand}
                    </pre>
                  </div>
                </div>

                {/* Bottom info */}
                <div className="mt-5 flex flex-col gap-3 border-t border-zinc-800/50 pt-5 sm:flex-row sm:items-center sm:justify-between">
                  <p className="text-sm text-zinc-400">
                    <span className="text-zinc-500">Compatible:</span> Ubuntu,
                    Fedora, Debian, Arch, openSUSE &amp; more
                  </p>
                  <div className="flex items-center gap-4 text-xs text-zinc-500">
                    <span className="flex items-center gap-1.5">
                      <CheckCircle2 className="h-3.5 w-3.5 text-green-500" />
                      Guided setup
                    </span>
                    <span className="flex items-center gap-1.5">
                      <Zap className="h-3.5 w-3.5 text-green-500" />
                      ~1-2 min default
                    </span>
                  </div>
                </div>

                {/* Tech stack info */}
                <div className="mt-4 flex flex-wrap items-center justify-center gap-4 border-t border-zinc-800/30 pt-4 text-xs text-zinc-400 sm:gap-6">
                  <span className="flex items-center gap-1.5">
                    <Zap className="h-3.5 w-3.5 text-yellow-500" />
                    <strong className="text-zinc-300">whisper.cpp</strong>{" "}
                    default
                  </span>
                  <span className="flex items-center gap-1.5">
                    <Cpu className="h-3.5 w-3.5 text-blue-500" />
                    Vulkan GPU ready
                  </span>
                  <span className="flex items-center gap-1.5">
                    <Settings className="h-3.5 w-3.5 text-purple-500" />
                    Interactive engine choice
                  </span>
                </div>
              </div>
            </motion.div>

            {/* Trust indicators */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.6, delay: 0.4 }}
              className="mt-12 flex flex-wrap items-center justify-center gap-6 text-sm text-muted-foreground sm:gap-10"
            >
              <div className="flex items-center gap-2">
                <Shield className="h-5 w-5 text-green-500" />
                <span>100% Offline</span>
              </div>
              <div className="flex items-center gap-2">
                <Lock className="h-5 w-5 text-blue-500" />
                <span>No Telemetry</span>
              </div>
              <div className="flex items-center gap-2">
                <Activity className="h-5 w-5 text-purple-500" />
                <span>Local Models</span>
              </div>
              <div className="flex items-center gap-2">
                <Globe className="h-5 w-5 text-orange-500" />
                <span>X11 &amp; Wayland</span>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Demo Section - Live Interactive Demo */}
      <section
        id="demo"
        className="bg-zinc-50 px-4 py-16 dark:bg-zinc-900/50 sm:px-6 sm:py-24"
      >
        <div className="mx-auto max-w-6xl">
          <FadeInSection>
            <div className="mb-12 text-center">
              <h2 className="mb-4 text-3xl font-bold sm:text-4xl md:text-5xl">
                Try a Speech-to-Text Preview in Your Browser
              </h2>
              <p className="mx-auto max-w-2xl text-lg text-muted-foreground">
                This preview runs when your browser exposes SpeechRecognition.
                Vocalinux itself runs offline after install.
              </p>
            </div>
          </FadeInSection>

          <FadeInSection delay={0.1}>
            <LiveDemo />
          </FadeInSection>

          {/* Key demo points */}
          <FadeInSection delay={0.2}>
            <div className="mt-12 grid grid-cols-1 gap-6 md:grid-cols-3">
              {[
                {
                  icon: <Keyboard className="h-6 w-6 text-primary" />,
                  title: "Flexible Shortcut Modes",
                  description:
                    "Use toggle mode (double-tap) or push-to-talk mode to dictate anywhere",
                  href: "/shortcuts/",
                },
                {
                  icon: <Zap className="h-6 w-6 text-primary" />,
                  title: "Real-time Transcription",
                  description:
                    "Compare engines and model choices for low-latency dictation",
                  href: "/compare/",
                },
                {
                  icon: <Volume2 className="h-6 w-6 text-primary" />,
                  title: "Audio Feedback",
                  description:
                    "Use sound effects to know when recording starts and stops",
                  href: "/shortcuts/",
                },
              ].map((item, i) => (
                <Link
                  key={i}
                  href={item.href}
                  className="hover:border-primary/50 hover:bg-primary/5 dark:hover:border-primary/50 dark:hover:bg-primary/10 group flex items-start gap-4 rounded-xl border border-zinc-200 bg-white p-4 transition-colors dark:border-zinc-700 dark:bg-zinc-800"
                >
                  <div className="bg-primary/10 rounded-lg p-2">
                    {item.icon}
                  </div>
                  <div>
                    <h3 className="mb-1 inline-flex items-center gap-1 font-semibold">
                      {item.title}
                      <ChevronRight className="h-4 w-4 text-primary opacity-0 transition-opacity group-hover:opacity-100" />
                    </h3>
                    <p className="text-sm text-muted-foreground">
                      {item.description}
                    </p>
                  </div>
                </Link>
              ))}
            </div>
          </FadeInSection>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="px-4 py-16 sm:px-6 sm:py-24">
        <div className="mx-auto max-w-7xl">
          <FadeInSection>
            <div className="mb-16 text-center">
              <h2 className="mb-4 text-3xl font-bold sm:text-4xl md:text-5xl">
                Offline Voice Dictation Features for Linux
              </h2>
              <p className="mx-auto max-w-3xl text-lg text-muted-foreground">
                Finally, Linux users get the voice dictation experience they
                deserve. no compromises on privacy, no cloud dependencies, just
                pure productivity.
              </p>
            </div>
          </FadeInSection>

          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
            <FeatureCard
              icon={<Shield className="h-6 w-6 text-primary" />}
              title="100% Offline & Private"
              description="All processing happens on your machine. Your voice data never leaves your computer. Complete privacy guaranteed."
              href="/offline/"
            />
            <FeatureCard
              icon={<Laptop className="h-6 w-6 text-primary" />}
              title="Universal App Support"
              description="Works everywhere: terminals, browsers, IDEs, office apps, and any text input field on your Linux system."
              href="/use-cases/"
            />
            <FeatureCard
              icon={<Zap className="h-6 w-6 text-primary" />}
              title="Blazing Fast"
              description="whisper.cpp brings C++ optimized inference with Vulkan GPU support. Works with AMD, Intel, and NVIDIA GPUs!"
              href="/gpu-acceleration/"
            />
            <FeatureCard
              icon={<Keyboard className="h-6 w-6 text-primary" />}
              title="Simple Activation"
              description="Choose toggle mode (double-tap) or push-to-talk mode (hold key). Simple, predictable control."
              href="/shortcuts/"
            />
            <FeatureCard
              icon={<Globe className="h-6 w-6 text-primary" />}
              title="X11 & Wayland Support"
              description="Works seamlessly with both display servers. Modern Wayland and traditional X11, fully supported."
              href="/wayland/"
            />
            <FeatureCard
              icon={<Settings className="h-6 w-6 text-primary" />}
              title="Fully Configurable"
              description="Adjust model size, language, activation mode, and voice command behavior. GUI settings panel or config file, your choice."
              href="/advanced-settings/"
            />
            <FeatureCard
              icon={<Server className="h-6 w-6 text-primary" />}
              title="Remote API Engine"
              description="Offload transcription to an OpenAI-compatible or whisper.cpp server while keeping the same Linux desktop workflow."
              href="/remote-api/"
            />
            <FeatureCard
              icon={<Activity className="h-6 w-6 text-primary" />}
              title="Silero Voice Activity Detection"
              description="Neural VAD drops silence-only buffers for cleaner dictation, with a safe amplitude fallback when ONNX Runtime is unavailable."
              href="/voice-activity-detection/"
            />
            <FeatureCard
              icon={<ShieldCheck className="h-6 w-6 text-primary" />}
              title="Desktop Reliability"
              description="Suspend/resume recovery, IBus runtime hardening, keyboard layout preservation, and non-ASCII text injection fallbacks."
              href="/desktop-reliability/"
            />
          </div>

          {/* Comparison highlight */}
          <FadeInSection delay={0.2}>
            <div className="from-primary/10 to-primary/10 mt-16 rounded-2xl bg-gradient-to-r via-cyan-500/10 p-8 sm:p-12">
              <div className="grid items-center gap-8 md:grid-cols-2">
                <div>
                  <h3 className="mb-4 text-2xl font-bold sm:text-3xl">
                    The Linux Voice Gap, Solved
                  </h3>
                  <p className="mb-6 text-muted-foreground">
                    While macOS and Windows have had built-in voice dictation
                    for years, Linux users have been left behind. Until now.
                  </p>
                  <ul className="space-y-3">
                    {[
                      "No more cloud services that compromise privacy",
                      "No more janky solutions that only work in specific apps",
                      "No more complicated setup processes",
                      "Just install and start dictating",
                    ].map((item, i) => (
                      <li key={i} className="flex items-start gap-3">
                        <CheckCircle2 className="mt-0.5 h-5 w-5 flex-shrink-0 text-green-500" />
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                </div>
                <div className="flex justify-center">
                  <div className="relative">
                    <div className="rounded-2xl bg-white p-8 shadow-xl dark:bg-zinc-800">
                      <div className="mb-6 flex items-center gap-4">
                        <VocalinuxLogo
                          width={64}
                          height={64}
                          className="h-16 w-16"
                        />
                        <div>
                          <div className="text-2xl font-bold">Vocalinux</div>
                          <div className="text-sm text-muted-foreground">
                            Voice dictation, finally
                          </div>
                        </div>
                      </div>
                      <div className="grid grid-cols-2 gap-4 text-center">
                        <div className="rounded-lg bg-zinc-50 p-3 dark:bg-zinc-900">
                          <div className="text-2xl font-bold text-primary">
                            0
                          </div>
                          <div className="text-xs text-muted-foreground">
                            Cloud calls
                          </div>
                        </div>
                        <div className="rounded-lg bg-zinc-50 p-3 dark:bg-zinc-900">
                          <div className="text-2xl font-bold text-primary">
                            ∞
                          </div>
                          <div className="text-xs text-muted-foreground">
                            Privacy
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </FadeInSection>
        </div>
      </section>

      {/* Installation Section */}
      <section
        id="install"
        className="bg-zinc-50 px-4 py-16 dark:bg-zinc-900/50 sm:px-6 sm:py-24"
      >
        <div className="mx-auto max-w-4xl">
          <FadeInSection>
            <div className="mb-12 text-center">
              <h2 className="mb-4 text-3xl font-bold sm:text-4xl md:text-5xl">
                How to Install Voice Dictation on Linux
              </h2>
              <p className="text-lg text-muted-foreground">
                One command. That&apos;s all it takes.
              </p>
            </div>
          </FadeInSection>

          <FadeInSection delay={0.1}>
            <div className="min-w-0 overflow-hidden rounded-2xl border border-zinc-200 bg-white shadow-xl dark:border-zinc-700 dark:bg-zinc-800">
              <div className="p-6 sm:p-8">
                {/* Interactive install */}
                <div>
                  <div className="mb-4 flex items-center gap-3">
                    <div className="rounded-lg bg-green-500/10 p-2">
                      <Zap className="h-5 w-5 text-green-500" />
                    </div>
                    <div className="flex-1">
                      <h3 className="text-xl font-semibold">
                        Recommended: interactive installer
                      </h3>
                      <p className="text-sm text-muted-foreground">
                        Detects your system, lets you choose an engine, and sets
                        up the desktop app.
                      </p>
                    </div>
                  </div>
                  <div className="overflow-hidden rounded-xl border border-zinc-800 bg-zinc-950/80">
                    <div className="flex items-center justify-between border-b border-zinc-800 bg-zinc-900/50 px-4 py-2.5">
                      <div className="flex items-center gap-2">
                        <div className="h-2.5 w-2.5 rounded-full bg-red-500/70" />
                        <div className="h-2.5 w-2.5 rounded-full bg-yellow-500/70" />
                        <div className="h-2.5 w-2.5 rounded-full bg-green-500/70" />
                      </div>
                      <CopyButton text={interactiveInstallCommand} />
                    </div>
                    <div className="p-4 sm:p-5">
                      <pre className="overflow-x-auto whitespace-pre-wrap text-left font-mono text-sm text-green-400 sm:text-base">
                        <span className="select-none text-zinc-500">$ </span>
                        {interactiveInstallDisplayCommand}
                      </pre>
                    </div>
                  </div>
                </div>

                <div className="mt-6 rounded-xl border border-zinc-200 bg-zinc-50 p-4 dark:border-zinc-700 dark:bg-zinc-900">
                  <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                    <div>
                      <h4 className="font-semibold">
                        Choose your engine during setup
                      </h4>
                      <p className="text-sm text-muted-foreground">
                        Start with the guided installer, then pick the runtime
                        that fits your hardware.
                      </p>
                    </div>
                    <Link
                      href="/compare/"
                      className="inline-flex items-center gap-1 text-sm font-semibold text-primary hover:underline"
                    >
                      Compare engines <ChevronRight className="h-4 w-4" />
                    </Link>
                  </div>

                  <div className="mt-4 grid gap-3 md:grid-cols-3">
                    {[
                      {
                        icon: <Zap className="h-4 w-4 text-green-500" />,
                        title: "whisper.cpp",
                        description: "Default, fast, Vulkan-capable",
                      },
                      {
                        icon: <Cpu className="h-4 w-4 text-cyan-500" />,
                        title: "Whisper",
                        description: "PyTorch/CUDA workflow",
                      },
                      {
                        icon: <Server className="h-4 w-4 text-orange-500" />,
                        title: "VOSK",
                        description: "Small footprint for older systems",
                      },
                    ].map((engine) => (
                      <div
                        key={engine.title}
                        className="rounded-lg border border-zinc-200 bg-white p-3 dark:border-zinc-700 dark:bg-zinc-800"
                      >
                        <div className="mb-2 flex items-center gap-2">
                          <span className="rounded-md bg-zinc-100 p-1.5 dark:bg-zinc-700">
                            {engine.icon}
                          </span>
                          <h5 className="font-semibold">{engine.title}</h5>
                        </div>
                        <p className="text-sm text-muted-foreground">
                          {engine.description}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>

                {/* What the installer does */}
                <div className="mt-8 rounded-lg bg-zinc-50 p-4 dark:bg-zinc-900">
                  <h4 className="mb-3 font-semibold">
                    What the installer does:
                  </h4>
                  <ul className="grid gap-2 text-sm text-muted-foreground sm:grid-cols-2">
                    {[
                      "Installs system dependencies",
                      "Creates isolated virtual environment",
                      "Downloads speech recognition models",
                      "Sets up desktop integration",
                      "Adds vocalinux to your PATH",
                      "Creates application launcher",
                    ].map((item, i) => (
                      <li key={i} className="flex items-center gap-2">
                        <CheckCircle2 className="h-4 w-4 text-green-500" />
                        {item}
                      </li>
                    ))}
                  </ul>
                </div>

                {/* After install */}
                <div className="bg-primary/5 border-primary/20 mt-6 rounded-lg border p-4">
                  <h4 className="mb-2 flex items-center gap-2 font-semibold">
                    <Play className="h-4 w-4 text-primary" />
                    After Installation
                  </h4>
                  <p className="mb-3 text-sm text-muted-foreground">
                    Launch Vocalinux from your terminal or application menu:
                  </p>
                  <code className="block rounded bg-zinc-900 px-4 py-2 text-sm text-green-400">
                    vocalinux
                  </code>
                </div>
              </div>
            </div>
          </FadeInSection>

          {/* System requirements */}
          <FadeInSection delay={0.2}>
            <div className="mt-8 space-y-6">
              <div className="min-w-0 rounded-xl border border-zinc-200 bg-white p-6 dark:border-zinc-700 dark:bg-zinc-800">
                <h4 className="mb-4 flex items-center gap-2 font-semibold">
                  <Cpu className="h-5 w-5 text-primary" />
                  System Requirements
                </h4>
                <ul className="grid gap-2 text-sm text-muted-foreground sm:grid-cols-2">
                  <li>
                    • Ubuntu, Debian, Fedora, Arch, openSUSE, or equivalent
                  </li>
                  <li>• Python 3.9+ with GTK 3/PyGObject dependencies</li>
                  <li>• 4GB RAM minimum; 8GB+ recommended for larger models</li>
                  <li>• Microphone plus X11 or Wayland desktop session</li>
                  <li>• ~200MB disk for the default whisper.cpp setup</li>
                  <li>
                    • Optional Vulkan GPU for AMD, Intel, or NVIDIA acceleration
                  </li>
                </ul>
              </div>
              <div className="min-w-0 rounded-xl border border-zinc-200 bg-white p-6 dark:border-zinc-700 dark:bg-zinc-800">
                <div className="mb-4 flex items-center gap-3">
                  <div className="rounded-lg bg-red-500/10 p-2">
                    <Terminal className="h-5 w-5 text-red-500" />
                  </div>
                  <div className="flex-1">
                    <h4 className="font-semibold">Uninstall</h4>
                    <p className="text-sm text-muted-foreground">
                      Clean removal in one command
                    </p>
                  </div>
                </div>
                <div className="overflow-hidden rounded-xl border border-zinc-800 bg-zinc-950/80">
                  <div className="flex items-center justify-between border-b border-zinc-800 bg-zinc-900/50 px-4 py-2.5">
                    <div className="flex items-center gap-2">
                      <div className="h-2.5 w-2.5 rounded-full bg-red-500/70" />
                      <div className="h-2.5 w-2.5 rounded-full bg-yellow-500/70" />
                      <div className="h-2.5 w-2.5 rounded-full bg-green-500/70" />
                    </div>
                    <CopyButton text={uninstallCommand} />
                  </div>
                  <div className="p-4 sm:p-5">
                    <pre className="overflow-x-auto whitespace-pre-wrap text-left font-mono text-sm text-green-400 sm:text-base">
                      <span className="select-none text-zinc-500">$ </span>
                      {uninstallDisplayCommand}
                    </pre>
                  </div>
                </div>
              </div>
            </div>
          </FadeInSection>
        </div>
      </section>

      {/* SEO Guide Hub Section */}
      <section id="guides" className="px-4 py-16 sm:px-6 sm:py-24">
        <div className="mx-auto max-w-6xl">
          <FadeInSection>
            <div className="mb-12 text-center">
              <h2 className="mb-4 text-3xl font-bold sm:text-4xl md:text-5xl">
                Linux Voice Dictation Guides by Distribution
              </h2>
              <p className="mx-auto max-w-3xl text-lg text-muted-foreground">
                Follow distro-specific setup instructions for Ubuntu, Fedora,
                and Arch Linux. These pages are written for real desktop
                workflows and include post-install checks.
              </p>
            </div>
          </FadeInSection>

          <div className="grid gap-6 md:grid-cols-3">
            {[
              {
                href: "/install/ubuntu/",
                title: "Ubuntu Voice Typing Guide",
                description:
                  "Install offline speech-to-text on Ubuntu 22.04+ for GNOME, KDE, X11, and Wayland.",
              },
              {
                href: "/install/fedora/",
                title: "Fedora Speech-to-Text Guide",
                description:
                  "Set up Vocalinux on Fedora Workstation with distro-specific notes for a stable dictation flow.",
              },
              {
                href: "/install/arch/",
                title: "Arch Linux Dictation Guide",
                description:
                  "Lean setup for Arch, Manjaro, and EndeavourOS with hardware and injection sanity checks.",
              },
            ].map((guide) => (
              <Link
                key={guide.href}
                href={guide.href}
                className="group rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm transition-all hover:-translate-y-1 hover:shadow-lg dark:border-zinc-700 dark:bg-zinc-800"
              >
                <h3 className="mb-3 text-xl font-semibold">{guide.title}</h3>
                <p className="mb-4 text-sm text-muted-foreground">
                  {guide.description}
                </p>
                <span className="inline-flex items-center gap-1 text-sm font-semibold text-primary group-hover:underline">
                  Read guide <ChevronRight className="h-4 w-4" />
                </span>
              </Link>
            ))}
          </div>

          <FadeInSection delay={0.15}>
            <div className="border-primary/20 bg-primary/5 mt-8 rounded-2xl border p-6 sm:p-8">
              <h3 className="mb-3 text-2xl font-bold">
                Need help choosing an engine?
              </h3>
              <p className="mb-4 text-muted-foreground">
                Compare whisper.cpp, Whisper, and VOSK for speed, hardware
                support, and model size.
              </p>
              <Link
                href="/compare/"
                className="inline-flex items-center gap-2 text-sm font-semibold text-primary hover:underline"
              >
                View speech engine comparison{" "}
                <ChevronRight className="h-4 w-4" />
              </Link>
            </div>
          </FadeInSection>
        </div>
      </section>

      {/* Speech Engines Section */}
      <section className="bg-zinc-50 px-4 py-16 dark:bg-zinc-900/50 sm:px-6 sm:py-24">
        <div className="mx-auto max-w-7xl">
          <FadeInSection>
            <div className="mb-12 text-center">
              <h2 className="mb-4 text-3xl font-bold sm:text-4xl md:text-5xl">
                Choose Your Linux Speech Recognition Engine
              </h2>
              <p className="mx-auto max-w-2xl text-lg text-muted-foreground">
                Vocalinux supports local and remote speech recognition engines.
                Pick the one that suits your hardware, privacy boundary, and
                latency needs.
              </p>
            </div>
          </FadeInSection>

          <div className="grid gap-8 md:grid-cols-2 xl:grid-cols-4">
            <FadeInSection delay={0.1}>
              <div className="h-full rounded-xl border border-zinc-200 bg-white p-6 dark:border-zinc-700 dark:bg-zinc-800">
                <div className="mb-4 flex items-center gap-3">
                  <div className="rounded-lg bg-purple-500/10 p-3">
                    <Sparkles className="h-6 w-6 text-purple-500" />
                  </div>
                  <h3 className="text-xl font-bold">Whisper (OpenAI)</h3>
                </div>
                <p className="mb-6 text-muted-foreground">
                  OpenAI&apos;s original PyTorch-based Whisper model. NVIDIA GPU
                  only.
                </p>
                <ul className="mb-6 space-y-2">
                  {[
                    "PyTorch-based implementation",
                    "NVIDIA GPU support (CUDA)",
                    "Same accuracy as whisper.cpp",
                    "Larger download (~2.3GB)",
                  ].map((item, i) => (
                    <li key={i} className="flex items-center gap-2 text-sm">
                      <CheckCircle2 className="h-4 w-4 text-purple-500" />
                      {item}
                    </li>
                  ))}
                </ul>
                <div className="text-sm text-muted-foreground">
                  <strong>Install time:</strong> ~5-10 minutes with PyTorch
                </div>
              </div>
            </FadeInSection>

            <FadeInSection delay={0.2}>
              <div className="flex h-full flex-col overflow-hidden rounded-xl border-2 border-primary bg-white p-6 dark:bg-zinc-800">
                <div className="mb-4 flex items-center gap-3">
                  <div className="bg-primary/10 rounded-lg p-3">
                    <Zap className="h-6 w-6 text-primary" />
                  </div>
                  <h3 className="text-xl font-bold">whisper.cpp</h3>
                </div>
                <p className="mb-6 text-muted-foreground">
                  High-performance C++ port of Whisper with Vulkan GPU support.
                  Our new default!
                </p>
                <ul className="mb-6 space-y-2">
                  {[
                    "10x faster installation (~1-2 min)",
                    "Universal GPU support (AMD/Intel/NVIDIA)",
                    "C++ optimized, true multi-threading",
                    "Tiny model only ~74MB",
                  ].map((item, i) => (
                    <li key={i} className="flex items-center gap-2 text-sm">
                      <CheckCircle2 className="h-4 w-4 text-green-500" />
                      {item}
                    </li>
                  ))}
                </ul>
                <div className="text-sm text-muted-foreground">
                  <strong>Model sizes:</strong> Tiny (74MB) • Base (141MB) •
                  Small (465MB) • Medium (1.5GB) • Large (3.0GB)
                </div>
                <div className="mt-auto flex justify-center pt-6">
                  <span className="rounded-full bg-primary px-3 py-1 text-xs font-semibold text-primary-foreground dark:text-black">
                    Default engine
                  </span>
                </div>
              </div>
            </FadeInSection>

            <FadeInSection delay={0.3}>
              <div className="h-full rounded-xl border border-zinc-200 bg-white p-6 dark:border-zinc-700 dark:bg-zinc-800">
                <div className="mb-4 flex items-center gap-3">
                  <div className="rounded-lg bg-blue-500/10 p-3">
                    <Cpu className="h-6 w-6 text-blue-500" />
                  </div>
                  <h3 className="text-xl font-bold">VOSK</h3>
                </div>
                <p className="mb-6 text-muted-foreground">
                  Lightweight, fast speech recognition engine perfect for
                  lower-powered systems.
                </p>
                <ul className="mb-6 space-y-2">
                  {[
                    "Very lightweight and fast",
                    "Low memory footprint",
                    "Great for real-time streaming",
                    "CPU only, minimal resources",
                  ].map((item, i) => (
                    <li key={i} className="flex items-center gap-2 text-sm">
                      <CheckCircle2 className="h-4 w-4 text-blue-500" />
                      {item}
                    </li>
                  ))}
                </ul>
                <div className="text-sm text-muted-foreground">
                  <strong>Footprint:</strong> ~40MB model, minimal CPU/RAM usage
                </div>
              </div>
            </FadeInSection>

            <FadeInSection delay={0.4}>
              <div className="h-full rounded-xl border border-zinc-200 bg-white p-6 dark:border-zinc-700 dark:bg-zinc-800">
                <div className="mb-4 flex items-center gap-3">
                  <div className="rounded-lg bg-green-500/10 p-3">
                    <Server className="h-6 w-6 text-green-500" />
                  </div>
                  <h3 className="text-xl font-bold">Remote API</h3>
                </div>
                <p className="mb-6 text-muted-foreground">
                  Send utterances to a trusted OpenAI-compatible or whisper.cpp
                  server when another machine should handle transcription.
                </p>
                <ul className="mb-6 space-y-2">
                  {[
                    "OpenAI-compatible endpoint support",
                    "whisper.cpp server support",
                    "Optional bearer token authentication",
                    "Local VAD and text injection remain active",
                  ].map((item, i) => (
                    <li key={i} className="flex items-center gap-2 text-sm">
                      <CheckCircle2 className="h-4 w-4 text-green-500" />
                      {item}
                    </li>
                  ))}
                </ul>
                <div className="text-sm text-muted-foreground">
                  <strong>Best for:</strong> powerful LAN servers and shared
                  Whisper backends
                </div>
              </div>
            </FadeInSection>
          </div>

          <FadeInSection delay={0.5}>
            <div className="mt-10 text-center">
              <Link
                href="/compare/"
                className="inline-flex items-center gap-1.5 text-sm font-medium text-primary hover:underline"
              >
                Compare all engines <ChevronRight className="h-4 w-4" />
              </Link>
            </div>
          </FadeInSection>
        </div>
      </section>

      {/* FAQ Section */}
      <section id="faq" className="px-4 py-16 sm:px-6 sm:py-24">
        <div className="mx-auto max-w-3xl">
          <FadeInSection>
            <div className="mb-12 text-center">
              <h2 className="mb-4 text-3xl font-bold sm:text-4xl md:text-5xl">
                Frequently Asked Questions
              </h2>
            </div>
          </FadeInSection>

          <div className="space-y-4">
            {(
              [
                {
                  question: "Is Vocalinux really 100% offline?",
                  answer: (
                    <>
                      Yes for local engines: whisper.cpp, Whisper, and VOSK
                      process speech on your machine. Vocalinux also includes an
                      optional Remote API engine for trusted servers you
                      configure yourself.{" "}
                      <Link
                        href="/offline/"
                        className="text-primary hover:underline"
                      >
                        Read more about offline voice dictation
                      </Link>
                      .
                    </>
                  ),
                },
                {
                  question: "Does Vocalinux collect usage telemetry?",
                  answer:
                    "No. The installed app does not send usage telemetry, analytics events, or background usage pings. Even the project maintainer cannot see how many people have installed or actively use Vocalinux, and you can verify this by watching for external network calls after installation.",
                },
                {
                  question: "Which Linux distributions are supported?",
                  answer: (
                    <>
                      Vocalinux works on most modern Linux distributions
                      including Ubuntu 22.04+, Debian 11+, Fedora 39+, Arch
                      Linux, and openSUSE Tumbleweed. Experimental support is
                      available for Gentoo, Alpine, Void, Solus, and more. It
                      supports both X11 and Wayland display servers.{" "}
                      <Link
                        href="/install/"
                        className="text-primary hover:underline"
                      >
                        See installation guides
                      </Link>
                      .
                    </>
                  ),
                },
                {
                  question: "How do I switch between speech engines?",
                  answer: (
                    <>
                      You can switch engines in the Settings dialog or via the
                      command line. The options are whisper.cpp (default),
                      OpenAI Whisper, VOSK, and Remote API. From the CLI, use
                      &quot;--engine whisper_cpp&quot;, &quot;--engine
                      whisper&quot;, &quot;--engine vosk&quot;, or
                      &quot;--engine remote_api&quot;.{" "}
                      <Link
                        href="/compare/"
                        className="text-primary hover:underline"
                      >
                        Compare all engines
                      </Link>
                      .
                    </>
                  ),
                },
                {
                  question: "Can Vocalinux use a remote transcription server?",
                  answer: (
                    <>
                      Yes. v0.12.0 adds Remote API recognition for
                      OpenAI-compatible Whisper servers and the whisper.cpp
                      server endpoint. Configure it from Settings → Advanced →
                      Remote Server.{" "}
                      <Link
                        href="/remote-api/"
                        className="text-primary hover:underline"
                      >
                        Read the Remote API guide
                      </Link>
                      .
                    </>
                  ),
                },
                {
                  question: "What is Silero VAD?",
                  answer: (
                    <>
                      Silero VAD is neural voice activity detection. Vocalinux
                      uses it when ONNX Runtime support is available to drop
                      silence-only buffers before recognition, with
                      amplitude-based VAD as a fallback.{" "}
                      <Link
                        href="/voice-activity-detection/"
                        className="text-primary hover:underline"
                      >
                        Learn about VAD
                      </Link>
                      .
                    </>
                  ),
                },
                {
                  question: "What happens when I close my laptop lid?",
                  answer: (
                    <>
                      Vocalinux v0.10.1+ automatically recovers speech
                      recognition and keyboard shortcuts after system
                      suspend/resume. No manual restart needed.{" "}
                      <Link
                        href="/desktop-reliability/"
                        className="text-primary hover:underline"
                      >
                        See reliability improvements
                      </Link>
                      .
                    </>
                  ),
                },
                {
                  question: "Does Vocalinux preserve my keyboard layout?",
                  answer:
                    "Yes! v0.10.1+ preserves your XKB keyboard layout when activating IBus, so you won't unexpectedly switch to US layout mid-dictation.",
                },
                {
                  question: "What are the system requirements?",
                  answer: (
                    <>
                      Minimum: 4GB RAM, Python 3.9+, ~200MB disk space. 8GB+ RAM
                      recommended for larger Whisper models. The default
                      whisper.cpp tiny model (~74MB) works great on modest
                      hardware. GPU acceleration is available via Vulkan for
                      AMD, Intel, and NVIDIA GPUs.{" "}
                      <Link
                        href="/install/"
                        className="text-primary hover:underline"
                      >
                        View full installation requirements
                      </Link>
                      .
                    </>
                  ),
                },
                {
                  question: "Can I use it in languages other than English?",
                  answer: (
                    <>
                      Yes! whisper.cpp and OpenAI Whisper support 99+ languages
                      with varying accuracy levels. VOSK includes models for 10
                      languages out of the box (English, Hindi, Spanish, French,
                      German, Italian, Portuguese, Russian, Chinese, and more).
                      Additional language models can be downloaded as needed.{" "}
                      <Link
                        href="/languages/"
                        className="text-primary hover:underline"
                      >
                        See supported languages
                      </Link>
                      .
                    </>
                  ),
                },
                {
                  question: "How do I customize the activation shortcut?",
                  answer: (
                    <>
                      The default is toggle mode with double-tap Ctrl. You can
                      switch to push-to-talk in Settings, and choose between
                      Left Ctrl, Right Ctrl, Alt, Shift, and other modifier
                      keys. Configuration is also available by editing
                      ~/.config/vocalinux/config.json.{" "}
                      <Link
                        href="/shortcuts/"
                        className="text-primary hover:underline"
                      >
                        View shortcut options
                      </Link>
                      .
                    </>
                  ),
                },
                {
                  question: "Can I disable voice commands?",
                  answer: (
                    <>
                      Yes. Voice commands can be toggled on or off in the
                      Settings dialog. By default, commands are automatically
                      enabled for VOSK and disabled for Whisper/whisper.cpp, but
                      you can override this at any time.{" "}
                      <Link
                        href="/shortcuts/"
                        className="text-primary hover:underline"
                      >
                        Learn about voice commands
                      </Link>
                      .
                    </>
                  ),
                },
                {
                  question: "Is Vocalinux free?",
                  answer: (
                    <>
                      Yes, Vocalinux is completely free and open-source,
                      licensed under GPL-3.0. No premium tiers, no
                      subscriptions, no tracking. Just free software.{" "}
                      <Link
                        href="/open-source/"
                        className="text-primary hover:underline"
                      >
                        Learn about the project
                      </Link>
                      .
                    </>
                  ),
                },
              ] as { question: string; answer: React.ReactNode }[]
            ).map((item, i) => (
              <FadeInSection key={i} delay={i * 0.05}>
                <details className="group rounded-xl border border-zinc-200 bg-white dark:border-zinc-700 dark:bg-zinc-800">
                  <summary className="flex cursor-pointer list-none items-center justify-between p-6">
                    <h3 className="pr-4 font-semibold">{item.question}</h3>
                    <ChevronRight className="h-5 w-5 text-muted-foreground transition-transform group-open:rotate-90" />
                  </summary>
                  <div className="px-6 pb-6 text-muted-foreground">
                    {item.answer}
                  </div>
                </details>
              </FadeInSection>
            ))}
          </div>
        </div>
      </section>

      {/* The Voca Family - Ecosystem Section */}
      <section
        id="ecosystem"
        className="bg-zinc-50 px-4 py-16 dark:bg-zinc-900/50 sm:px-6 sm:py-24"
      >
        <div className="mx-auto max-w-7xl">
          <FadeInSection>
            <div className="mb-12 text-center">
              <h2 className="mb-4 text-3xl font-bold sm:text-4xl md:text-5xl">
                The Voca Family
              </h2>
              <p className="mx-auto max-w-2xl text-lg text-muted-foreground">
                Voice dictation, done right, on every platform.
              </p>
            </div>
          </FadeInSection>

          <div className="grid gap-8 md:grid-cols-3">
            {/* VocaMac Card */}
            <FadeInSection delay={0.1}>
              <div className="group relative h-full overflow-hidden rounded-xl border border-zinc-300/80 bg-gradient-to-br from-zinc-50 via-white to-zinc-200 p-6 shadow-sm transition-all duration-300 hover:-translate-y-1 hover:border-zinc-400 hover:shadow-xl hover:shadow-zinc-500/10 dark:border-zinc-600 dark:from-zinc-800 dark:via-zinc-800 dark:to-zinc-700/70">
                <div className="pointer-events-none absolute inset-x-6 top-0 h-px bg-gradient-to-r from-transparent via-white/70 to-transparent opacity-70 dark:via-white/20" />
                <div className="absolute right-4 top-4">
                  <span className="rounded bg-primary px-2 py-1 text-xs font-semibold text-primary-foreground dark:text-black">
                    Beta
                  </span>
                </div>
                <div className="mb-4 flex items-center gap-3">
                  <div className="flex items-center justify-center rounded-lg bg-gradient-to-br from-zinc-100 to-zinc-300 p-3 shadow-inner transition-transform duration-300 group-hover:scale-105 dark:from-zinc-700 dark:to-zinc-500">
                    <img
                      src="https://cdn.simpleicons.org/apple/000000"
                      alt="macOS"
                      width={24}
                      height={24}
                      className="dark:invert"
                    />
                  </div>
                  <h3 className="text-xl font-bold">VocaMac</h3>
                </div>
                <p className="mb-4 text-muted-foreground">
                  Native macOS menu bar app. 100% offline voice-to-text powered
                  by WhisperKit and CoreML with Apple Silicon acceleration.
                </p>
                <div className="mb-6 flex flex-wrap gap-2">
                  <span className="bg-primary/10 rounded-full px-2 py-1 text-xs font-medium text-primary">
                    WhisperKit
                  </span>
                  <span className="bg-primary/10 rounded-full px-2 py-1 text-xs font-medium text-primary">
                    CoreML
                  </span>
                  <span className="bg-primary/10 rounded-full px-2 py-1 text-xs font-medium text-primary">
                    Apple Silicon
                  </span>
                  <span className="rounded-full bg-zinc-100 px-2 py-1 text-xs font-medium text-zinc-700 dark:bg-zinc-700 dark:text-zinc-300">
                    AGPL-3.0
                  </span>
                </div>
                <div className="flex gap-3">
                  <a
                    href="https://vocamac.com"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="hover:bg-primary/90 inline-flex items-center gap-1.5 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-all dark:text-black"
                  >
                    <Globe className="h-4 w-4" />
                    Website
                  </a>
                  <a
                    href="https://github.com/jatinkrmalik/vocamac"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1.5 rounded-lg bg-zinc-100 px-4 py-2 text-sm font-medium text-zinc-700 transition-all hover:bg-zinc-200 dark:bg-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-600"
                  >
                    <Github className="h-4 w-4" />
                    GitHub
                  </a>
                </div>
              </div>
            </FadeInSection>

            {/* VocaLinux Card (center) */}
            <FadeInSection delay={0.2}>
              <div className="from-primary/10 shadow-primary/10 hover:shadow-primary/20 group relative h-full overflow-hidden rounded-xl border-2 border-primary bg-gradient-to-br via-white to-emerald-500/10 p-6 shadow-sm transition-all duration-300 hover:-translate-y-1 hover:shadow-xl dark:via-zinc-800 dark:to-emerald-500/15">
                <div className="via-primary/70 pointer-events-none absolute inset-x-6 top-0 h-px bg-gradient-to-r from-transparent to-transparent" />
                <div className="absolute right-4 top-4">
                  <span className="rounded bg-primary px-2 py-1 text-xs font-semibold text-primary-foreground dark:text-black">
                    Beta
                  </span>
                </div>
                <div className="mb-4 flex items-center gap-3">
                  <div className="from-primary/15 dark:from-primary/20 flex items-center justify-center rounded-lg bg-gradient-to-br to-emerald-500/20 p-3 shadow-inner transition-transform duration-300 group-hover:scale-105 dark:to-emerald-500/20">
                    <img
                      src="https://cdn.simpleicons.org/linux/000000"
                      alt="Linux"
                      width={24}
                      height={24}
                      className="dark:invert"
                    />
                  </div>
                  <h3 className="text-xl font-bold">VocaLinux</h3>
                </div>
                <p className="mb-4 text-muted-foreground">
                  Voice dictation for Linux. System tray app with whisper.cpp,
                  Vulkan GPU acceleration, and full offline support.
                </p>
                <div className="mb-6 flex flex-wrap gap-2">
                  <span className="bg-primary/10 rounded-full px-2 py-1 text-xs font-medium text-primary">
                    whisper.cpp
                  </span>
                  <span className="bg-primary/10 rounded-full px-2 py-1 text-xs font-medium text-primary">
                    Vulkan GPU
                  </span>
                  <span className="bg-primary/10 rounded-full px-2 py-1 text-xs font-medium text-primary">
                    GTK
                  </span>
                  <span className="rounded-full bg-zinc-100 px-2 py-1 text-xs font-medium text-zinc-700 dark:bg-zinc-700 dark:text-zinc-300">
                    GPL-3.0
                  </span>
                </div>
                <div className="flex gap-3">
                  <a
                    href="#install"
                    className="hover:bg-primary/90 inline-flex items-center gap-1.5 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-all dark:text-black"
                  >
                    <Download className="h-4 w-4" />
                    Install
                  </a>
                  <a
                    href="https://github.com/jatinkrmalik/vocalinux"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1.5 rounded-lg bg-zinc-100 px-4 py-2 text-sm font-medium text-zinc-700 transition-all hover:bg-zinc-200 dark:bg-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-600"
                  >
                    <Github className="h-4 w-4" />
                    GitHub
                  </a>
                </div>
              </div>
            </FadeInSection>

            {/* VocaWin Card */}
            <FadeInSection delay={0.3}>
              <div className="group relative h-full overflow-hidden rounded-xl border border-sky-300/60 bg-gradient-to-br from-sky-50 via-white to-blue-100 p-6 shadow-sm transition-all duration-300 hover:-translate-y-1 hover:border-sky-400 hover:shadow-xl hover:shadow-sky-500/10 dark:border-sky-900/80 dark:from-zinc-800 dark:via-zinc-800 dark:to-blue-950/50">
                <div className="pointer-events-none absolute inset-x-6 top-0 h-px bg-gradient-to-r from-transparent via-sky-300/70 to-transparent dark:via-sky-500/40" />
                <div className="absolute right-4 top-4">
                  <span className="rounded bg-amber-100 px-2 py-1 text-xs font-semibold text-amber-700 dark:bg-amber-900/30 dark:text-amber-400">
                    Coming Soon
                  </span>
                </div>
                <div className="mb-4 flex items-center gap-3">
                  <div className="flex items-center justify-center rounded-lg bg-gradient-to-br from-sky-100 to-blue-200 p-3 shadow-inner transition-transform duration-300 group-hover:scale-105 dark:from-blue-950 dark:to-sky-900">
                    <svg
                      viewBox="0 0 88 88"
                      width={24}
                      height={24}
                      aria-label="Windows"
                    >
                      <path
                        d="M0 12.402l35.687-4.86.016 34.423-35.67.203zm35.67 33.529.028 34.453L.028 75.48.026 45.7zm4.326-39.025L87.314.0v41.527l-47.318.376zm47.329 39.349-.011 41.34-47.318-6.678-.066-34.739z"
                        fill="#0078D4"
                      />
                    </svg>
                  </div>
                  <h3 className="text-xl font-bold">VocaWin</h3>
                </div>
                <p className="mb-4 text-muted-foreground">
                  Voice dictation for Windows. Native system tray app with
                  offline-first architecture. Currently in planning.
                </p>
                <div className="mb-6 flex flex-wrap gap-2">
                  <span className="bg-primary/10 rounded-full px-2 py-1 text-xs font-medium text-primary">
                    whisper.cpp
                  </span>
                  <span className="bg-primary/10 rounded-full px-2 py-1 text-xs font-medium text-primary">
                    Native Tray
                  </span>
                  <span className="rounded-full bg-amber-100 px-2 py-1 text-xs font-medium text-amber-700 dark:bg-amber-900/30 dark:text-amber-400">
                    Planned
                  </span>
                </div>
                <div className="flex gap-3">
                  <a
                    href="https://vocawin.com"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="hover:bg-primary/90 inline-flex items-center gap-1.5 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-all dark:text-black"
                  >
                    <Globe className="h-4 w-4" />
                    Website
                  </a>
                  <a
                    href="https://github.com/jatinkrmalik/vocawin"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1.5 rounded-lg bg-zinc-100 px-4 py-2 text-sm font-medium text-zinc-700 transition-all hover:bg-zinc-200 dark:bg-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-600"
                  >
                    <Github className="h-4 w-4" />
                    GitHub
                  </a>
                </div>
              </div>
            </FadeInSection>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="from-primary/10 to-primary/10 bg-gradient-to-br via-cyan-500/10 px-4 py-16 sm:px-6 sm:py-24">
        <div className="mx-auto max-w-4xl text-center">
          <FadeInSection>
            <h2 className="mb-6 text-3xl font-bold sm:text-4xl md:text-5xl">
              Ready to Ditch Your Keyboard?
            </h2>
            <p className="mx-auto mb-8 max-w-2xl text-lg text-muted-foreground">
              Join the growing community of Linux users who have discovered the
              power of voice dictation. It&apos;s free, it&apos;s private, and
              it just works.
            </p>
            <div className="flex flex-col justify-center gap-4 sm:flex-row">
              <a
                href="#install"
                className="hover:bg-primary/90 shadow-primary/25 inline-flex items-center justify-center gap-2 rounded-xl bg-primary px-8 py-4 text-lg font-semibold text-white shadow-lg transition-all hover:scale-105 dark:text-zinc-900"
              >
                <Download className="h-5 w-5" />
                Install Vocalinux
              </a>
              <a
                href="https://github.com/jatinkrmalik/vocalinux"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center justify-center gap-2 rounded-xl bg-zinc-900 px-8 py-4 text-lg font-semibold text-white transition-all hover:bg-zinc-800"
              >
                <Star className="h-5 w-5" />
                Star on GitHub
              </a>
            </div>
          </FadeInSection>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-zinc-900 px-4 py-12 text-white sm:px-6">
        <div className="mx-auto max-w-7xl">
          <div className="mb-12 grid grid-cols-2 gap-8 md:grid-cols-3 lg:grid-cols-6">
            <div className="col-span-2 mb-4 lg:col-span-1 lg:mb-0">
              <Link href="/" className="mb-4 flex items-center gap-2">
                <VocalinuxLogo width={32} height={32} className="h-8 w-8" />
                <span className="text-xl font-bold">Vocalinux</span>
              </Link>
              <p className="mb-4 max-w-xs text-sm text-zinc-400">
                Free, open-source voice dictation for Linux. 100% offline and
                privacy-focused.
              </p>
              <div className="flex items-center gap-4">
                <a
                  href="https://github.com/jatinkrmalik/vocalinux"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-zinc-400 transition-colors hover:text-white"
                  aria-label="GitHub"
                >
                  <Github className="h-6 w-6" />
                </a>
              </div>
            </div>

            <div>
              <h3 className="mb-4 text-xs font-semibold uppercase tracking-wider text-zinc-400">
                Get Started
              </h3>
              <ul className="space-y-2.5 text-sm">
                <li>
                  <a
                    href="#features"
                    className="text-zinc-400 transition-colors hover:text-white"
                  >
                    Features
                  </a>
                </li>
                <li>
                  <Link
                    href="/install/"
                    className="text-zinc-400 transition-colors hover:text-white"
                  >
                    Install Guide
                  </Link>
                </li>
                <li>
                  <Link
                    href="/changelog/"
                    className="text-zinc-400 transition-colors hover:text-white"
                  >
                    Changelog
                  </Link>
                </li>
                <li>
                  <Link
                    href="/autostart/"
                    className="text-zinc-400 transition-colors hover:text-white"
                  >
                    Autostart
                  </Link>
                </li>
              </ul>
            </div>

            <div>
              <h3 className="mb-4 text-xs font-semibold uppercase tracking-wider text-zinc-400">
                Recognition
              </h3>
              <ul className="space-y-2.5 text-sm">
                <li>
                  <Link
                    href="/compare/"
                    className="text-zinc-400 transition-colors hover:text-white"
                  >
                    Engine Comparison
                  </Link>
                </li>
                <li>
                  <Link
                    href="/remote-api/"
                    className="text-zinc-400 transition-colors hover:text-white"
                  >
                    Remote API
                  </Link>
                </li>
                <li>
                  <Link
                    href="/whisper-model-guide/"
                    className="text-zinc-400 transition-colors hover:text-white"
                  >
                    Whisper Models
                  </Link>
                </li>
                <li>
                  <Link
                    href="/advanced-settings/"
                    className="text-zinc-400 transition-colors hover:text-white"
                  >
                    Advanced Settings
                  </Link>
                </li>
                <li>
                  <Link
                    href="/voice-activity-detection/"
                    className="text-zinc-400 transition-colors hover:text-white"
                  >
                    Silero VAD
                  </Link>
                </li>
                <li>
                  <Link
                    href="/vs-nerd-dictation/"
                    className="text-zinc-400 transition-colors hover:text-white"
                  >
                    vs Nerd Dictation
                  </Link>
                </li>
              </ul>
            </div>

            <div>
              <h3 className="mb-4 text-xs font-semibold uppercase tracking-wider text-zinc-400">
                Desktop
              </h3>
              <ul className="space-y-2.5 text-sm">
                <li>
                  <Link
                    href="/wayland/"
                    className="text-zinc-400 transition-colors hover:text-white"
                  >
                    Wayland Support
                  </Link>
                </li>
                <li>
                  <Link
                    href="/gpu-acceleration/"
                    className="text-zinc-400 transition-colors hover:text-white"
                  >
                    GPU Acceleration
                  </Link>
                </li>
                <li>
                  <Link
                    href="/desktop-reliability/"
                    className="text-zinc-400 transition-colors hover:text-white"
                  >
                    Desktop Reliability
                  </Link>
                </li>
                <li>
                  <Link
                    href="/shortcuts/"
                    className="text-zinc-400 transition-colors hover:text-white"
                  >
                    Voice Commands
                  </Link>
                </li>
                <li>
                  <Link
                    href="/offline/"
                    className="text-zinc-400 transition-colors hover:text-white"
                  >
                    100% Offline
                  </Link>
                </li>
              </ul>
            </div>

            <div>
              <h3 className="mb-4 text-xs font-semibold uppercase tracking-wider text-zinc-400">
                Use Cases
              </h3>
              <ul className="space-y-2.5 text-sm">
                <li>
                  <Link
                    href="/for-developers/"
                    className="text-zinc-400 transition-colors hover:text-white"
                  >
                    For Developers
                  </Link>
                </li>
                <li>
                  <Link
                    href="/writers/"
                    className="text-zinc-400 transition-colors hover:text-white"
                  >
                    For Writers
                  </Link>
                </li>
                <li>
                  <Link
                    href="/voice-typing-vscode/"
                    className="text-zinc-400 transition-colors hover:text-white"
                  >
                    VS Code
                  </Link>
                </li>
                <li>
                  <Link
                    href="/gnome-kde/"
                    className="text-zinc-400 transition-colors hover:text-white"
                  >
                    GNOME vs KDE
                  </Link>
                </li>
                <li>
                  <Link
                    href="/rsi-prevention/"
                    className="text-zinc-400 transition-colors hover:text-white"
                  >
                    RSI Prevention
                  </Link>
                </li>
              </ul>
            </div>

            <div>
              <h3 className="mb-4 text-xs font-semibold uppercase tracking-wider text-zinc-400">
                Support
              </h3>
              <ul className="space-y-2.5 text-sm">
                <li>
                  <Link
                    href="/faq/"
                    className="text-zinc-400 transition-colors hover:text-white"
                  >
                    FAQ
                  </Link>
                </li>
                <li>
                  <Link
                    href="/troubleshooting/"
                    className="text-zinc-400 transition-colors hover:text-white"
                  >
                    Troubleshooting
                  </Link>
                </li>
                <li>
                  <Link
                    href="/alternatives/"
                    className="text-zinc-400 transition-colors hover:text-white"
                  >
                    Alternatives
                  </Link>
                </li>
                <li>
                  <Link
                    href="/privacy/"
                    className="text-zinc-400 transition-colors hover:text-white"
                  >
                    Privacy Policy
                  </Link>
                </li>
              </ul>
            </div>
          </div>

          <div className="flex flex-col items-center justify-between gap-4 border-t border-zinc-800 pt-8 sm:flex-row">
            <p className="text-sm text-zinc-400">
              © {new Date().getFullYear()} Vocalinux. Open-source under GPL-3.0
              License.
            </p>
            <p className="flex items-center gap-1 text-sm text-zinc-400">
              Made with <Heart className="h-4 w-4 text-red-500" /> by{" "}
              <a
                href="https://x.com/intent/user?screen_name=jatinkrmalik"
                target="_blank"
                rel="noopener noreferrer"
                className="text-zinc-400 transition-colors hover:text-white"
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
