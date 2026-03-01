import Link from "next/link";
import { type Metadata } from "next";
import { CheckCircle2, ChevronRight, Heart, Keyboard, Shield, User } from "lucide-react";
import { SeoSubpageShell } from "@/components/seo-subpage-shell";
import { absoluteUrl, buildPageMetadata } from "@/lib/seo";

const benefits = [
  {
    title: "Reduce Physical Strain",
    description:
      "Give your hands, wrists, and fingers a break. Voice dictation lets you type without the physical toll of keyboard use.",
    icon: Heart,
    iconColor: "text-rose-500",
    iconBg: "bg-rose-100 dark:bg-rose-900/30",
  },
  {
    title: "Prevent Repetitive Stress",
    description:
      "RSI develops from thousands of repeated motions. Dictating breaks the cycle and allows recovery.",
    icon: Keyboard,
    iconColor: "text-amber-500",
    iconBg: "bg-amber-100 dark:bg-amber-900/30",
  },
  {
    title: "Privacy for Health",
    description:
      "Your health data stays private. All voice processing happens locally—no cloud uploads, no third parties.",
    icon: Shield,
    iconColor: "text-blue-500",
    iconBg: "bg-blue-100 dark:bg-blue-900/30",
  },
  {
    title: "Independence",
    description:
      "For those with mobility limitations, voice dictation provides computer independence without relying on others.",
    icon: User,
    iconColor: "text-emerald-500",
    iconBg: "bg-emerald-100 dark:bg-emerald-900/30",
  },
];

const conditions = [
  {
    name: "Carpal Tunnel Syndrome",
    description:
      "Compression of the median nerve causing numbness, tingling, and weakness in the hand.",
    howDictationHelps:
      "Eliminate the wrist movements that aggravate symptoms while maintaining productivity.",
  },
  {
    name: "Repetitive Strain Injury (RSI)",
    description: "Pain in muscles, nerves, or tendons caused by repetitive movements and overuse.",
    howDictationHelps:
      "Break the cycle of repetitive keystrokes and allow your hands to recover.",
  },
  {
    name: "Tendinitis",
    description: "Inflammation or irritation of a tendon, often affecting the wrist and fingers.",
    howDictationHelps:
      "Reduce tendon stress by speaking instead of typing for extended periods.",
  },
  {
    name: "Tennis Elbow (Lateral Epicondylitis)",
    description: "Overuse injury causing pain on the outside of the elbow and forearm.",
    howDictationHelps:
      "Minimize the gripping and wrist motions that exacerbate elbow pain.",
  },
  {
    name: "Thoracic Outlet Syndrome",
    description:
      "Compression of nerves or blood vessels in the lower neck and upper chest.",
    howDictationHelps:
      "Reduce the forward-head posture and shoulder tension common with keyboard use.",
  },
  {
    name: "General Mobility Limitations",
    description:
      "Conditions affecting hand, arm, or finger movement from various causes.",
    howDictationHelps:
      "Full computer control without physical keyboard interaction required.",
  },
];

const statistics = [
  { value: "8+", label: "Hours per day average computer use for office workers" },
  { value: "50%", label: "Of computer users experience RSI symptoms" },
  { value: "100+", label: "Words per minute achievable with voice dictation" },
  { value: "100%", label: "Offline - no data ever leaves your computer" },
];

export const metadata: Metadata = buildPageMetadata({
  title: "Voice Dictation for RSI & Carpal Tunnel Prevention | Vocalinux",
  description:
    "Prevent and manage RSI, carpal tunnel, and repetitive strain injuries with voice dictation. Hands-free typing for Linux users with 100% offline privacy.",
  path: "/rsi-prevention",
  keywords: [
    "RSI voice dictation",
    "carpal tunnel voice typing",
    "hands-free typing",
    "repetitive strain injury prevention",
    "voice typing for wrist pain",
    "dictation software for RSI",
    "ergonomic typing alternative",
    "Linux voice dictation accessibility",
  ],
});

