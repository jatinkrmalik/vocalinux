import Link from "next/link";
import { type Metadata } from "next";
import { CheckCircle2, ChevronRight, Cloud, DollarSign, Lock, Server, Shield, XCircle, Zap } from "lucide-react";
import { SeoSubpageShell } from "@/components/seo-subpage-shell";
import { absoluteUrl, buildPageMetadata } from "@/lib/seo";

const alternatives = [
  {
    name: "Dragon Naturally Speaking",
    type: "Proprietary Desktop",
    pros: ["High accuracy", "Industry standard", "Advanced commands"],
    cons: ["No Linux support", "Expensive subscription", "Closed source", "Cloud dependency"],
    pricing: "$500/year+",
  },
  {
    name: "Otter.ai",
    type: "Cloud Service",
    pros: ["Good accuracy", "Meeting transcription", "Collaboration features"],
    cons: ["Cloud-only (no offline)", "Subscription required", "Privacy concerns", "No Linux desktop app"],
    pricing: "$10-30/month",
  },
  {
    name: "Google Voice Typing",
    type: "Cloud Service",
    pros: ["Free", "Good accuracy", "Multi-language"],
    cons: ["Requires Chrome/Google Docs", "Cloud-only", "Privacy concerns", "No Linux desktop integration"],
    pricing: "Free",
  },
  {
    name: "Speechnotes",
    type: "Web App",
    pros: ["Free tier available", "Simple to use", "No installation"],
    cons: ["Browser-only", "Limited offline support", "No desktop integration", "Privacy concerns"],
    pricing: "$10/month pro",
  },
  {
    name: "Windows Voice Typing",
    type: "OS Built-in",
    pros: ["Free", "Integrated with Windows", "Decent accuracy"],
    cons: ["Windows only", "No Linux support", "Limited customization", "Cloud processing"],
    pricing: "Free (Windows only)",
  },
];

const comparisonTable = [
  { feature: "Linux Support", vocalinux: true, dragon: false, otter: false, google: true },
  { feature: "100% Offline", vocalinux: true, dragon: false, otter: false, google: false },
  { feature: "Open Source", vocalinux: true, dragon: false, otter: false, google: false },
  { feature: "Free Forever", vocalinux: true, dragon: false, otter: false, google: true },
  { feature: "Desktop Integration", vocalinux: true, dragon: true, otter: false, google: false },
  { feature: "Wayland Support", vocalinux: true, dragon: false, otter: false, google: false },
  { feature: "Custom Shortcuts", vocalinux: true, dragon: true, otter: false, google: false },
  { feature: "Voice Commands", vocalinux: true, dragon: true, otter: true, google: true },
  { feature: "Multi-language", vocalinux: true, dragon: true, otter: true, google: true },
  { feature: "GPU Acceleration", vocalinux: true, dragon: false, otter: false, google: false },
];

export const metadata: Metadata = buildPageMetadata({
  title: "Vocalinux Alternatives - Linux Voice Dictation Comparison",
  description:
    "Compare Vocalinux to Dragon, Otter.ai, Google Voice Typing, and other speech-to-text alternatives. See why Vocalinux is the best choice for Linux voice dictation.",
  path: "/alternatives",
  keywords: [
    "vocalinux alternatives",
    "dragon naturally speaking linux alternative",
    "otter.ai alternative",
    "linux speech to text comparison",
    "offline voice dictation",
  ],
});

