import Link from "next/link";
import { type Metadata } from "next";
import {
  CheckCircle2,
  ChevronRight,
  Command,
  Cpu,
  Gauge,
  Headphones,
  PanelTop,
  Trophy,
  Waypoints,
} from "lucide-react";
import { SeoSubpageShell } from "@/components/seo-subpage-shell";
import { absoluteUrl, buildPageMetadata } from "@/lib/seo";

const comparisonRows = [
  {
    feature: "Interface and daily workflow",
    vocalinux: "Full GTK GUI + tray controls + keyboard shortcuts",
    nerdDictation: "CLI-first terminal workflow",
    winner: "Vocalinux",
    icon: PanelTop,
  },
  {
    feature: "Offline voice dictation",
    vocalinux: "100% offline with multiple engine options",
    nerdDictation: "Offline dictation, single CLI-centered flow",
    winner: "Vocalinux",
    icon: Command,
  },
  {
    feature: "Wayland text injection",
    vocalinux: "Native IBus integration for dictation in any app",
    nerdDictation: "IBus-based text injection on Wayland",
    winner: "Vocalinux",
    icon: Waypoints,
  },
  {
    feature: "GPU acceleration",
    vocalinux: "Vulkan acceleration across AMD, Intel, and NVIDIA",
    nerdDictation: "CPU-focused workflow",
    winner: "Vocalinux",
    icon: Cpu,
  },
  {
    feature: "Push-to-talk",
    vocalinux: "Built-in push-to-talk and toggle mode",
    nerdDictation: "Terminal-first trigger workflow",
    winner: "Vocalinux",
    icon: Gauge,
  },
  {
    feature: "Audio feedback",
    vocalinux: "Built-in pleasant sound effects for start/stop/error",
    nerdDictation: "No native desktop sound-feedback layer",
    winner: "Vocalinux",
    icon: Headphones,
  },
  {
    feature: "System tray integration",
    vocalinux: "Tray icon with status, controls, and settings access",
    nerdDictation: "No native system tray app",
    winner: "Vocalinux",
    icon: Trophy,
  },
];

export const metadata: Metadata = buildPageMetadata({
  title: "Vocalinux vs Nerd Dictation: Best Offline Voice Dictation for Linux",
  description:
    "Comparing Vocalinux and Nerd Dictation for offline Linux voice dictation. CLI vs GUI, GPU vs CPU-only, Wayland support, and more.",
  path: "/vs-nerd-dictation",
  keywords: [
    "vocalinux vs nerd dictation",
    "linux voice dictation comparison",
    "offline speech to text linux",
  ],
});

