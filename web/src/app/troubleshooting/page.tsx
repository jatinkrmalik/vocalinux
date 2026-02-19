import Link from "next/link";
import { type Metadata } from "next";
import { AlertTriangle, CheckCircle2, ChevronRight, ExternalLink, Lightbulb, Terminal, Wrench } from "lucide-react";
import { SeoSubpageShell } from "@/components/seo-subpage-shell";
import { absoluteUrl, buildPageMetadata } from "@/lib/seo";

const troubleshootingItems = [
  {
    title: "Vocalinux won't start",
    symptoms: ["Command not found", "Module import errors", "Application crashes on launch"],
    solutions: [
      "Ensure you ran the installer: curl -fsSL https://raw.githubusercontent.com/jatinkrmalik/vocalinux/main/install.sh | bash",
      "Check if the virtual environment is activated: source ~/.local/share/vocalinux/venv/bin/activate",
      "Verify Python version (3.8+ required): python3 --version",
      "Try reinstalling: ./uninstall.sh && ./install.sh",
    ],
  },
  {
    title: "No audio detected / microphone not working",
    symptoms: ["Dictation shows no text", "Audio level indicator stays at zero"],
    solutions: [
      "Check microphone permissions in your system settings",
      "Verify microphone is detected: arecord -l (Linux)",
      "Test microphone recording: arecord -d 3 test.wav && aplay test.wav",
      "Ensure no other application is using the microphone",
      "Check PulseAudio/PipeWire settings: pavucontrol",
    ],
  },
  {
    title: "Text not appearing in applications",
    symptoms: ["Dictation works but text doesn't appear", "Text injection fails"],
    solutions: [
      "For Wayland: Ensure IBus is running and Vocalinux IBus is configured",
      "For X11: Verify xdotool is installed: sudo apt install xdotool",
      "Check if the target application has focus",
      "Try a different application (terminal, text editor) to isolate the issue",
      "Restart Vocalinux after changing display servers",
    ],
  },
  {
    title: "High CPU/GPU usage",
    symptoms: ["System slowdown during dictation", "Fan noise", "Laggy response"],
    solutions: [
      "Use a smaller model (tiny or base instead of medium/large)",
      "Enable GPU acceleration if available (Vulkan for AMD/Intel, CUDA for NVIDIA)",
      "Switch to VOSK engine for lower resource usage",
      "Reduce audio sample rate in settings",
    ],
  },
  {
    title: "Poor transcription accuracy",
    symptoms: ["Many transcription errors", "Wrong words", "Garbled text"],
    solutions: [
      "Use a larger model (small → medium → large) for better accuracy",
      "Ensure microphone is positioned correctly and not too far",
      "Reduce background noise",
      "Speak clearly and at a moderate pace",
      "Try a different speech engine (whisper.cpp vs VOSK)",
      "Set the correct language in settings",
    ],
  },
  {
    title: "Installation fails",
    symptoms: ["Dependency errors", "Package not found", "Permission denied"],
    solutions: [
      "Ensure you have internet connectivity for downloading dependencies",
      "Run with sufficient permissions (don't use sudo unless specifically needed)",
      "Check your distribution is supported (Ubuntu 22.04+, Fedora 39+, Arch)",
      "Install system dependencies manually: sudo apt install python3-pip python3-gi python3-venv",
      "Check disk space: df -h",
    ],
  },
  {
    title: "Keyboard shortcut not working",
    symptoms: ["Double-tap Ctrl doesn't start dictation", "Custom shortcuts ignored"],
    solutions: [
      "Check if another application is capturing the shortcut",
      "Verify Vocalinux is running (check system tray)",
      "Try changing the shortcut in Settings",
      "On Wayland, ensure keyboard shortcuts are not blocked by compositor settings",
    ],
  },
  {
    title: "Tray icon not appearing",
    symptoms: ["No system tray icon", "Cannot access settings"],
    solutions: [
      "Ensure your desktop environment supports system trays (GNOME requires extension)",
      "Install AppIndicator extension for GNOME: sudo apt install gnome-shell-extension-appindicator",
      "Check if ayatana-appindicator is installed: sudo apt install libayatana-appindicator3-1",
      "Try launching from terminal to see any errors: vocalinux --debug",
    ],
  },
];

export const metadata: Metadata = buildPageMetadata({
  title: "Troubleshooting Guide - Vocalinux Voice Dictation",
  description:
    "Fix common Vocalinux issues: microphone problems, text injection, installation errors, and performance. Step-by-step solutions for Linux voice dictation.",
  path: "/troubleshooting",
  keywords: [
    "vocalinux troubleshooting",
    "linux voice dictation problems",
    "speech to text not working",
    "microphone issues linux",
  ],
});

