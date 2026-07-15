import Link from "next/link";
import { type Metadata } from "next";
import { Camera, ChevronRight, Download } from "lucide-react";
import {
  ScreenshotGallery,
  type Screenshot,
} from "@/components/screenshot-gallery";
import { SeoSubpageShell } from "@/components/seo-subpage-shell";
import { absoluteUrl, buildPageMetadata } from "@/lib/seo";

const productShots: Screenshot[] = [
  {
    src: "/screenshots/00-transcription.png",
    alt: "Vocalinux real-time transcription in action",
    title: "Transcription in action",
    description: "Dictate into any Linux app with real-time voice-to-text.",
    width: 2565,
    height: 2018,
  },
  {
    src: "/screenshots/02-system-tray.png",
    alt: "Vocalinux system tray listening indicator",
    title: "System tray",
    description: "Tray icon shows idle, listening, and processing states.",
    width: 565,
    height: 453,
  },
  {
    src: "/screenshots/05-about-view.png",
    alt: "Vocalinux About dialog",
    title: "About",
    description: "Version info, credits, and project links.",
    width: 1012,
    height: 854,
  },
  {
    src: "/screenshots/03-log-viewer.png",
    alt: "Vocalinux log viewer dialog",
    title: "Log viewer",
    description: "Inspect runtime logs when diagnosing dictation issues.",
    width: 1904,
    height: 1578,
  },
];

const settingsShots: Screenshot[] = [
  {
    src: "/screenshots/settings-speech-engine.png",
    alt: "Speech Engine settings tab",
    title: "Speech Engine",
    description:
      "Choose whisper.cpp, Whisper, VOSK, or Remote API and pick a model.",
    width: 1504,
    height: 2146,
  },
  {
    src: "/screenshots/settings-recognition.png",
    alt: "Recognition settings tab",
    title: "Recognition",
    description: "Language, voice commands, and recognition behavior.",
    width: 1504,
    height: 2146,
  },
  {
    src: "/screenshots/settings-audio.png",
    alt: "Audio settings tab",
    title: "Audio",
    description: "Input device, feedback sounds, and capture options.",
    width: 1504,
    height: 2146,
  },
  {
    src: "/screenshots/settings-shortcuts.png",
    alt: "Shortcuts and hotkeys settings tab",
    title: "Shortcuts & Hotkeys",
    description: "Toggle mode, push-to-talk, and custom key bindings.",
    width: 1504,
    height: 2146,
  },
  {
    src: "/screenshots/settings-general.png",
    alt: "General settings tab",
    title: "General",
    description: "Autostart, UI preferences, and everyday defaults.",
    width: 1504,
    height: 2146,
  },
  {
    src: "/screenshots/settings-advanced.png",
    alt: "Advanced tuning and settings tab",
    title: "Advanced",
    description: "Power-user decoding controls and Remote Server options.",
    width: 1504,
    height: 2146,
  },
];

export const metadata: Metadata = buildPageMetadata({
  title: "Vocalinux Screenshots | Linux Voice Dictation UI",
  description:
    "See Vocalinux in action: system tray, about dialog, log viewer, and the full settings tabs for speech engine, recognition, audio, shortcuts, general, and advanced options.",
  path: "/screenshots",
  keywords: [
    "Vocalinux screenshots",
    "Linux voice dictation UI",
    "offline speech recognition settings",
    "whisper.cpp Linux screenshots",
    "voice typing system tray Linux",
  ],
});

export default function ScreenshotsPage() {
  const articleJsonLd = {
    "@context": "https://schema.org",
    "@type": "ImageGallery",
    name: "Vocalinux Screenshots",
    description:
      "Product and settings screenshots of Vocalinux, offline voice dictation for Linux.",
    dateModified: "2026-07-15",
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
    mainEntityOfPage: absoluteUrl("/screenshots"),
  };

  return (
    <SeoSubpageShell>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(articleJsonLd) }}
      />

      <section>
        <p className="border-primary/30 bg-primary/10 mb-4 inline-flex items-center gap-2 rounded-full border px-4 py-1.5 text-sm font-medium text-primary">
          <Camera className="h-4 w-4" />
          v0.14.0 Beta UI
        </p>
        <h1 className="mb-5 text-4xl font-bold tracking-tight sm:text-5xl md:text-6xl">
          Vocalinux Screenshots
        </h1>
        <p className="mb-8 max-w-4xl text-lg text-muted-foreground">
          A look at offline voice dictation on Linux: tray controls, debugging
          tools, and the full settings dialog. Click any image to expand it and
          browse the gallery. These shots match the current v0.14.0-beta UI.
        </p>
      </section>

      <ScreenshotGallery
        productShots={productShots}
        settingsShots={settingsShots}
      />

      <section className="border-primary/20 bg-primary/5 rounded-2xl border p-8">
        <h2 className="mb-3 text-2xl font-bold">Try it yourself</h2>
        <p className="mb-6 max-w-2xl text-muted-foreground">
          Install Vocalinux and open Settings from the system tray to explore
          the same screens on your desktop.
        </p>
        <div className="flex flex-col gap-3 sm:flex-row">
          <Link
            href="/install/"
            className="hover:bg-primary/90 inline-flex items-center justify-center gap-2 rounded-xl bg-primary px-5 py-3 text-sm font-semibold text-primary-foreground dark:text-black"
          >
            <Download className="h-4 w-4" />
            Install guide
            <ChevronRight className="h-4 w-4" />
          </Link>
          <Link
            href="/advanced-settings/"
            className="inline-flex items-center justify-center gap-2 rounded-xl border border-zinc-300 bg-white px-5 py-3 text-sm font-semibold transition-colors hover:bg-zinc-50 dark:border-zinc-600 dark:bg-zinc-800 dark:hover:bg-zinc-700"
          >
            Advanced settings guide
            <ChevronRight className="h-4 w-4" />
          </Link>
        </div>
      </section>
    </SeoSubpageShell>
  );
}