export default function VsNerdDictationPage() {
  const articleJsonLd = {
    "@context": "https://schema.org",
    "@type": "Article",
    headline: "Vocalinux vs Nerd Dictation: Best Offline Voice Dictation for Linux",
    description:
      "Comparing Vocalinux and Nerd Dictation for offline Linux voice dictation. CLI vs GUI, GPU vs CPU-only, Wayland support, and more.",
    dateModified: "2026-03-30",
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
    mainEntityOfPage: absoluteUrl("/vs-nerd-dictation"),
  };

  return (
    <SeoSubpageShell>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(articleJsonLd) }}
      />

      <section>
        <p className="mb-4 inline-flex items-center gap-2 rounded-full border border-primary/30 bg-primary/10 px-4 py-1.5 text-sm font-medium text-primary">
          <Trophy className="h-4 w-4" />
          Vocalinux Comparison
        </p>
        <h1 className="mb-5 text-4xl font-bold tracking-tight sm:text-5xl md:text-6xl">
          Vocalinux vs Nerd Dictation
        </h1>
        <p className="mb-8 max-w-4xl text-lg text-muted-foreground">
          Nerd Dictation is a popular offline CLI tool for Linux. But if you want a complete desktop
          dictation experience with GUI controls, tray integration, push-to-talk, and broad GPU support,
          Vocalinux is the better choice.
        </p>
      </section>

      <section className="overflow-x-auto rounded-2xl border border-zinc-200 bg-white shadow-sm dark:border-zinc-700 dark:bg-zinc-800">
        <h2 className="px-4 pb-2 pt-5 text-2xl font-bold">Feature-by-feature comparison</h2>
        <table className="w-full border-collapse text-left">
          <thead>
            <tr className="border-b border-zinc-200 dark:border-zinc-700">
              <th className="px-4 py-3 text-sm font-semibold">Feature</th>
              <th className="px-4 py-3 text-sm font-semibold">Vocalinux</th>
              <th className="px-4 py-3 text-sm font-semibold">Nerd Dictation</th>
              <th className="px-4 py-3 text-sm font-semibold">Winner</th>
            </tr>
          </thead>
          <tbody>
            {comparisonRows.map((row) => {
              const Icon = row.icon;

              return (
                <tr
                  key={row.feature}
                  className="border-b border-zinc-100 align-top dark:border-zinc-700/70"
                >
                  <td className="px-4 py-4 font-semibold">
                    <span className="inline-flex items-center gap-2">
                      <span className="rounded-md bg-primary/10 p-1.5">
                        <Icon className="h-4 w-4 text-primary" />
                      </span>
                      {row.feature}
                    </span>
                  </td>
                  <td className="px-4 py-4 text-sm text-muted-foreground">{row.vocalinux}</td>
                  <td className="px-4 py-4 text-sm text-muted-foreground">{row.nerdDictation}</td>
                  <td className="px-4 py-4 text-sm font-semibold text-green-600 dark:text-green-400">
                    <span className="inline-flex items-center gap-2">
                      <CheckCircle2 className="h-4 w-4" />
                      {row.winner}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </section>

      <section className="mt-10 rounded-2xl border border-zinc-200 bg-zinc-50 p-6 dark:border-zinc-700 dark:bg-zinc-900/60">
        <h2 className="mb-4 text-2xl font-bold">Go deeper</h2>
        <div className="grid gap-3 text-sm text-muted-foreground sm:grid-cols-2 lg:grid-cols-3">
          <Link href="/offline/" className="font-semibold text-primary hover:underline">
            Why offline dictation matters
          </Link>
          <Link href="/gpu-acceleration/" className="font-semibold text-primary hover:underline">
            Vulkan GPU acceleration details
          </Link>
          <Link href="/wayland/" className="font-semibold text-primary hover:underline">
            Wayland + IBus integration guide
          </Link>
          <Link href="/compare/" className="font-semibold text-primary hover:underline">
            Engine comparison (whisper.cpp vs Whisper vs VOSK)
          </Link>
          <Link href="/for-developers/" className="font-semibold text-primary hover:underline">
            Developer docs and architecture
          </Link>
          <Link href="/rsi-prevention/" className="font-semibold text-primary hover:underline">
            RSI prevention with voice typing
          </Link>
        </div>
      </section>

      <section className="mt-10 rounded-2xl border border-primary/20 bg-primary/5 p-8">
        <h2 className="mb-4 text-2xl font-bold">Ready to switch from terminal-only dictation?</h2>
        <p className="mb-6 max-w-3xl text-muted-foreground">
          Install Vocalinux for a native Linux voice dictation workflow with offline privacy, better
          usability, and stronger performance options.
        </p>
        <div className="flex flex-wrap gap-4">
          <Link
            href="/install/"
            className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground dark:text-black hover:bg-primary/90"
          >
            Install Vocalinux
            <ChevronRight className="h-4 w-4" />
          </Link>
          <Link
            href="/compare/"
            className="inline-flex items-center gap-2 rounded-lg border border-zinc-300 bg-white px-4 py-2 text-sm font-semibold hover:bg-zinc-50 dark:border-zinc-600 dark:bg-zinc-800 dark:hover:bg-zinc-700"
          >
            Engine comparison
          </Link>
        </div>
      </section>
    </SeoSubpageShell>
  );
}
