"use client";

import React, { useState, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import Image from "next/image";
import Link from "next/link";
import { LiveDemo } from "@/components/live-demo";
import {
  Mic,
  Terminal,
  Lock,
  Zap,
  Laptop,
  Keyboard,
  Settings,
  Code,
  Github,
  Edit,
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
  Globe,
  Cpu,
  Volume2,
  Sparkles,
  Heart,
  ExternalLink,
} from "lucide-react";
import { ThemeToggle } from "@/components/theme-toggle";
import SyntaxHighlighter from "react-syntax-highlighter";
import { atomOneDark } from "react-syntax-highlighter/dist/esm/styles/hljs";
import { useInView } from "react-intersection-observer";

// The one-liner install command (split into three lines for display)
const oneClickInstallCommand = `curl \\
  -fsSL https://raw.githubusercontent.com/jatinkrmalik/vocalinux/main/install.sh \\
  | bash`;

const oneClickInstallWhisperCpu = `curl \\
  -fsSL https://raw.githubusercontent.com/jatinkrmalik/vocalinux/main/install.sh \\
  | bash -s -- --whisper-cpu`;

const oneClickInstallNoWhisper = `curl \\
  -fsSL https://raw.githubusercontent.com/jatinkrmalik/vocalinux/main/install.sh \\
  | bash -s -- --no-whisper`;

const uninstallCommand = `curl -fsSL \\
  https://raw.githubusercontent.com/jatinkrmalik/vocalinux/main/uninstall.sh \\
  | bash`;

const FeatureCard = ({
  icon,
  title,
  description,
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
}) => {
  const [ref, inView] = useInView({
    triggerOnce: true,
    threshold: 0.1,
  });
  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 20 }}
      animate={inView ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
      transition={{ duration: 0.5 }}
      className="bg-white dark:bg-zinc-800 p-6 rounded-xl shadow-md hover:shadow-xl transition-all h-full border border-zinc-100 dark:border-zinc-700"
    >
      <div className="flex items-center gap-4 mb-4">
        <div className="bg-primary/10 p-3 rounded-lg">{icon}</div>
        <h3 className="text-lg sm:text-xl font-semibold">{title}</h3>
      </div>
      <p className="text-sm sm:text-base text-muted-foreground">{description}</p>
    </motion.div>
  );
};