export default function AlternativesPage() {
  const articleJsonLd = {
    "@context": "https://schema.org",
    "@type": "Article",
    headline: "Vocalinux vs Dragon, Otter, Google - Voice Dictation Comparison",
    description:
      "Comprehensive comparison of Vocalinux with other voice dictation solutions for Linux users.",
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
    mainEntityOfPage: absoluteUrl("/alternatives"),
  };

  return (
    <SeoSubpageShell>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(articleJsonLd) }}
      />

      <section>
        <p className="mb-4 inline-flex items-center gap-2 rounded-full border border-primary/30 bg-primary/10 px-4 py-1.5 text-sm font-medium text-primary">
          <Zap className="h-4 w-4" />
          Comparison
        </p>
        <h1 className="mb-5 text-4xl font-bold tracking-tight sm:text-5xl md:text-6xl">
          Vocalinux vs The Alternatives
        </h1>
        <p className="mb-8 max-w-4xl text-lg text-muted-foreground">
          Looking for voice dictation on Linux? Compare Vocalinux with Dragon, Otter.ai, Google Voice
          Typing, and other alternatives. See why Vocalinux is the best choice for Linux users.
        </p>
      </section>

      <section className="mb-12 rounded-2xl border border-primary/20 bg-primary/5 p-6">
        <h2 className="mb-4 text-xl font-bold">Why Vocalinux for Linux?</h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div className="flex items-center gap-3">
            <Lock className="h-5 w-5 text-primary" />
            <span className="font-medium">100% Offline</span>
          </div>
          <div className="flex items-center gap-3">
            <Shield className="h-5 w-5 text-primary" />
            <span className="font-medium">Privacy First</span>
          </div>
          <div className="flex items-center gap-3">
            <DollarSign className="h-5 w-5 text-primary" />
            <span className="font-medium">Free Forever</span>
          </div>
          <div className="flex items-center gap-3">
            <Server className="h-5 w-5 text-primary" />
            <span className="font-medium">Linux Native</span>
          </div>
        </div>
      </section>

      <section className="mb-12 rounded-2xl border border-zinc-200 bg-white p-6 overflow-x-auto dark:border-zinc-700 dark:bg-zinc-800">
        <h2 className="mb-6 text-2xl font-bold">Feature Comparison</h2>
        <table className="w-full min-w-[600px] text-left">
          <thead>
            <tr className="border-b border-zinc-200 dark:border-zinc-700">
              <th className="pb-3 text-sm font-semibold">Feature</th>
              <th className="pb-3 text-sm font-semibold">Vocalinux</th>
              <th className="pb-3 text-sm font-semibold">Dragon</th>
              <th className="pb-3 text-sm font-semibold">Otter.ai</th>
              <th className="pb-3 text-sm font-semibold">Google</th>
            </tr>
          </thead>
          <tbody className="text-sm">
            {comparisonTable.map((row) => (
              <tr key={row.feature} className="border-b border-zinc-100 dark:border-zinc-700/70">
                <td className="py-3 font-medium">{row.feature}</td>
                <td className="py-3">
                  {row.vocalinux ? (
                    <CheckCircle2 className="h-5 w-5 text-green-500" />
                  ) : (
                    <XCircle className="h-5 w-5 text-red-500" />
                  )}
                </td>
                <td className="py-3">
                  {row.dragon ? (
                    <CheckCircle2 className="h-5 w-5 text-green-500" />
                  ) : (
                    <XCircle className="h-5 w-5 text-red-500" />
                  )}
                </td>
                <td className="py-3">
                  {row.otter ? (
                    <CheckCircle2 className="h-5 w-5 text-green-500" />
                  ) : (
                    <XCircle className="h-5 w-5 text-red-500" />
                  )}
                </td>
                <td className="py-3">
                  {row.google ? (
                    <CheckCircle2 className="h-5 w-5 text-green-500" />
                  ) : (
                    <XCircle className="h-5 w-5 text-red-500" />
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section className="space-y-6">
        <h2 className="text-2xl font-bold">Detailed Comparison</h2>
        {alternatives.map((alt) => (
          <article
            key={alt.name}
            className="rounded-2xl border border-zinc-200 bg-white p-6 dark:border-zinc-700 dark:bg-zinc-800"
          >
            <div className="mb-4 flex flex-wrap items-center justify-between gap-4">
              <div>
                <h3 className="text-xl font-bold">{alt.name}</h3>
                <p className="text-sm text-muted-foreground">{alt.type}</p>
              </div>
              <span className="rounded-full bg-zinc-100 px-3 py-1 text-sm font-medium dark:bg-zinc-700">
                {alt.pricing}
              </span>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div className="rounded-lg bg-green-50 p-4 dark:bg-green-900/20">
                <p className="mb-2 text-sm font-semibold text-green-700 dark:text-green-400">Pros</p>
                <ul className="space-y-1">
                  {alt.pros.map((pro) => (
                    <li key={pro} className="flex items-center gap-2 text-sm text-green-600 dark:text-green-300">
                      <CheckCircle2 className="h-3.5 w-3.5" />
                      {pro}
                    </li>
                  ))}
                </ul>
              </div>

              <div className="rounded-lg bg-red-50 p-4 dark:bg-red-900/20">
                <p className="mb-2 text-sm font-semibold text-red-700 dark:text-red-400">Cons</p>
                <ul className="space-y-1">
                  {alt.cons.map((con) => (
                    <li key={con} className="flex items-center gap-2 text-sm text-red-600 dark:text-red-300">
                      <XCircle className="h-3.5 w-3.5" />
                      {con}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </article>
        ))}
      </section>

      <section className="mt-12 rounded-2xl border border-zinc-200 bg-zinc-50 p-8 dark:border-zinc-700 dark:bg-zinc-900/60">
        <h2 className="mb-4 text-2xl font-bold">The Bottom Line</h2>
        <p className="mb-6 text-muted-foreground">
          If you're on Linux and need voice dictation, Vocalinux is the only option that offers
          offline processing, privacy, and full desktop integration at no cost.
        </p>
        <div className="flex flex-wrap gap-4">
          <Link
            href="/install/"
            className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:bg-primary/90"
          >
            Install Vocalinux
            <ChevronRight className="h-4 w-4" />
          </Link>
          <Link
            href="/privacy/"
            className="inline-flex items-center gap-2 rounded-lg border border-zinc-300 bg-white px-4 py-2 text-sm font-semibold hover:bg-zinc-50 dark:border-zinc-600 dark:bg-zinc-800 dark:hover:bg-zinc-700"
          >
            <Lock className="h-4 w-4" />
            Our Privacy Commitment
          </Link>
        </div>
      </section>
    </SeoSubpageShell>
  );
}
