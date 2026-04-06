import Link from "next/link";
import { type Metadata } from "next";
import {
  CheckCircle2,
  ChevronRight,
  CloudOff,
  Database,
  Lock,
  Shield,
  WifiOff,
  XCircle,
} from "lucide-react";
import { SeoSubpageShell } from "@/components/seo-subpage-shell";
import { absoluteUrl, buildPageMetadata } from "@/lib/seo";

const benefits = [
  {
    title: "No Internet Required",
    description:
      "Works on airplanes, in tunnels, on remote farms. Your voice never needs to leave your machine.",
    icon: WifiOff,
    iconColor: "text-blue-500",
    iconBg: "bg-blue-100 dark:bg-blue-900/30",
  },
  {
    title: "Zero Data Collection",
    description:
      "No telemetry, no analytics, no usage tracking. There's no server to send data to even if we wanted to.",
    icon: Database,
    iconColor: "text-emerald-500",
    iconBg: "bg-emerald-100 dark:bg-emerald-900/30",
  },
  {
    title: "No Account Required",
    description:
      "No signup, no login, no password to forget. Download and run—that's it.",
    icon: Lock,
    iconColor: "text-violet-500",
    iconBg: "bg-violet-100 dark:bg-violet-900/30",
  },
  {
    title: "Your Voice Stays Yours",
    description:
      "Voice data is biometric. Your voice patterns, accent, and speech habits are yours alone.",
    icon: Shield,
    iconColor: "text-rose-500",
    iconBg: "bg-rose-100 dark:bg-rose-900/30",
  },
];

const vsCloud = [
  { feature: "Requires internet", offline: false, cloud: true },
  { feature: "Voice data uploaded to servers", offline: false, cloud: true },
  { feature: "Account/signup required", offline: false, cloud: true },
  { feature: "Subscription cost", offline: false, cloud: true },
  { feature: "Works in airplane mode", offline: true, cloud: false },
  { feature: "GDPR/privacy compliant by default", offline: true, cloud: false },
  { feature: "Vendor can shut down service", offline: false, cloud: true },
  { feature: "Sensitive content safe", offline: true, cloud: false },
];

const sensitiveUseCases = [
  {
    title: "Medical Professionals",
    description: "Patient notes, diagnoses, and medical records must stay private.",
  },
  {
    title: "Legal Professionals",
    description: "Attorney-client privilege requires absolute data confidentiality.",
  },
  {
    title: "Journalists & Sources",
    description: "Protecting sources means keeping all communications offline.",
  },
  {
    title: "Corporate Trade Secrets",
    description: "Product plans, financial data, and strategies shouldn't leave your network.",
  },
  {
    title: "Government & Defense",
    description: "Classified or sensitive government work requires air-gapped solutions.",
  },
  {
    title: "Personal Journals",
    description: "Your private thoughts and reflections deserve complete privacy.",
  },
];

export const metadata: Metadata = buildPageMetadata({
  title: "100% Offline Voice Dictation - No Cloud, No Upload | Vocalinux",
  description:
    "Completely offline voice dictation for Linux. No cloud processing, no data upload, no account required. Your voice data never leaves your computer.",
  path: "/offline",
  keywords: [
    "offline voice dictation",
    "no cloud speech recognition",
    "private voice typing",
    "local speech to text",
    "offline dictation software",
    "no internet voice recognition",
    "airplane mode dictation",
    "privacy-first speech recognition",
  ],
});

