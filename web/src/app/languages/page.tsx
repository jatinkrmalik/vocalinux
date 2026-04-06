import Link from "next/link";
import { type Metadata } from "next";
import { CheckCircle2, ChevronRight, Globe, Languages, Mic } from "lucide-react";
import { SeoSubpageShell } from "@/components/seo-subpage-shell";
import { absoluteUrl, buildPageMetadata } from "@/lib/seo";

const supportedLanguages = [
  {
    code: "en",
    name: "English",
    nativeName: "English",
    flag: "🇺🇸",
    description: "Full support across all engines (whisper.cpp, Whisper, VOSK)",
    engines: ["whisper.cpp", "Whisper", "VOSK"],
    modelSizes: ["tiny", "base", "small", "medium", "large"],
  },
  {
    code: "es",
    name: "Spanish",
    nativeName: "Español",
    flag: "🇪🇸",
    description: "Complete Spanish language support for dictation",
    engines: ["whisper.cpp", "Whisper", "VOSK"],
    modelSizes: ["tiny", "base", "small", "medium", "large"],
  },
  {
    code: "fr",
    name: "French",
    nativeName: "Français",
    flag: "🇫🇷",
    description: "French language voice typing and transcription",
    engines: ["whisper.cpp", "Whisper", "VOSK"],
    modelSizes: ["tiny", "base", "small", "medium", "large"],
  },
  {
    code: "de",
    name: "German",
    nativeName: "Deutsch",
    flag: "🇩🇪",
    description: "German dictation with high accuracy",
    engines: ["whisper.cpp", "Whisper", "VOSK"],
    modelSizes: ["tiny", "base", "small", "medium", "large"],
  },
  {
    code: "it",
    name: "Italian",
    nativeName: "Italiano",
    flag: "🇮🇹",
    description: "Italian voice recognition and text dictation",
    engines: ["whisper.cpp", "Whisper", "VOSK"],
    modelSizes: ["tiny", "base", "small", "medium", "large"],
  },
  {
    code: "pt",
    name: "Portuguese",
    nativeName: "Português",
    flag: "🇧🇷",
    description: "Brazilian and European Portuguese support",
    engines: ["whisper.cpp", "Whisper", "VOSK"],
    modelSizes: ["tiny", "base", "small", "medium", "large"],
  },
  {
    code: "ru",
    name: "Russian",
    nativeName: "Русский",
    flag: "🇷🇺",
    description: "Russian language speech-to-text transcription",
    engines: ["whisper.cpp", "Whisper", "VOSK"],
    modelSizes: ["tiny", "base", "small", "medium", "large"],
  },
  {
    code: "zh",
    name: "Chinese",
    nativeName: "中文",
    flag: "🇨🇳",
    description: "Mandarin Chinese voice dictation support",
    engines: ["whisper.cpp", "Whisper", "VOSK"],
    modelSizes: ["tiny", "base", "small", "medium", "large"],
  },
  {
    code: "hi",
    name: "Hindi",
    nativeName: "हिन्दी",
    flag: "🇮🇳",
    description: "Hindi language voice typing and transcription",
    engines: ["whisper.cpp", "Whisper", "VOSK"],
    modelSizes: ["tiny", "base", "small", "medium", "large"],
  },
];

const features = [
  {
    title: "Automatic Language Detection",
    description:
      "Vocalinux can automatically detect the language you're speaking, no manual switching required.",
    icon: Globe,
  },
  {
    title: "Multi-Engine Support",
    description:
      "All supported languages work across whisper.cpp, OpenAI Whisper, and VOSK engines.",
    icon: Mic,
  },
  {
    title: "Offline Processing",
    description:
      "All language processing happens locally on your machine. No cloud, no data upload.",
    icon: CheckCircle2,
  },
];

export const metadata: Metadata = buildPageMetadata({
  title: "Multilingual Voice Dictation - Spanish, French, German, & More | Vocalinux",
  description:
    "Dictate in 9+ languages including Spanish, French, German, Italian, Portuguese, Russian, Chinese, and Hindi. Free offline multilingual voice typing for Linux.",
  path: "/languages",
  keywords: [
    "multilingual voice dictation",
    "Spanish voice typing",
    "French speech to text",
    "German dictation software",
    "Italian voice recognition",
    "Portuguese voice typing",
    "Russian speech recognition",
    "Chinese dictation",
    "Hindi voice typing",
    "Linux multilingual dictation",
  ],
});