export default function RsiPreventionPage() {
  const articleJsonLd = {
    "@context": "https://schema.org",
    "@type": "Article",
    headline: "Voice Dictation for RSI & Carpal Tunnel Prevention",
    description:
      "How voice dictation helps prevent and manage repetitive strain injuries. Hands-free typing solution for Linux users.",
    dateModified: "2026-02-22",
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
    mainEntityOfPage: absoluteUrl("/rsi-prevention"),
  };

  return (
    <SeoSubpageShell>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(articleJsonLd) }}
      />

      <section>
        <p className="mb-4 inline-flex items-center gap-2 rounded-full border border-rose-500/30 bg-rose-500/10 px-4 py-1.5 text-sm font-medium text-rose-600 dark:text-rose-400">
          <Heart className="h-4 w-4" />
          Health & Accessibility
        </p>
        <h1 className="mb-5 text-4xl font-bold tracking-tight sm:text-5xl md:text-6xl">
          Voice Dictation for RSI Prevention
        </h1>
        <p className="mb-8 max-w-4xl text-lg text-muted-foreground">
          Suffering from carpal tunnel, wrist pain, or repetitive strain? Voice dictation lets you
          keep working without the physical toll. All processing happens locally on your Linux
          machine.
        </p>
      </section>

      <section className="mb-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {statistics.map((stat) => (
          <div
            key={stat.label}
            className="rounded-xl border border-zinc-200 bg-white p-5 text-center dark:border-zinc-700 dark:bg-zinc-800"
          >
            <p className="mb-1 text-3xl font-bold text-primary">{stat.value}</p>
            <p className="text-sm text-muted-foreground">{stat.label}</p>
          </div>
        ))}
      </section>

      <section className="mb-12">
        <h2 className="mb-6 text-2xl font-bold">Why Voice Dictation Helps</h2>
        <div className="grid gap-6 sm:grid-cols-2">
          {benefits.map((benefit) => {
            const Icon = benefit.icon;
            return (
              <article
                key={benefit.title}
                className="rounded-xl border border-zinc-200 bg-white p-6 dark:border-zinc-700 dark:bg-zinc-800"
              >
                <div className="mb-4 flex items-center gap-3">
                  <div className={`rounded-lg p-2.5 ${benefit.iconBg}`}>
                    <Icon className={`h-5 w-5 ${benefit.iconColor}`} />
                  </div>
                  <h3 className="font-semibold">{benefit.title}</h3>
                </div>
                <p className="text-sm text-muted-foreground">{benefit.description}</p>
              </article>
            );
          })}
        </div>
      </section>

      <section className="mb-12">
        <h2 className="mb-6 text-2xl font-bold">Conditions Helped by Voice Dictation</h2>
        <div className="space-y-4">
          {conditions.map((condition) => (
            <article
              key={condition.name}
              className="rounded-xl border border-zinc-200 bg-white p-5 dark:border-zinc-700 dark:bg-zinc-800"
            >
              <h3 className="mb-2 font-semibold">{condition.name}</h3>
              <p className="mb-3 text-sm text-muted-foreground">{condition.description}</p>
              <div className="rounded-lg bg-green-50 p-3 dark:bg-green-900/20">
                <p className="text-sm text-green-700 dark:text-green-400">
                  <strong>How dictation helps:</strong> {condition.howDictationHelps}
                </p>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="mb-12 rounded-2xl border border-zinc-200 bg-white p-6 dark:border-zinc-700 dark:bg-zinc-800">
        <h2 className="mb-4 text-2xl font-bold">Getting Started with Hands-Free Typing</h2>
        <div className="grid gap-6 md:grid-cols-2">
          <div>
            <h3 className="mb-3 font-semibold">Tips for Transitioning</h3>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li className="inline-flex items-start gap-2">
                <CheckCircle2 className="mt-0.5 h-4 w-4 flex-shrink-0 text-green-500" />
                Start by dictating emails and documents, then expand to other tasks
              </li>
              <li className="inline-flex items-start gap-2">
                <CheckCircle2 className="mt-0.5 h-4 w-4 flex-shrink-0 text-green-500" />
                Use voice commands for punctuation to maintain natural speech flow
              </li>
              <li className="inline-flex items-start gap-2">
                <CheckCircle2 className="mt-0.5 h-4 w-4 flex-shrink-0 text-green-500" />
                Take breaks—voice dictation is still work, and vocal rest matters too
              </li>
              <li className="inline-flex items-start gap-2">
                <CheckCircle2 className="mt-0.5 h-4 w-4 flex-shrink-0 text-green-500" />
                Combine with ergonomic equipment for maximum benefit
              </li>
            </ul>
          </div>
          <div>
            <h3 className="mb-3 font-semibold">Vocalinux Advantages</h3>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li className="inline-flex items-start gap-2">
                <CheckCircle2 className="mt-0.5 h-4 w-4 flex-shrink-0 text-green-500" />
                Toggle mode or push-to-talk control—no mouse required
              </li>
              <li className="inline-flex items-start gap-2">
                <CheckCircle2 className="mt-0.5 h-4 w-4 flex-shrink-0 text-green-500" />
                System tray indicator shows recording status
              </li>
              <li className="inline-flex items-start gap-2">
                <CheckCircle2 className="mt-0.5 h-4 w-4 flex-shrink-0 text-green-500" />
                Pleasant audio feedback confirms start/stop
              </li>
              <li className="inline-flex items-start gap-2">
                <CheckCircle2 className="mt-0.5 h-4 w-4 flex-shrink-0 text-green-500" />
                Works in ALL Linux applications—universal compatibility
              </li>
            </ul>
          </div>
        </div>
      </section>

      <section className="rounded-2xl border border-rose-200 bg-rose-50 p-8 dark:border-rose-800 dark:bg-rose-900/20">
        <h2 className="mb-4 text-2xl font-bold text-rose-800 dark:text-rose-300">
          Take Care of Your Hands
        </h2>
        <p className="mb-6 text-rose-700 dark:text-rose-400">
          Your health matters. If you&apos;re experiencing pain, numbness, or tingling, consult a
          healthcare professional. Voice dictation is a tool to help, not a substitute for proper
          medical care.
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
            href="/use-cases/"
            className="inline-flex items-center gap-2 rounded-lg border border-rose-300 bg-white px-4 py-2 text-sm font-semibold text-rose-700 hover:bg-rose-50 dark:border-rose-700 dark:bg-rose-900/50 dark:text-rose-300 dark:hover:bg-rose-900/70"
          >
            See Other Use Cases
          </Link>
        </div>
      </section>
    </SeoSubpageShell>
  );
}