export default function TroubleshootingPage() {
  const articleJsonLd = {
    "@context": "https://schema.org",
    "@type": "Article",
    headline: "Vocalinux Troubleshooting Guide",
    description:
      "Complete troubleshooting guide for Vocalinux Linux voice dictation software.",
    dateModified: "2026-02-19",
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
    mainEntityOfPage: absoluteUrl("/troubleshooting"),
  };

  return (
    <SeoSubpageShell>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(articleJsonLd) }}
      />

      <section>
        <p className="mb-4 inline-flex items-center gap-2 rounded-full border border-amber-500/30 bg-amber-500/10 px-4 py-1.5 text-sm font-medium text-amber-600 dark:text-amber-400">
          <Wrench className="h-4 w-4" />
          Support Guide
        </p>
        <h1 className="mb-5 text-4xl font-bold tracking-tight sm:text-5xl md:text-6xl">
          Troubleshooting Guide
        </h1>
        <p className="mb-8 max-w-4xl text-lg text-muted-foreground">
          Having issues with Vocalinux? Find solutions to common problems below. Can't find your
          issue? Open a GitHub issue for help.
        </p>
      </section>

      <section className="mb-12 rounded-2xl border border-zinc-200 bg-white p-6 dark:border-zinc-700 dark:bg-zinc-800">
        <h2 className="mb-4 flex items-center gap-2 text-xl font-bold">
          <Terminal className="h-5 w-5 text-green-500" />
          Quick Debug Command
        </h2>
        <p className="mb-4 text-sm text-muted-foreground">
          Run Vocalinux with debug output to see detailed logs:
        </p>
        <div className="rounded-lg bg-zinc-950 p-4">
          <code className="text-sm text-green-400">vocalinux --debug</code>
        </div>
      </section>

      <section className="space-y-6">
        {troubleshootingItems.map((item) => (
          <article
            key={item.title}
            className="rounded-2xl border border-zinc-200 bg-white p-6 dark:border-zinc-700 dark:bg-zinc-800"
          >
            <h2 className="mb-4 text-xl font-bold">{item.title}</h2>

            <div className="mb-4 rounded-lg bg-amber-50 p-4 dark:bg-amber-900/20">
              <p className="mb-2 flex items-center gap-2 text-sm font-semibold text-amber-700 dark:text-amber-400">
                <AlertTriangle className="h-4 w-4" />
                Symptoms
              </p>
              <ul className="ml-6 list-disc text-sm text-amber-600 dark:text-amber-300">
                {item.symptoms.map((symptom) => (
                  <li key={symptom}>{symptom}</li>
                ))}
              </ul>
            </div>

            <div className="rounded-lg bg-green-50 p-4 dark:bg-green-900/20">
              <p className="mb-2 flex items-center gap-2 text-sm font-semibold text-green-700 dark:text-green-400">
                <CheckCircle2 className="h-4 w-4" />
                Solutions
              </p>
              <ul className="ml-6 list-disc text-sm text-green-600 dark:text-green-300">
                {item.solutions.map((solution) => (
                  <li key={solution}>{solution}</li>
                ))}
              </ul>
            </div>
          </article>
        ))}
      </section>

      <section className="mt-12 rounded-2xl border border-zinc-200 bg-zinc-50 p-8 dark:border-zinc-700 dark:bg-zinc-900/60">
        <h2 className="mb-4 flex items-center gap-2 text-2xl font-bold">
          <Lightbulb className="h-5 w-5 text-amber-500" />
          Still having issues?
        </h2>
        <ul className="space-y-3 text-muted-foreground">
          <li className="inline-flex items-center gap-2">
            <ChevronRight className="h-4 w-4 text-primary" />
            Check the{" "}
            <Link href="/faq/" className="font-semibold text-primary hover:underline">
              FAQ page
            </Link>{" "}
            for common questions
          </li>
          <li className="inline-flex items-center gap-2">
            <ChevronRight className="h-4 w-4 text-primary" />
            <a
              href="https://github.com/jatinkrmalik/vocalinux/issues"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 font-semibold text-primary hover:underline"
            >
              Search existing issues on GitHub
              <ExternalLink className="h-3.5 w-3.5" />
            </a>
          </li>
          <li className="inline-flex items-center gap-2">
            <ChevronRight className="h-4 w-4 text-primary" />
            <a
              href="https://github.com/jatinkrmalik/vocalinux/issues/new"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 font-semibold text-primary hover:underline"
            >
              Open a new issue (include debug logs)
              <ExternalLink className="h-3.5 w-3.5" />
            </a>
          </li>
        </ul>
      </section>
    </SeoSubpageShell>
  );
}
