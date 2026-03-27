import Link from "next/link";
import { type Metadata } from "next";
import { CheckCircle2, Cpu, Sparkles, Zap } from "lucide-react";
import { SeoSubpageShell } from "@/components/seo-subpage-shell";
import { absoluteUrl, buildPageMetadata } from "@/lib/seo";

const engineTable = [
  {
    engine: "whisper.cpp",
    speed: "Fastest startup + low latency",
    hardware: "CPU + AMD/Intel/NVIDIA GPU",
    accuracy: "High (best overall balance)",
    footprint: "Small models available (~39MB tiny)",
    bestFor: "Most users who want strong speed + quality",
    icon: Zap,
    iconColor: "text-amber-500",
    iconBg: "bg-amber-500/10",
  },
  {
    engine: "Whisper (OpenAI)",
    speed: "Slower install and startup",
    hardware: "CPU or NVIDIA CUDA",
    accuracy: "High",
    footprint: "Large dependency footprint (~2.3GB)",
    bestFor: "Users already standardized on PyTorch stack",
    icon: Sparkles,
    iconColor: "text-violet-500",
    iconBg: "bg-violet-500/10",
  },
  {
    engine: "VOSK",
    speed: "Very fast realtime on low-end systems",
    hardware: "CPU",
    accuracy: "Good for lightweight use",
    footprint: "Very lightweight (~40MB model)",
    bestFor: "Older hardware and minimal-resource environments",
    icon: Cpu,
    iconColor: "text-cyan-500",
    iconBg: "bg-cyan-500/10",
  },
];

export const metadata: Metadata = buildPageMetadata({
  title: "Whisper.cpp vs Whisper vs VOSK for Linux Voice Dictation",
  description:
    "Compare whisper.cpp, Whisper, and VOSK for Linux speech-to-text. See speed, hardware requirements, model size, and which engine is best for your workflow.",
  path: "/compare",
  keywords: [
    "whisper.cpp vs vosk",
    "linux speech recognition comparison",
    "best voice dictation engine linux",
    "whisper vs vosk linux",
  ],
});

export default function CompareEnginesPage() {
  const articleJsonLd = {
    "@context": "https://schema.org",
    "@type": "Article",
    headline: "Whisper.cpp vs Whisper vs VOSK for Linux Voice Dictation",
    description:
      "Technical comparison of speech recognition engines for offline Linux voice typing.",
    dateModified: "2026-02-12",
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
    mainEntityOfPage: absoluteUrl("/compare"),
  };

  return (
    <SeoSubpageShell>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(articleJsonLd) }}
      />

      <section>
        <p className="mb-4 inline-flex items-center gap-2 rounded-full border border-primary/30 bg-primary/10 px-4 py-1.5 text-sm font-medium text-primary">
          <Sparkles className="h-4 w-4" />
          Speech Engine Comparison
        </p>
        <h1 className="mb-5 text-4xl font-bold tracking-tight sm:text-5xl md:text-6xl">
          whisper.cpp vs Whisper vs VOSK on Linux
        </h1>
        <p className="mb-8 max-w-4xl text-lg text-muted-foreground">
          If you are choosing a Linux speech-to-text engine, this page gives a practical side-by-side
          comparison focused on latency, hardware support, install footprint, and real desktop usage.
        </p>
      </section>

      <section className="overflow-x-auto rounded-2xl border border-zinc-200 bg-white shadow-sm dark:border-zinc-700 dark:bg-zinc-800">
        <table className="w-full border-collapse text-left">
          <thead>
            <tr className="border-b border-zinc-200 dark:border-zinc-700">
              <th className="px-4 py-3 text-sm font-semibold">Engine</th>
              <th className="px-4 py-3 text-sm font-semibold">Speed</th>
              <th className="px-4 py-3 text-sm font-semibold">Hardware</th>
              <th className="px-4 py-3 text-sm font-semibold">Accuracy</th>
              <th className="px-4 py-3 text-sm font-semibold">Footprint</th>
              <th className="px-4 py-3 text-sm font-semibold">Best for</th>
            </tr>
          </thead>
          <tbody>
            {engineTable.map((row) => {
              const Icon = row.icon;
              return (
                <tr
                  key={row.engine}
                  className="border-b border-zinc-100 align-top dark:border-zinc-700/70"
                >
                  <td className="px-4 py-4 font-semibold">
                    <span className="inline-flex items-center gap-2">
                      <span className={`inline-flex rounded-md p-1.5 ${row.iconBg}`}>
                        <Icon className={`h-4 w-4 ${row.iconColor}`} />
                      </span>
                      {row.engine}
                    </span>
                  </td>
                  <td className="px-4 py-4 text-sm text-muted-foreground">{row.speed}</td>
                  <td className="px-4 py-4 text-sm text-muted-foreground">{row.hardware}</td>
                  <td className="px-4 py-4 text-sm text-muted-foreground">{row.accuracy}</td>
                  <td className="px-4 py-4 text-sm text-muted-foreground">{row.footprint}</td>
                  <td className="px-4 py-4 text-sm text-muted-foreground">{row.bestFor}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </section>

      <section className="mt-12 grid gap-6 md:grid-cols-3">
        <article className="rounded-2xl border border-zinc-200 bg-white p-6 dark:border-zinc-700 dark:bg-zinc-800">
          <h2 className="mb-3 text-2xl font-semibold">When to pick whisper.cpp</h2>
          <p className="text-sm text-muted-foreground">
            Choose whisper.cpp when you want the best speed-to-accuracy ratio and broad hardware support.
            It is the default in Vocalinux for a reason.
          </p>
        </article>

        <article className="rounded-2xl border border-zinc-200 bg-white p-6 dark:border-zinc-700 dark:bg-zinc-800">
          <h2 className="mb-3 text-2xl font-semibold">When to pick Whisper</h2>
          <p className="text-sm text-muted-foreground">
            Choose OpenAI Whisper if your environment already depends on PyTorch/CUDA workflows and you
            prefer that runtime profile.
          </p>
        </article>

        <article className="rounded-2xl border border-zinc-200 bg-white p-6 dark:border-zinc-700 dark:bg-zinc-800">
          <h2 className="mb-3 text-2xl font-semibold">When to pick VOSK</h2>
          <p className="text-sm text-muted-foreground">
            Choose VOSK on older laptops, low-RAM systems, or lightweight VMs where small model size and
            minimal overhead matter most.
          </p>
        </article>
      </section>

      <section className="mt-12 rounded-2xl border border-zinc-200 bg-zinc-50 p-8 dark:border-zinc-700 dark:bg-zinc-900/60">
        <h2 className="mb-4 text-2xl font-bold">Next steps</h2>
        <ul className="space-y-3 text-muted-foreground">
          <li>
            <span className="inline-flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-green-500" />
              Install by distro:
              <Link href="/install/ubuntu/" className="font-semibold text-primary hover:underline">
                Ubuntu
              </Link>
              ,
              <Link href="/install/fedora/" className="font-semibold text-primary hover:underline">
                Fedora
              </Link>
              ,
              <Link href="/install/arch/" className="font-semibold text-primary hover:underline">
                Arch Linux
              </Link>
              .
            </span>
          </li>
          <li>
            <span className="inline-flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-green-500" />
              Use interactive install to detect your hardware and pick the best engine defaults.
            </span>
          </li>
          <li>
            <span className="inline-flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-green-500" />
              After install, tune model size for your preferred latency and accuracy level.
            </span>
          </li>
        </ul>
      </section>
    </SeoSubpageShell>
  );
}
