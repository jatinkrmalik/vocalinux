import Link from "next/link";
import { type Metadata } from "next";
import { CheckCircle2, Lock, Server, Shield, Eye, Database, ExternalLink } from "lucide-react";
import { SeoSubpageShell } from "@/components/seo-subpage-shell";
import { absoluteUrl, buildPageMetadata } from "@/lib/seo";

export const metadata: Metadata = buildPageMetadata({
  title: "Privacy Policy - 100% Offline Voice Dictation",
  description:
    "Vocalinux is 100% offline. Your voice data never leaves your computer. Learn about our privacy-first approach to Linux voice dictation.",
  path: "/privacy",
  keywords: [
    "vocalinux privacy",
    "offline voice dictation privacy",
    "speech to text data privacy",
    "linux dictation security",
  ],
});

export default function PrivacyPage() {
  const articleJsonLd = {
    "@context": "https://schema.org",
    "@type": "Article",
    headline: "Vocalinux Privacy Policy - 100% Offline Voice Dictation",
    description:
      "Complete privacy policy for Vocalinux, the offline voice dictation software for Linux.",
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
    mainEntityOfPage: absoluteUrl("/privacy"),
  };

  return (
    <SeoSubpageShell>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(articleJsonLd) }}
      />

      <section>
        <p className="mb-4 inline-flex items-center gap-2 rounded-full border border-green-500/30 bg-green-500/10 px-4 py-1.5 text-sm font-medium text-green-600 dark:text-green-400">
          <Shield className="h-4 w-4" />
          Privacy First
        </p>
        <h1 className="mb-5 text-4xl font-bold tracking-tight sm:text-5xl md:text-6xl">
          Your Voice Stays on Your Computer
        </h1>
        <p className="mb-8 max-w-4xl text-lg text-muted-foreground">
          Vocalinux is built from the ground up for privacy. All speech recognition happens locally,
          with zero cloud processing. Your voice data never leaves your machine.
        </p>
      </section>

      {/* Key Privacy Points */}
      <section className="mb-12 grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        <article className="rounded-2xl border border-zinc-200 bg-white p-6 dark:border-zinc-700 dark:bg-zinc-800">
          <div className="mb-4 inline-flex rounded-xl bg-green-100 p-3 dark:bg-green-900/30">
            <Lock className="h-6 w-6 text-green-600 dark:text-green-400" />
          </div>
          <h3 className="mb-2 text-xl font-semibold">100% Offline</h3>
          <p className="text-sm text-muted-foreground">
            No internet connection required after installation. All processing happens on your
            device, period.
          </p>
        </article>

        <article className="rounded-2xl border border-zinc-200 bg-white p-6 dark:border-zinc-700 dark:bg-zinc-800">
          <div className="mb-4 inline-flex rounded-xl bg-blue-100 p-3 dark:bg-blue-900/30">
            <Server className="h-6 w-6 text-blue-600 dark:text-blue-400" />
          </div>
          <h3 className="mb-2 text-xl font-semibold">No Cloud Processing</h3>
          <p className="text-sm text-muted-foreground">
            Unlike Dragon, Otter, or Google Dictation, we don't send your voice to any servers.
            Everything stays local.
          </p>
        </article>

        <article className="rounded-2xl border border-zinc-200 bg-white p-6 dark:border-zinc-700 dark:bg-zinc-800">
          <div className="mb-4 inline-flex rounded-xl bg-violet-100 p-3 dark:bg-violet-900/30">
            <Eye className="h-6 w-6 text-violet-600 dark:text-violet-400" />
          </div>
          <h3 className="mb-2 text-xl font-semibold">Open Source</h3>
          <p className="text-sm text-muted-foreground">
            Fully open source under GPL-3.0. Inspect the code yourself on GitHub. No hidden
            telemetry or data collection.
          </p>
        </article>
      </section>

      {/* Detailed Privacy Sections */}
      <section className="space-y-8">
        <article className="rounded-2xl border border-zinc-200 bg-white p-6 dark:border-zinc-700 dark:bg-zinc-800">
          <h2 className="mb-4 flex items-center gap-2 text-2xl font-bold">
            <Database className="h-5 w-5 text-primary" />
            Data Collection
          </h2>
          <div className="space-y-4 text-muted-foreground">
            <p>
              <strong className="text-foreground">We do not collect any personal data.</strong> This
              includes:
            </p>
            <ul className="space-y-2">
              <li className="inline-flex items-start gap-2">
                <CheckCircle2 className="mt-0.5 h-4 w-4 flex-shrink-0 text-green-500" />
                No voice recordings or audio data
              </li>
              <li className="inline-flex items-start gap-2">
                <CheckCircle2 className="mt-0.5 h-4 w-4 flex-shrink-0 text-green-500" />
                No transcribed text
              </li>
              <li className="inline-flex items-start gap-2">
                <CheckCircle2 className="mt-0.5 h-4 w-4 flex-shrink-0 text-green-500" />
                No usage analytics or telemetry
              </li>
              <li className="inline-flex items-start gap-2">
                <CheckCircle2 className="mt-0.5 h-4 w-4 flex-shrink-0 text-green-500" />
                No device fingerprints
              </li>
              <li className="inline-flex items-start gap-2">
                <CheckCircle2 className="mt-0.5 h-4 w-4 flex-shrink-0 text-green-500" />
                No IP addresses or location data
              </li>
            </ul>
          </div>
        </article>

        <article className="rounded-2xl border border-zinc-200 bg-white p-6 dark:border-zinc-700 dark:bg-zinc-800">
          <h2 className="mb-4 flex items-center gap-2 text-2xl font-bold">
            <Shield className="h-5 w-5 text-primary" />
            How We Process Your Voice
          </h2>
          <div className="space-y-4 text-muted-foreground">
            <p>When you dictate, here's exactly what happens:</p>
            <ol className="space-y-3 pl-4">
              <li className="border-l-2 border-primary pl-4">
                <strong className="text-foreground">1. Audio Capture</strong> — Your microphone
                records audio temporarily in RAM
              </li>
              <li className="border-l-2 border-primary pl-4">
                <strong className="text-foreground">2. Local Processing</strong> — Audio is
                processed by whisper.cpp, Whisper, or VOSK on your CPU/GPU
              </li>
              <li className="border-l-2 border-primary pl-4">
                <strong className="text-foreground">3. Text Output</strong> — Transcribed text is
                injected into your active application
              </li>
              <li className="border-l-2 border-primary pl-4">
                <strong className="text-foreground">4. Immediate Deletion</strong> — Audio data is
                discarded immediately after processing
              </li>
            </ol>
            <p className="mt-4 rounded-lg bg-amber-50 p-4 text-sm dark:bg-amber-900/20">
              <strong>Note:</strong> No audio is ever written to disk or transmitted over the
              network.
            </p>
          </div>
        </article>

        <article className="rounded-2xl border border-zinc-200 bg-white p-6 dark:border-zinc-700 dark:bg-zinc-800">
          <h2 className="mb-4 flex items-center gap-2 text-2xl font-bold">
            <Lock className="h-5 w-5 text-primary" />
            Configuration Data
          </h2>
          <div className="space-y-4 text-muted-foreground">
            <p>
              Vocalinux stores configuration locally at <code className="rounded bg-zinc-100 px-1.5 py-0.5 dark:bg-zinc-700">~/.config/vocalinux/</code>:
            </p>
            <ul className="space-y-2">
              <li className="inline-flex items-start gap-2">
                <CheckCircle2 className="mt-0.5 h-4 w-4 flex-shrink-0 text-green-500" />
                Settings like preferred engine, model size, and language
              </li>
              <li className="inline-flex items-start gap-2">
                <CheckCircle2 className="mt-0.5 h-4 w-4 flex-shrink-0 text-green-500" />
                Custom keyboard shortcuts
              </li>
              <li className="inline-flex items-start gap-2">
                <CheckCircle2 className="mt-0.5 h-4 w-4 flex-shrink-0 text-green-500" />
                Window and tray preferences
              </li>
            </ul>
            <p>
              This data is stored in plain text YAML format. You can view, edit, or delete it at
              any time.
            </p>
          </div>
        </article>
      </section>

      {/* Comparison with Cloud Services */}
      <section className="mt-12 rounded-2xl border border-zinc-200 bg-zinc-50 p-8 dark:border-zinc-700 dark:bg-zinc-900/60">
        <h2 className="mb-6 text-2xl font-bold">Vocalinux vs Cloud Dictation Services</h2>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[500px] text-left">
            <thead>
              <tr className="border-b border-zinc-200 dark:border-zinc-700">
                <th className="pb-3 text-sm font-semibold">Feature</th>
                <th className="pb-3 text-sm font-semibold">Vocalinux</th>
                <th className="pb-3 text-sm font-semibold">Cloud Services</th>
              </tr>
            </thead>
            <tbody className="text-sm text-muted-foreground">
              <tr className="border-b border-zinc-100 dark:border-zinc-700/70">
                <td className="py-3 font-medium text-foreground">Data leaves device</td>
                <td className="py-3 text-green-600 dark:text-green-400">Never</td>
                <td className="py-3 text-red-600 dark:text-red-400">Always</td>
              </tr>
              <tr className="border-b border-zinc-100 dark:border-zinc-700/70">
                <td className="py-3 font-medium text-foreground">Internet required</td>
                <td className="py-3 text-green-600 dark:text-green-400">No</td>
                <td className="py-3 text-red-600 dark:text-red-400">Yes</td>
              </tr>
              <tr className="border-b border-zinc-100 dark:border-zinc-700/70">
                <td className="py-3 font-medium text-foreground">Source code available</td>
                <td className="py-3 text-green-600 dark:text-green-400">Yes (GPL-3.0)</td>
                <td className="py-3 text-red-600 dark:text-red-400">No</td>
              </tr>
              <tr className="border-b border-zinc-100 dark:border-zinc-700/70">
                <td className="py-3 font-medium text-foreground">Voice recordings stored</td>
                <td className="py-3 text-green-600 dark:text-green-400">No</td>
                <td className="py-3">Varies by service</td>
              </tr>
              <tr>
                <td className="py-3 font-medium text-foreground">Cost</td>
                <td className="py-3 text-green-600 dark:text-green-400">Free forever</td>
                <td className="py-3">Subscription</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      {/* Contact */}
      <section className="mt-12 rounded-2xl border border-zinc-200 bg-white p-6 dark:border-zinc-700 dark:bg-zinc-800">
        <h2 className="mb-4 text-xl font-bold">Questions About Privacy?</h2>
        <p className="mb-4 text-muted-foreground">
          If you have any questions about our privacy practices or want to verify our claims,
          please reach out:
        </p>
        <a
          href="https://github.com/jatinkrmalik/vocalinux/issues"
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-2 text-primary hover:underline"
        >
          Open an issue on GitHub
          <ExternalLink className="h-4 w-4" />
        </a>
      </section>
    </SeoSubpageShell>
  );
}