export default function OfflinePage() {
  const articleJsonLd = {
    "@context": "https://schema.org",
    "@type": "Article",
    headline: "100% Offline Voice Dictation for Linux",
    description:
      "Why Vocalinux is completely offline. No cloud processing, no data upload, maximum privacy.",
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
    mainEntityOfPage: absoluteUrl("/offline"),
  };

  return (
    <SeoSubpageShell>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(articleJsonLd) }}
      />

      <section>
        <p className="mb-4 inline-flex items-center gap-2 rounded-full border border-primary/30 bg-primary/10 px-4 py-1.5 text-sm font-medium text-primary">
          <CloudOff className="h-4 w-4" />
          100% Offline
        </p>
        <h1 className="mb-5 text-4xl font-bold tracking-tight sm:text-5xl md:text-6xl">
          Offline Voice Dictation
        </h1>
        <p className="mb-8 max-w-4xl text-lg text-muted-foreground">
          Your voice never leaves your computer. All speech recognition happens locally using
          whisper.cpp, VOSK, or OpenAI Whisper models running on your hardware. No cloud. No
          upload. No exceptions.
        </p>
      </section>

      <section className="mb-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
        {benefits.map((benefit) => {
          const Icon = benefit.icon;
          return (
            <article
              key={benefit.title}
              className="rounded-xl border border-zinc-200 bg-white p-5 dark:border-zinc-700 dark:bg-zinc-800"
            >
              <div className={`mb-3 inline-flex rounded-lg p-2 ${benefit.iconBg}`}>
                <Icon className={`h-5 w-5 ${benefit.iconColor}`} />
              </div>
              <h3 className="mb-2 font-semibold">{benefit.title}</h3>
              <p className="text-sm text-muted-foreground">{benefit.description}</p>
            </article>
          );
        })}
      </section>

      <section className="mb-12 rounded-2xl border border-zinc-200 bg-white p-6 dark:border-zinc-700 dark:bg-zinc-800">
        <h2 className="mb-6 text-2xl font-bold">Offline vs Cloud Dictation</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-zinc-200 dark:border-zinc-700">
                <th className="pb-3 pr-4 font-semibold">Feature</th>
                <th className="pb-3 pr-4 font-semibold text-center">Vocalinux (Offline)</th>
                <th className="pb-3 font-semibold text-center">Cloud Dictation</th>
              </tr>
            </thead>
            <tbody>
              {vsCloud.map((row) => (
                <tr key={row.feature} className="border-b border-zinc-100 dark:border-zinc-700/70">
                  <td className="py-3 pr-4">{row.feature}</td>
                  <td className="py-3 pr-4 text-center">
                    {row.offline ? (
                      <CheckCircle2 className="mx-auto h-5 w-5 text-green-500" />
                    ) : (
                      <XCircle className="mx-auto h-5 w-5 text-red-500" />
                    )}
                  </td>
                  <td className="py-3 text-center">
                    {row.cloud ? (
                      <CheckCircle2 className="mx-auto h-5 w-5 text-green-500" />
                    ) : (
                      <XCircle className="mx-auto h-5 w-5 text-red-500" />
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="mb-12">
        <h2 className="mb-6 text-2xl font-bold">When Offline Matters Most</h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {sensitiveUseCases.map((useCase) => (
            <div
              key={useCase.title}
              className="rounded-xl border border-zinc-200 bg-white p-5 dark:border-zinc-700 dark:bg-zinc-800"
            >
              <h3 className="mb-2 font-semibold">{useCase.title}</h3>
              <p className="text-sm text-muted-foreground">{useCase.description}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="mb-12 rounded-2xl border border-emerald-200 bg-emerald-50 p-6 dark:border-emerald-800 dark:bg-emerald-900/20">
        <h2 className="mb-3 text-xl font-bold text-emerald-800 dark:text-emerald-300">
          How Offline Processing Works
        </h2>
        <p className="mb-4 text-sm text-emerald-700 dark:text-emerald-400">
          Vocalinux uses speech recognition models that run entirely on your CPU or GPU:
        </p>
        <ul className="space-y-2 text-sm text-emerald-700 dark:text-emerald-400">
          <li className="flex items-start gap-2">
            <CheckCircle2 className="mt-0.5 h-4 w-4 flex-shrink-0" />
            <strong>whisper.cpp</strong> — C++ port of OpenAI Whisper, runs locally with GPU
            acceleration
          </li>
          <li className="flex items-start gap-2">
            <CheckCircle2 className="mt-0.5 h-4 w-4 flex-shrink-0" />
            <strong>VOSK</strong> — Lightweight offline engine, minimal resources
          </li>
          <li className="flex items-start gap-2">
            <CheckCircle2 className="mt-0.5 h-4 w-4 flex-shrink-0" />
            <strong>OpenAI Whisper</strong> — PyTorch-based, runs on NVIDIA GPU or CPU
          </li>
        </ul>
        <p className="mt-4 text-sm text-emerald-700 dark:text-emerald-400">
          Models are downloaded once (39MB-1.5GB depending on size), then all processing happens
          locally. No network requests during dictation.
        </p>
      </section>

      <section className="mb-12 rounded-2xl border border-amber-200 bg-amber-50 p-6 dark:border-amber-800 dark:bg-amber-900/20">
        <h2 className="mb-3 text-xl font-bold text-amber-800 dark:text-amber-300">
          Verify It Yourself
        </h2>
        <p className="mb-3 text-sm text-amber-700 dark:text-amber-400">
          Don&apos;t trust—verify. Vocalinux is open source. You can:
        </p>
        <ul className="space-y-2 text-sm text-amber-700 dark:text-amber-400">
          <li className="flex items-start gap-2">
            <CheckCircle2 className="mt-0.5 h-4 w-4 flex-shrink-0" />
            Read every line of code on{" "}
            <a
              href="https://github.com/jatinkrmalik/vocalinux"
              target="_blank"
              rel="noopener noreferrer"
              className="font-semibold hover:underline"
            >
              GitHub
            </a>
          </li>
          <li className="flex items-start gap-2">
            <CheckCircle2 className="mt-0.5 h-4 w-4 flex-shrink-0" />
            Run with <code className="rounded bg-amber-200 px-1 dark:bg-amber-900">--debug</code> to see all network activity (there is none)
          </li>
          <li className="flex items-start gap-2">
            <CheckCircle2 className="mt-0.5 h-4 w-4 flex-shrink-0" />
            Monitor with <code className="rounded bg-amber-200 px-1 dark:bg-amber-900">tcpdump</code> or{" "}
            <code className="rounded bg-amber-200 px-1 dark:bg-amber-900">wireshark</code>—you&apos;ll see silence
          </li>
          <li className="flex items-start gap-2">
            <CheckCircle2 className="mt-0.5 h-4 w-4 flex-shrink-0" />
            Disconnect from the internet and verify dictation still works perfectly
          </li>
        </ul>
      </section>

      <section className="rounded-2xl border border-zinc-200 bg-zinc-50 p-8 dark:border-zinc-700 dark:bg-zinc-900/60">
        <h2 className="mb-4 text-2xl font-bold">Truly Private Voice Dictation</h2>
        <p className="mb-6 text-muted-foreground">
          Install Vocalinux and take control of your voice data. No cloud, no tracking, no
          compromises.
        </p>
        <div className="flex flex-wrap gap-4">
          <Link
            href="/install/"
            className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground dark:text-black hover:bg-primary/90"
          >
            Install Now
            <ChevronRight className="h-4 w-4" />
          </Link>
          <Link
            href="/open-source/"
            className="inline-flex items-center gap-2 rounded-lg border border-zinc-300 bg-white px-4 py-2 text-sm font-semibold hover:bg-zinc-50 dark:border-zinc-600 dark:bg-zinc-800 dark:hover:bg-zinc-700"
          >
            View Source Code
          </Link>
        </div>
      </section>
    </SeoSubpageShell>
  );
}