export default function LanguagesPage() {
  const articleJsonLd = {
    "@context": "https://schema.org",
    "@type": "Article",
    headline: "Multilingual Voice Dictation for Linux - 9+ Languages Supported",
    description:
      "Complete guide to Vocalinux multilingual voice dictation. Dictate in Spanish, French, German, Italian, Portuguese, Russian, Chinese, Hindi, and more.",
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
    mainEntityOfPage: absoluteUrl("/languages"),
  };

  return (
    <SeoSubpageShell>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(articleJsonLd) }}
      />

      <section>
        <p className="mb-4 inline-flex items-center gap-2 rounded-full border border-primary/30 bg-primary/10 px-4 py-1.5 text-sm font-medium text-primary">
          <Languages className="h-4 w-4" />
          9+ Languages
        </p>
        <h1 className="mb-5 text-4xl font-bold tracking-tight sm:text-5xl md:text-6xl">
          Multilingual Voice Dictation for Linux
        </h1>
        <p className="mb-8 max-w-4xl text-lg text-muted-foreground">
          Dictate in your native language. Vocalinux supports 9+ languages with full offline
          processing—no cloud required, no data leaves your machine.
        </p>
      </section>

      <section className="mb-12 grid gap-6 sm:grid-cols-3">
        {features.map((feature) => {
          const Icon = feature.icon;
          return (
            <div
              key={feature.title}
              className="rounded-xl border border-zinc-200 bg-white p-6 dark:border-zinc-700 dark:bg-zinc-800"
            >
              <Icon className="mb-3 h-8 w-8 text-primary" />
              <h3 className="mb-2 font-semibold">{feature.title}</h3>
              <p className="text-sm text-muted-foreground">{feature.description}</p>
            </div>
          );
        })}
      </section>

      <section className="mb-12">
        <h2 className="mb-6 text-2xl font-bold">Supported Languages</h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {supportedLanguages.map((lang) => (
            <article
              key={lang.code}
              className="rounded-xl border border-zinc-200 bg-white p-5 dark:border-zinc-700 dark:bg-zinc-800"
            >
              <div className="mb-3 flex items-center gap-3">
                <span className="text-3xl">{lang.flag}</span>
                <div>
                  <h3 className="font-semibold">{lang.name}</h3>
                  <p className="text-sm text-muted-foreground">{lang.nativeName}</p>
                </div>
              </div>
              <p className="mb-3 text-sm text-muted-foreground">{lang.description}</p>
              <div className="flex flex-wrap gap-1">
                {lang.engines.map((engine) => (
                  <span
                    key={engine}
                    className="rounded-full bg-zinc-100 px-2 py-0.5 text-xs font-medium dark:bg-zinc-700"
                  >
                    {engine}
                  </span>
                ))}
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="mb-12 rounded-2xl border border-zinc-200 bg-white p-6 dark:border-zinc-700 dark:bg-zinc-800">
        <h2 className="mb-4 text-2xl font-bold">How Language Support Works</h2>
        <div className="grid gap-6 md:grid-cols-2">
          <div>
            <h3 className="mb-3 font-semibold">Language Selection</h3>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li className="inline-flex items-start gap-2">
                <CheckCircle2 className="mt-0.5 h-4 w-4 flex-shrink-0 text-green-500" />
                Select your language in Settings → Speech Engine → Language
              </li>
              <li className="inline-flex items-start gap-2">
                <CheckCircle2 className="mt-0.5 h-4 w-4 flex-shrink-0 text-green-500" />
                Use "Auto" for automatic language detection (whisper.cpp/Whisper)
              </li>
              <li className="inline-flex items-start gap-2">
                <CheckCircle2 className="mt-0.5 h-4 w-4 flex-shrink-0 text-green-500" />
                Switch languages on-the-fly without restarting
              </li>
            </ul>
          </div>
          <div>
            <h3 className="mb-3 font-semibold">Model Selection</h3>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li className="inline-flex items-start gap-2">
                <CheckCircle2 className="mt-0.5 h-4 w-4 flex-shrink-0 text-green-500" />
                Larger models provide better accuracy for all languages
              </li>
              <li className="inline-flex items-start gap-2">
                <CheckCircle2 className="mt-0.5 h-4 w-4 flex-shrink-0 text-green-500" />
                "tiny" model works for all supported languages
              </li>
              <li className="inline-flex items-start gap-2">
                <CheckCircle2 className="mt-0.5 h-4 w-4 flex-shrink-0 text-green-500" />
                Models are downloaded automatically on first use
              </li>
            </ul>
          </div>
        </div>
      </section>

      <section className="rounded-2xl border border-zinc-200 bg-zinc-50 p-8 dark:border-zinc-700 dark:bg-zinc-900/60">
        <h2 className="mb-4 text-2xl font-bold">Ready to Dictate in Your Language?</h2>
        <p className="mb-6 text-muted-foreground">
          Install Vocalinux and start dictating in your preferred language. All processing happens
          locally on your Linux machine.
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
            href="/compare/"
            className="inline-flex items-center gap-2 rounded-lg border border-zinc-300 bg-white px-4 py-2 text-sm font-semibold hover:bg-zinc-50 dark:border-zinc-600 dark:bg-zinc-800 dark:hover:bg-zinc-700"
          >
            Compare Engines
          </Link>
        </div>
      </section>
    </SeoSubpageShell>
  );
}
