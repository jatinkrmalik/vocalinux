import Link from "next/link";
import { type Metadata } from "next";
import { BookOpen, CheckCircle2, ChevronRight, Clock, Download, Sparkles, Tag, Zap } from "lucide-react";
import { SeoSubpageShell } from "@/components/seo-subpage-shell";
import { absoluteUrl, buildPageMetadata } from "@/lib/seo";

const releases = [
  {
    version: "v0.6.3-beta",
    date: "2026-02-19",
    type: "beta",
    highlights: [
      "Fixed installer default tag pointing to correct version",
      "Added missing psutil dependency for fresh installs",
      "Process check and interactive prompts in install/uninstall",
      "Removed leading space from first speech transcription",
    ],
  },
  {
    version: "v0.6.2-beta",
    date: "2026-02-18",
    type: "beta",
    highlights: [
      "Interactive backend selection (GPU/CPU)",
      "Enhanced welcome message",
      "Simplified install commands",
      "Better GPU support and Vulkan detection",
    ],
  },
  {
    version: "v0.6.0-beta",
    date: "2026-02-12",
    type: "beta",
    highlights: [
      "whisper.cpp as default engine",
      "Multi-language support with auto-detection",
      "System tray indicator",
      "Full Wayland support",
      "IBus text injection engine",
    ],
  },
  {
    version: "v0.5.0-beta",
    date: "2026-02-06",
    type: "beta",
    highlights: [
      "First beta release",
      "Stable core functionality",
      "Multiple speech engine support",
      "Improved text injection",
    ],
  },
  {
    version: "v0.4.1-alpha",
    date: "2026-01-29",
    type: "alpha",
    highlights: [
      "Language selector UI",
      "App drawer launch fix",
      "Better commit handling",
      "Improved update mechanism",
    ],
  },
  {
    version: "v0.4.0-alpha",
    date: "2026-01-29",
    type: "alpha",
    highlights: [
      "Multi-language support (French, German, Russian)",
      "Debian 13+ compatibility",
      "Python 3.12+ support",
      "Tag-based version selection in installer",
    ],
  },
  {
    version: "v0.3.0-alpha",
    date: "2026-01-21",
    type: "alpha",
    highlights: [
      "Initial public alpha",
      "Basic speech recognition",
      "X11 text injection",
      "VOSK engine support",
    ],
  },
];

const getTypeStyles = (type: string) => {
  switch (type) {
    case "stable":
      return {
        badge: "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400",
        label: "Stable",
      };
    case "beta":
      return {
        badge: "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400",
        label: "Beta",
      };
    case "alpha":
      return {
        badge: "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400",
        label: "Alpha",
      };
    default:
      return {
        badge: "bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-400",
        label: type,
      };
  }
};

export const metadata: Metadata = buildPageMetadata({
  title: "Vocalinux Changelog - Release History",
  description:
    "Track Vocalinux release history and version updates. See what's new in each version of our Linux voice dictation software.",
  path: "/changelog",
  keywords: [
    "vocalinux changelog",
    "vocalinux release notes",
    "voice dictation linux updates",
    "speech to text linux versions",
  ],
});

export default function ChangelogPage() {
  const articleJsonLd = {
    "@context": "https://schema.org",
    "@type": "Article",
    headline: "Vocalinux Changelog - Release History",
    description:
      "Complete release history for Vocalinux, the offline voice dictation software for Linux.",
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
    mainEntityOfPage: absoluteUrl("/changelog"),
  };

  return (
    <SeoSubpageShell>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(articleJsonLd) }}
      />

      <section>
        <p className="mb-4 inline-flex items-center gap-2 rounded-full border border-primary/30 bg-primary/10 px-4 py-1.5 text-sm font-medium text-primary">
          <Clock className="h-4 w-4" />
          Release History
        </p>
        <h1 className="mb-5 text-4xl font-bold tracking-tight sm:text-5xl md:text-6xl">
          Vocalinux Changelog
        </h1>
        <p className="mb-8 max-w-4xl text-lg text-muted-foreground">
          Track every release and see how Vocalinux has evolved. From initial alpha to stable
          releases, follow the journey of Linux voice dictation.
        </p>
      </section>

      <section className="space-y-6">
        {releases.map((release, index) => {
          const styles = getTypeStyles(release.type);
          return (
            <article
              key={release.version}
              className="rounded-2xl border border-zinc-200 bg-white p-6 dark:border-zinc-700 dark:bg-zinc-800"
            >
              <div className="mb-4 flex flex-wrap items-center gap-3">
                <div className="flex items-center gap-2">
                  <Tag className="h-5 w-5 text-primary" />
                  <span className="text-2xl font-bold">{release.version}</span>
                </div>
                <span
                  className={`rounded-full px-3 py-1 text-xs font-semibold ${styles.badge}`}
                >
                  {styles.label}
                </span>
                {index === 0 && (
                  <span className="rounded-full bg-primary/10 px-3 py-1 text-xs font-semibold text-primary">
                    Latest
                  </span>
                )}
                <span className="text-sm text-muted-foreground">{release.date}</span>
              </div>

              <ul className="space-y-2">
                {release.highlights.map((highlight) => (
                  <li key={highlight} className="inline-flex items-start gap-2 text-muted-foreground">
                    <CheckCircle2 className="mt-0.5 h-4 w-4 flex-shrink-0 text-green-500" />
                    {highlight}
                  </li>
                ))}
              </ul>

              <div className="mt-4 pt-4 border-t border-zinc-100 dark:border-zinc-700">
                <a
                  href={`https://github.com/jatinkrmalik/vocalinux/releases/tag/${release.version}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 text-sm font-medium text-primary hover:underline"
                >
                  <Download className="h-4 w-4" />
                  View release on GitHub
                  <ChevronRight className="h-4 w-4" />
                </a>
              </div>
            </article>
          );
        })}
      </section>

      <section className="mt-12 rounded-2xl border border-zinc-200 bg-zinc-50 p-8 dark:border-zinc-700 dark:bg-zinc-900/60">
        <h2 className="mb-4 text-2xl font-bold">Stay Updated</h2>
        <ul className="space-y-3 text-muted-foreground">
          <li className="inline-flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-primary" />
            Watch the repository on GitHub for release notifications
          </li>
          <li className="inline-flex items-center gap-2">
            <Zap className="h-4 w-4 text-primary" />
            Re-run the installer to update to the latest version
          </li>
          <li className="inline-flex items-center gap-2">
            <BookOpen className="h-4 w-4 text-primary" />
            Check the{" "}
            <Link href="/install/" className="font-semibold text-primary hover:underline">
              install guide
            </Link>{" "}
            for update instructions
          </li>
        </ul>
      </section>
    </SeoSubpageShell>
  );
}