const CopyButton = ({ text, className = "" }: { text: string; className?: string }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = useCallback(() => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }, [text]);

  return (
    <button
      onClick={handleCopy}
      className={`flex items-center gap-2 bg-zinc-700 hover:bg-zinc-600 text-white px-3 py-1.5 rounded text-sm transition-all ${className}`}
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
    // Fetch actual GitHub stars
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
    { href: "#voice-commands", label: "Commands" },
    { href: "#faq", label: "FAQ" },
  ];

  return (
    <main className="min-h-screen bg-gradient-to-b from-zinc-50 to-white dark:from-zinc-900 dark:to-zinc-950">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-background/80 backdrop-blur-md border-b border-border">
        <nav className="max-w-7xl mx-auto px-4 sm:px-6 py-3 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2 group">
            <Image
              src="/vocalinux.svg"
              alt="Vocalinux Logo"
              width={32}
              height={32}
              className="h-7 w-7 sm:h-8 sm:w-8 transition-transform group-hover:scale-110"
              priority
            />
            <span className="font-bold text-lg sm:text-xl">Vocalinux</span>
            <span className="hidden sm:inline-block text-xs bg-gradient-to-r from-primary/20 to-green-500/20 text-primary border border-primary/30 px-2.5 py-1 rounded-full font-semibold shadow-sm shadow-primary/20">
              v0.2.0 Alpha
            </span>
          </Link>

          {/* Desktop navigation */}
          <div className="hidden md:flex items-center gap-6">
            {navLinks.map((link) => (
              <a
                key={link.href}
                href={link.href}
                className="text-muted-foreground hover:text-foreground transition-colors text-sm font-medium"
              >
                {link.label}
              </a>
            ))}
            <a
              href="https://github.com/jatinkrmalik/vocalinux"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors"
            >
              <Github className="h-5 w-5" />
              {stars !== null && (
                <span className="text-xs bg-zinc-100 dark:bg-zinc-800 px-2 py-0.5 rounded-full">
                  {stars.toLocaleString()}
                </span>
              )}
            </a>
            <ThemeToggle />
          </div>

          {/* Mobile navigation toggle */}
          <div className="flex md:hidden items-center gap-3">
            <ThemeToggle />
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 text-foreground focus:outline-none"
              aria-label="Toggle menu"
            >
              {mobileMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
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
          className="md:hidden overflow-hidden bg-background border-b border-border"
        >
          <div className="px-4 py-3 space-y-2">
            {navLinks.map((link) => (
              <a
                key={link.href}
                href={link.href}
                className="block py-2 text-foreground hover:text-primary transition-colors"
                onClick={() => setMobileMenuOpen(false)}
              >
                {link.label}
              </a>
            ))}
            <a
              href="https://github.com/jatinkrmalik/vocalinux"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 py-2 text-foreground hover:text-primary transition-colors"
              onClick={() => setMobileMenuOpen(false)}
            >
              <Github className="h-5 w-5" />
              GitHub
            </a>
          </div>
        </motion.div>
      </header>

      {/* Hero Section */}
      <section className="relative pt-28 sm:pt-36 pb-16 sm:pb-24 px-4 sm:px-6 overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-purple-500/5 dark:from-primary/10 dark:to-purple-500/10" />

        {/* Animated background elements */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 50, repeat: Infinity, ease: "linear" }}
            className="absolute -top-1/2 -right-1/2 w-full h-full bg-gradient-to-br from-primary/5 to-transparent rounded-full blur-3xl"
          />
        </div>

        <div className="max-w-7xl mx-auto relative">
          <div className="text-center max-w-4xl mx-auto">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
            >
              {/* Badge */}
              <div className="inline-flex items-center gap-2 bg-primary/10 px-4 py-2 rounded-full mb-6">
                <Sparkles className="h-4 w-4 text-primary" />
                <span className="text-sm font-medium text-primary">
                  Alpha Release — Try it now!
                </span>
              </div>

              <h1 className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-bold tracking-tight mb-6">
                Voice Dictation for Linux,{" "}
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-purple-600">
                  Finally Done Right
                </span>
              </h1>

              <p className="text-lg sm:text-xl md:text-2xl text-muted-foreground mb-8 max-w-3xl mx-auto">
                100% offline, privacy-first voice-to-text. Double-tap Ctrl to dictate anywhere.
                Powered by Whisper AI &amp; VOSK. Free &amp; open-source.
              </p>

              {/* CTA Buttons */}
              <div className="flex flex-col sm:flex-row gap-4 justify-center mb-12">
                <a
                  href="#install"
                  className="inline-flex items-center justify-center gap-2 bg-primary text-white dark:text-zinc-900 hover:bg-primary/90 px-8 py-4 rounded-xl text-lg font-semibold transition-all hover:scale-105 shadow-lg shadow-primary/25"
                >
                  <Download className="h-5 w-5" />
                  Install Now — It&apos;s Free
                </a>
                <a
                  href="#demo"
                  className="inline-flex items-center justify-center gap-2 bg-secondary text-secondary-foreground hover:bg-secondary/80 px-8 py-4 rounded-xl text-lg font-semibold transition-all"
                >
                  <Play className="h-5 w-5" />
                  Watch Demo
                </a>
              </div>
            </motion.div>

            {/* One-Click Install Box - Redesigned */}
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
              className="w-full max-w-6xl mx-auto px-4"
            >
              <div className="bg-gradient-to-br from-zinc-900 to-zinc-950 rounded-2xl p-6 sm:p-8 shadow-2xl border border-zinc-800/50 backdrop-blur">
                {/* Header */}
                <div className="flex items-center gap-3 mb-5">
                  <div className="flex items-center justify-center h-10 w-10 rounded-full bg-green-500/20 flex-shrink-0">
                    <Terminal className="h-5 w-5 text-green-400" />
                  </div>
                  <div className="text-left">
                    <h3 className="text-lg font-semibold text-white text-left">Quick Install</h3>
                    <p className="text-xs text-zinc-400 text-left">Copy & paste in your terminal</p>
                  </div>
                </div>

                {/* Command box */}
                <div className="bg-zinc-950/80 rounded-xl border border-zinc-800 overflow-hidden">
                  <div className="flex items-center justify-between px-4 py-2.5 border-b border-zinc-800 bg-zinc-900/50">
                    <div className="flex items-center gap-2">
                      <div className="h-2.5 w-2.5 rounded-full bg-red-500/70" />
                      <div className="h-2.5 w-2.5 rounded-full bg-yellow-500/70" />
                      <div className="h-2.5 w-2.5 rounded-full bg-green-500/70" />
                    </div>
                    <CopyButton text={oneClickInstallCommand} />
                  </div>
                  <div className="p-4 sm:p-5">
                    <pre className="font-mono text-sm sm:text-base text-green-400 text-left whitespace-pre">
                      <span className="text-zinc-500 select-none">$ </span>{oneClickInstallCommand}
                    </pre>
                  </div>
                </div>

                {/* Bottom info */}
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mt-5 pt-5 border-t border-zinc-800/50">
                  <p className="text-sm text-zinc-400">
                    <span className="text-zinc-500">Compatible:</span> Ubuntu, Fedora, Debian, Arch & more
                  </p>
                  <div className="flex items-center gap-4 text-xs text-zinc-500">
                    <span className="flex items-center gap-1.5">
                      <CheckCircle2 className="h-3.5 w-3.5 text-green-500" />
                      No sudo required
                    </span>
                    <span className="flex items-center gap-1.5">
                      <Zap className="h-3.5 w-3.5 text-yellow-500" />
                      ~5-10 min
                    </span>
                  </div>
                </div>
              </div>
            </motion.div>

            {/* Trust indicators */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.6, delay: 0.4 }}
              className="flex flex-wrap justify-center items-center gap-6 sm:gap-10 mt-12 text-sm text-muted-foreground"
            >
              <div className="flex items-center gap-2">
                <Shield className="h-5 w-5 text-green-500" />
                <span>100% Offline</span>
              </div>
              <div className="flex items-center gap-2">
                <Lock className="h-5 w-5 text-blue-500" />
                <span>Privacy First</span>
              </div>
              <div className="flex items-center gap-2">
                <Code className="h-5 w-5 text-purple-500" />
                <span>Open Source (GPL-3.0)</span>
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
      <section id="demo" className="py-16 sm:py-24 px-4 sm:px-6 bg-zinc-50 dark:bg-zinc-900/50">
        <div className="max-w-6xl mx-auto">
          <FadeInSection>
            <div className="text-center mb-12">
              <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold mb-4">
                Try It Yourself
              </h2>
              <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
                Experience voice-to-text right here in your browser. Click the microphone and start speaking!
              </p>
            </div>
          </FadeInSection>

          <FadeInSection delay={0.1}>
            <LiveDemo />
          </FadeInSection>

          {/* Key demo points */}
          <FadeInSection delay={0.2}>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-12">
              {[
                {
                  icon: <Keyboard className="h-6 w-6 text-primary" />,
                  title: "Double-tap Ctrl",
                  description: "In the real app, just double-tap Ctrl to start dictating anywhere",
                },
                {
                  icon: <Zap className="h-6 w-6 text-primary" />,
                  title: "Real-time Transcription",
                  description: "See your words appear as you speak with minimal latency",
                },
                {
                  icon: <Volume2 className="h-6 w-6 text-primary" />,
                  title: "Audio Feedback",
                  description: "Subtle sounds let you know when recording starts and stops",
                },
              ].map((item, i) => (
                <div
                  key={i}
                  className="flex items-start gap-4 p-4 rounded-xl bg-white dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700"
                >
                  <div className="bg-primary/10 p-2 rounded-lg">{item.icon}</div>
                  <div>
                    <h3 className="font-semibold mb-1">{item.title}</h3>
                    <p className="text-sm text-muted-foreground">{item.description}</p>
                  </div>
                </div>
              ))}
            </div>
          </FadeInSection>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-16 sm:py-24 px-4 sm:px-6">
        <div className="max-w-7xl mx-auto">
          <FadeInSection>
            <div className="text-center mb-16">
              <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold mb-4">
                Why Choose Vocalinux?
              </h2>
              <p className="text-lg text-muted-foreground max-w-3xl mx-auto">
                Finally, Linux users get the voice dictation experience they deserve —
                no compromises on privacy, no cloud dependencies, just pure productivity.
              </p>
            </div>
          </FadeInSection>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            <FeatureCard
              icon={<Shield className="h-6 w-6 text-primary" />}
              title="100% Offline & Private"
              description="All processing happens on your machine. Your voice data never leaves your computer — complete privacy guaranteed."
            />
            <FeatureCard
              icon={<Laptop className="h-6 w-6 text-primary" />}
              title="Universal App Support"
              description="Works everywhere — terminals, browsers, IDEs, office apps, and any text input field on your Linux system."
            />
            <FeatureCard
              icon={<Zap className="h-6 w-6 text-primary" />}
              title="Blazing Fast"
              description="Optimized for real-time transcription. Choose from Whisper AI (accurate) or VOSK (lightweight) engines."
            />
            <FeatureCard
              icon={<Keyboard className="h-6 w-6 text-primary" />}
              title="Simple Activation"
              description="Double-tap Ctrl to start, double-tap again to stop. No complex keyboard shortcuts to memorize."
            />
            <FeatureCard
              icon={<Globe className="h-6 w-6 text-primary" />}
              title="X11 & Wayland Support"
              description="Works seamlessly with both display servers. Modern Wayland and traditional X11 — we've got you covered."
            />
            <FeatureCard
              icon={<Settings className="h-6 w-6 text-primary" />}
              title="Fully Configurable"
              description="Adjust model size, language, activation method, and more. GUI settings panel or config file — your choice."
            />
          </div>

          {/* Comparison highlight */}
          <FadeInSection delay={0.2}>
            <div className="mt-16 bg-gradient-to-r from-primary/10 via-purple-500/10 to-primary/10 rounded-2xl p-8 sm:p-12">
              <div className="grid md:grid-cols-2 gap-8 items-center">
                <div>
                  <h3 className="text-2xl sm:text-3xl font-bold mb-4">
                    The Linux Voice Gap, Solved
                  </h3>
                  <p className="text-muted-foreground mb-6">
                    While macOS and Windows have had built-in voice dictation for years,
                    Linux users have been left behind — until now.
                  </p>
                  <ul className="space-y-3">
                    {[
                      "No more cloud services that compromise privacy",
                      "No more janky solutions that only work in specific apps",
                      "No more complicated setup processes",
                      "Just install and start dictating",
                    ].map((item, i) => (
                      <li key={i} className="flex items-start gap-3">
                        <CheckCircle2 className="h-5 w-5 text-green-500 flex-shrink-0 mt-0.5" />
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                </div>
                <div className="flex justify-center">
                  <div className="relative">
                    <div className="bg-white dark:bg-zinc-800 rounded-2xl p-8 shadow-xl">
                      <div className="flex items-center gap-4 mb-6">
                        <Image src="/vocalinux.svg" alt="Vocalinux" width={64} height={64} className="h-16 w-16" />
                        <div>
                          <div className="text-2xl font-bold">Vocalinux</div>
                          <div className="text-sm text-muted-foreground">
                            Voice dictation, finally
                          </div>
                        </div>
                      </div>
                      <div className="grid grid-cols-2 gap-4 text-center">
                        <div className="p-3 bg-zinc-50 dark:bg-zinc-900 rounded-lg">
                          <div className="text-2xl font-bold text-primary">0</div>
                          <div className="text-xs text-muted-foreground">Cloud calls</div>
                        </div>
                        <div className="p-3 bg-zinc-50 dark:bg-zinc-900 rounded-lg">
                          <div className="text-2xl font-bold text-primary">∞</div>
                          <div className="text-xs text-muted-foreground">Privacy</div>
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
      <section id="install" className="py-16 sm:py-24 px-4 sm:px-6 bg-zinc-50 dark:bg-zinc-900/50">
        <div className="max-w-4xl mx-auto">
          <FadeInSection>
            <div className="text-center mb-12">
              <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold mb-4">
                Get Started in Seconds
              </h2>
              <p className="text-lg text-muted-foreground">
                One command. That&apos;s all it takes.
              </p>
            </div>
          </FadeInSection>

          <FadeInSection delay={0.1}>
            <div className="bg-white dark:bg-zinc-800 rounded-2xl shadow-xl overflow-hidden border border-zinc-200 dark:border-zinc-700 min-w-0">
              <div className="p-6 sm:p-8">
                {/* Primary install option */}
                <div className="mb-8">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="bg-green-500/10 p-2 rounded-lg">
                      <Sparkles className="h-5 w-5 text-green-500" />
                    </div>
                    <div className="flex-1">
                      <h3 className="text-xl font-semibold">Recommended: Full Install</h3>
                      <p className="text-sm text-muted-foreground">
                        Includes Whisper AI for best accuracy (~5-10 min)
                      </p>
                    </div>
                    <CopyButton text={oneClickInstallCommand} />
                  </div>
                  <div className="overflow-x-auto">
                    <SyntaxHighlighter
                      language="bash"
                      style={atomOneDark}
                      className="rounded-lg text-sm sm:text-base"
                      customStyle={{ margin: 0, maxWidth: '100%', overflowX: 'auto' }}
                      wrapLongLines={false}
                    >
                      {oneClickInstallCommand}
                    </SyntaxHighlighter>
                  </div>
                </div>

                {/* Alternative install - CPU only */}
                <div className="border-t border-zinc-200 dark:border-zinc-700 pt-6">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="bg-blue-500/10 p-2 rounded-lg">
                      <Cpu className="h-5 w-5 text-blue-500" />
                    </div>
                    <div className="flex-1">
                      <h3 className="text-lg font-semibold">Whisper CPU-only</h3>
                      <p className="text-sm text-muted-foreground">
                        Smaller download (~200MB vs ~2.3GB) - no NVIDIA GPU needed (~3-4 min)
                      </p>
                    </div>
                    <CopyButton text={oneClickInstallWhisperCpu} />
                  </div>
                  <div className="overflow-x-auto">
                    <SyntaxHighlighter
                      language="bash"
                      style={atomOneDark}
                      className="rounded-lg text-sm"
                      customStyle={{ margin: 0, maxWidth: '100%', overflowX: 'auto' }}
                      wrapLongLines={false}
                    >
                      {oneClickInstallWhisperCpu}
                    </SyntaxHighlighter>
                  </div>
                </div>

                {/* Alternative install - VOSK only */}
                <div className="border-t border-zinc-200 dark:border-zinc-700 pt-6">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="bg-green-500/10 p-2 rounded-lg">
                      <Zap className="h-5 w-5 text-green-500" />
                    </div>
                    <div className="flex-1">
                      <h3 className="text-lg font-semibold">VOSK only (lightest)</h3>
                      <p className="text-sm text-muted-foreground">
                        For low-RAM systems (8GB or less) - skips Whisper entirely (~2-3 min)
                      </p>
                    </div>
                    <CopyButton text={oneClickInstallNoWhisper} />
                  </div>
                  <div className="overflow-x-auto">
                    <SyntaxHighlighter
                      language="bash"
                      style={atomOneDark}
                      className="rounded-lg text-sm"
                      customStyle={{ margin: 0, maxWidth: '100%', overflowX: 'auto' }}
                      wrapLongLines={false}
                    >
                      {oneClickInstallNoWhisper}
                    </SyntaxHighlighter>
                  </div>
                </div>

                {/* What the installer does */}
                <div className="mt-8 p-4 bg-zinc-50 dark:bg-zinc-900 rounded-lg">
                  <h4 className="font-semibold mb-3">What the installer does:</h4>
                  <ul className="grid sm:grid-cols-2 gap-2 text-sm text-muted-foreground">
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
                <div className="mt-6 p-4 bg-primary/5 rounded-lg border border-primary/20">
                  <h4 className="font-semibold mb-2 flex items-center gap-2">
                    <Play className="h-4 w-4 text-primary" />
                    After Installation
                  </h4>
                  <p className="text-sm text-muted-foreground mb-3">
                    Launch Vocalinux from your terminal or application menu:
                  </p>
                  <code className="block bg-zinc-900 text-green-400 px-4 py-2 rounded text-sm">
                    vocalinux
                  </code>
                </div>
              </div>
            </div>
          </FadeInSection>

          {/* System requirements */}
          <FadeInSection delay={0.2}>
            <div className="mt-8 grid sm:grid-cols-2 gap-6">
              <div className="bg-white dark:bg-zinc-800 p-6 rounded-xl border border-zinc-200 dark:border-zinc-700 min-w-0">
                <h4 className="font-semibold mb-4 flex items-center gap-2">
                  <Cpu className="h-5 w-5 text-primary" />
                  System Requirements
                </h4>
                <ul className="space-y-2 text-sm text-muted-foreground">
                  <li>• Ubuntu 22.04+ (or equivalent)</li>
                  <li>• Python 3.8 or newer</li>
                  <li>• 4GB RAM (8GB for large models)</li>
                  <li>• Microphone</li>
                  <li>• X11 or Wayland display server</li>
                </ul>
              </div>
              <div className="bg-white dark:bg-zinc-800 p-6 rounded-xl border border-zinc-200 dark:border-zinc-700 min-w-0">
                <div className="flex items-center gap-3 mb-4">
                  <div className="bg-red-500/10 p-2 rounded-lg">
                    <Terminal className="h-5 w-5 text-red-500" />
                  </div>
                  <div className="flex-1">
                    <h4 className="font-semibold">Uninstall</h4>
                    <p className="text-sm text-muted-foreground">
                      Clean removal in one command
                    </p>
                  </div>
                  <CopyButton text={uninstallCommand} />
                </div>
                <div className="overflow-x-auto">
                  <SyntaxHighlighter
                    language="bash"
                    style={atomOneDark}
                    className="rounded-lg text-sm"
                    customStyle={{ margin: 0, maxWidth: '100%', overflowX: 'auto' }}
                    wrapLongLines={false}
                  >
                    {uninstallCommand}
                  </SyntaxHighlighter>
                </div>
              </div>
            </div>
          </FadeInSection>
        </div>
      </section>

      {/* Voice Commands Section */}
      <section id="voice-commands" className="py-16 sm:py-24 px-4 sm:px-6">
        <div className="max-w-5xl mx-auto">
          <FadeInSection>
            <div className="text-center mb-12">
              <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold mb-4">
                Built-in Voice Commands
              </h2>
              <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
                Go beyond basic dictation with natural voice commands for punctuation, formatting, and editing.
              </p>
            </div>
          </FadeInSection>

          <div className="grid md:grid-cols-2 gap-8">
            <FadeInSection delay={0.1}>
              <div className="bg-white dark:bg-zinc-800 rounded-xl p-6 border border-zinc-200 dark:border-zinc-700 h-full">
                <h3 className="text-xl font-semibold mb-6 flex items-center gap-2">
                  <Edit className="h-5 w-5 text-primary" />
                  Punctuation &amp; Formatting
                </h3>
                <div className="space-y-3">
                  {[
                    { command: '"new line"', result: "Inserts a line break" },
                    { command: '"period" / "full stop"', result: "Types a period (.)" },
                    { command: '"comma"', result: "Types a comma (,)" },
                    { command: '"question mark"', result: "Types a question mark (?)" },
                    { command: '"exclamation mark"', result: "Types an exclamation mark (!)" },
                    { command: '"colon"', result: "Types a colon (:)" },
                    { command: '"semicolon"', result: "Types a semicolon (;)" },
                    { command: '"new paragraph"', result: "Inserts two line breaks" },
                  ].map((item, i) => (
                    <div key={i} className="flex justify-between items-center py-2 border-b border-zinc-100 dark:border-zinc-700 last:border-0">
                      <code className="text-sm bg-zinc-100 dark:bg-zinc-900 px-2 py-1 rounded">
                        {item.command}
                      </code>
                      <span className="text-sm text-muted-foreground">{item.result}</span>
                    </div>
                  ))}
                </div>
              </div>
            </FadeInSection>

            <FadeInSection delay={0.2}>
              <div className="bg-white dark:bg-zinc-800 rounded-xl p-6 border border-zinc-200 dark:border-zinc-700 h-full">
                <h3 className="text-xl font-semibold mb-6 flex items-center gap-2">
                  <Terminal className="h-5 w-5 text-primary" />
                  Editing Commands
                </h3>
                <div className="space-y-3">
                  {[
                    { command: '"delete that"', result: "Deletes the last phrase" },
                    { command: '"backspace"', result: "Deletes previous character" },
                    { command: '"undo"', result: "Undoes last action" },
                    { command: '"redo"', result: "Redoes last action" },
                    { command: '"select all"', result: "Selects all text" },
                    { command: '"copy"', result: "Copies selected text" },
                    { command: '"paste"', result: "Pastes from clipboard" },
                    { command: '"capitalize"', result: "Capitalizes next word" },
                  ].map((item, i) => (
                    <div key={i} className="flex justify-between items-center py-2 border-b border-zinc-100 dark:border-zinc-700 last:border-0">
                      <code className="text-sm bg-zinc-100 dark:bg-zinc-900 px-2 py-1 rounded">
                        {item.command}
                      </code>
                      <span className="text-sm text-muted-foreground">{item.result}</span>
                    </div>
                  ))}
                </div>
              </div>
            </FadeInSection>
          </div>
        </div>
      </section>

      {/* Speech Engines Section */}
      <section className="py-16 sm:py-24 px-4 sm:px-6 bg-zinc-50 dark:bg-zinc-900/50">
        <div className="max-w-5xl mx-auto">
          <FadeInSection>
            <div className="text-center mb-12">
              <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold mb-4">
                Choose Your Engine
              </h2>
              <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
                Vocalinux supports multiple speech recognition engines. Pick the one that suits your needs.
              </p>
            </div>
          </FadeInSection>

          <div className="grid md:grid-cols-2 gap-8">
            <FadeInSection delay={0.1}>
              <div className="bg-white dark:bg-zinc-800 rounded-xl p-6 border-2 border-primary h-full relative overflow-hidden">
                <div className="absolute top-4 right-4">
                  <span className="bg-primary text-primary-foreground text-xs font-semibold px-2 py-1 rounded">
                    DEFAULT
                  </span>
                </div>
                <div className="flex items-center gap-3 mb-4">
                  <div className="bg-primary/10 p-3 rounded-lg">
                    <Sparkles className="h-6 w-6 text-primary" />
                  </div>
                  <h3 className="text-xl font-bold">Whisper AI</h3>
                </div>
                <p className="text-muted-foreground mb-6">
                  OpenAI&apos;s state-of-the-art speech recognition model, running locally on your machine.
                </p>
                <ul className="space-y-2 mb-6">
                  {[
                    "Highest accuracy available",
                    "Multiple model sizes (tiny to large)",
                    "Excellent multi-language support",
                    "Best for clear, accurate transcription",
                  ].map((item, i) => (
                    <li key={i} className="flex items-center gap-2 text-sm">
                      <CheckCircle2 className="h-4 w-4 text-green-500" />
                      {item}
                    </li>
                  ))}
                </ul>
                <div className="text-sm text-muted-foreground">
                  <strong>Model sizes:</strong> Tiny (75MB) • Base (142MB) • Small (466MB) • Medium (1.5GB) • Large (3GB)
                </div>
              </div>
            </FadeInSection>

            <FadeInSection delay={0.2}>
              <div className="bg-white dark:bg-zinc-800 rounded-xl p-6 border border-zinc-200 dark:border-zinc-700 h-full">
                <div className="flex items-center gap-3 mb-4">
                  <div className="bg-blue-500/10 p-3 rounded-lg">
                    <Zap className="h-6 w-6 text-blue-500" />
                  </div>
                  <h3 className="text-xl font-bold">VOSK</h3>
                </div>
                <p className="text-muted-foreground mb-6">
                  Lightweight, fast speech recognition engine perfect for lower-powered systems.
                </p>
                <ul className="space-y-2 mb-6">
                  {[
                    "Very lightweight and fast",
                    "Low memory footprint",
                    "Great for real-time streaming",
                    "Good for basic transcription needs",
                  ].map((item, i) => (
                    <li key={i} className="flex items-center gap-2 text-sm">
                      <CheckCircle2 className="h-4 w-4 text-blue-500" />
                      {item}
                    </li>
                  ))}
                </ul>
                <div className="text-sm text-muted-foreground">
                  <strong>Footprint:</strong> ~50MB model, minimal CPU/RAM usage
                </div>
              </div>
            </FadeInSection>
          </div>
        </div>
      </section>

      {/* FAQ Section */}
      <section id="faq" className="py-16 sm:py-24 px-4 sm:px-6">
        <div className="max-w-3xl mx-auto">
          <FadeInSection>
            <div className="text-center mb-12">
              <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold mb-4">
                Frequently Asked Questions
              </h2>
            </div>
          </FadeInSection>

          <div className="space-y-4">
            {[
              {
                question: "Is Vocalinux really 100% offline?",
                answer:
                  "Yes! All speech recognition processing happens locally on your machine. Your voice data never leaves your computer. No internet connection is required after installation (models are downloaded during setup).",
              },
              {
                question: "Which Linux distributions are supported?",
                answer:
                  "Vocalinux works on most modern Linux distributions including Ubuntu 22.04+, Fedora, Debian, Arch Linux, Linux Mint, Pop!_OS, and more. It supports both X11 and Wayland display servers.",
              },
              {
                question: "How do I switch between Whisper and VOSK?",
                answer:
                  'You can switch engines via the settings GUI or command line. Use "vocalinux --engine whisper" or "vocalinux --engine vosk". Whisper is recommended for accuracy, VOSK for speed.',
              },
              {
                question: "What are the system requirements?",
                answer:
                  "Minimum: 4GB RAM, dual-core CPU, Python 3.8+. For Whisper large models: 8GB+ RAM recommended. The tiny/base Whisper models and VOSK work great on modest hardware.",
              },
              {
                question: "Can I use it in languages other than English?",
                answer:
                  "Yes! Whisper supports 99+ languages with varying accuracy levels. VOSK has models for 20+ languages. Download additional language models as needed.",
              },
              {
                question: "How do I customize the activation shortcut?",
                answer:
                  "The default is double-tap Ctrl. You can customize this via the GUI settings dialog or by editing ~/.config/vocalinux/config.yaml. Any key combination is supported.",
              },
              {
                question: "Is Vocalinux free?",
                answer:
                  "Yes, Vocalinux is completely free and open-source, licensed under GPL-3.0. No premium tiers, no subscriptions, no tracking — just free software.",
              },
            ].map((item, i) => (
              <FadeInSection key={i} delay={i * 0.05}>
                <details className="group bg-white dark:bg-zinc-800 rounded-xl border border-zinc-200 dark:border-zinc-700">
                  <summary className="flex items-center justify-between p-6 cursor-pointer list-none">
                    <h3 className="font-semibold pr-4">{item.question}</h3>
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

      {/* CTA Section */}
      <section className="py-16 sm:py-24 px-4 sm:px-6 bg-gradient-to-br from-primary/10 via-purple-500/10 to-primary/10">
        <div className="max-w-4xl mx-auto text-center">
          <FadeInSection>
            <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold mb-6">
              Ready to Ditch Your Keyboard?
            </h2>
            <p className="text-lg text-muted-foreground mb-8 max-w-2xl mx-auto">
              Join the growing community of Linux users who have discovered the power of voice dictation.
              It&apos;s free, it&apos;s private, and it just works.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <a
                href="#install"
                className="inline-flex items-center justify-center gap-2 bg-primary text-white dark:text-zinc-900 hover:bg-primary/90 px-8 py-4 rounded-xl text-lg font-semibold transition-all hover:scale-105 shadow-lg shadow-primary/25"
              >
                <Download className="h-5 w-5" />
                Install Vocalinux
              </a>
              <a
                href="https://github.com/jatinkrmalik/vocalinux"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center justify-center gap-2 bg-zinc-900 text-white hover:bg-zinc-800 px-8 py-4 rounded-xl text-lg font-semibold transition-all"
              >
                <Star className="h-5 w-5" />
                Star on GitHub
              </a>
            </div>
          </FadeInSection>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-4 sm:px-6 bg-zinc-900 text-white">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-8 mb-12">
            <div className="md:col-span-2">
              <Link href="/" className="flex items-center gap-2 mb-4">
                <Image src="/vocalinux.svg" alt="Vocalinux" width={32} height={32} className="h-8 w-8" />
                <span className="text-xl font-bold">Vocalinux</span>
              </Link>
              <p className="text-zinc-400 mb-4 max-w-md">
                Free, open-source voice dictation for Linux. 100% offline and privacy-focused.
              </p>
              <div className="flex items-center gap-4">
                <a
                  href="https://github.com/jatinkrmalik/vocalinux"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-zinc-400 hover:text-white transition-colors"
                  aria-label="GitHub"
                >
                  <Github className="h-6 w-6" />
                </a>
              </div>
            </div>

            <div>
              <h3 className="font-semibold mb-4">Quick Links</h3>
              <ul className="space-y-2 text-sm">
                <li>
                  <a href="#features" className="text-zinc-400 hover:text-white transition-colors">
                    Features
                  </a>
                </li>
                <li>
                  <a href="#install" className="text-zinc-400 hover:text-white transition-colors">
                    Installation
                  </a>
                </li>
                <li>
                  <a href="#voice-commands" className="text-zinc-400 hover:text-white transition-colors">
                    Voice Commands
                  </a>
                </li>
                <li>
                  <a href="#faq" className="text-zinc-400 hover:text-white transition-colors">
                    FAQ
                  </a>
                </li>
              </ul>
            </div>

            <div>
              <h3 className="font-semibold mb-4">Resources</h3>
              <ul className="space-y-2 text-sm">
                <li>
                  <a
                    href="https://github.com/jatinkrmalik/vocalinux"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-zinc-400 hover:text-white transition-colors"
                  >
                    GitHub Repository
                  </a>
                </li>
                <li>
                  <a
                    href="https://github.com/jatinkrmalik/vocalinux/issues"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-zinc-400 hover:text-white transition-colors"
                  >
                    Report Issues
                  </a>
                </li>
                <li>
                  <a
                    href="https://github.com/jatinkrmalik/vocalinux/discussions"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-zinc-400 hover:text-white transition-colors"
                  >
                    Discussions
                  </a>
                </li>
                <li>
                  <a
                    href="https://github.com/jatinkrmalik/vocalinux/blob/main/CONTRIBUTING.md"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-zinc-400 hover:text-white transition-colors"
                  >
                    Contributing
                  </a>
                </li>
              </ul>
            </div>
          </div>

          <div className="pt-8 border-t border-zinc-800 flex flex-col sm:flex-row justify-between items-center gap-4">
            <p className="text-zinc-500 text-sm">
              © {new Date().getFullYear()} Vocalinux. Open-source under GPL-3.0 License.
            </p>
            <p className="text-zinc-500 text-sm flex items-center gap-1">
              Made with <Heart className="h-4 w-4 text-red-500" /> by{" "}
              <a
                href="https://x.com/intent/user?screen_name=jatinkrmalik"
                target="_blank"
                rel="noopener noreferrer"
                className="text-zinc-400 hover:text-white transition-colors"
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
