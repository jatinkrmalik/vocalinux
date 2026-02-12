import "@/styles/globals.css";
import React from "react";
import { GeistSans } from "geist/font/sans";
import { type Metadata } from "next";
import Script from "next/script";
import { ThemeProvider } from "@/components/theme-provider";

export const viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 5,
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#ffffff" },
    { media: "(prefers-color-scheme: dark)", color: "#18181b" },
  ],
};

export const metadata: Metadata = {
  metadataBase: new URL("https://vocalinux.com"),
  title: {
    default: "Vocalinux - Voice Dictation for Linux, Finally Done Right",
    template: "%s | Vocalinux"
  },
  description: "Free, open-source voice dictation for Linux. 100% offline with Whisper AI. Double-tap Ctrl to start. Works everywhere - X11 & Wayland. One-click install.",
  applicationName: "Vocalinux",
  keywords: [
    "voice dictation linux",
    "speech to text linux",
    "linux voice typing",
    "whisper linux",
    "vosk linux",
    "offline voice dictation",
    "privacy voice recognition",
    "speech recognition linux",
    "dictation software ubuntu",
    "voice typing fedora",
    "wayland voice dictation",
    "x11 speech to text",
    "open source dictation",
    "free speech recognition",
    "linux accessibility",
    "hands free typing linux",
    "voice commands linux",
    "GTK voice dictation"
  ],
  authors: [{ name: "Jatin K Malik", url: "https://github.com/jatinkrmalik" }],
  creator: "Jatin K Malik",
  publisher: "Vocalinux",
  icons: {
    icon: [
      { url: "/vocalinux.png", type: "image/png" },
      { url: "/favicon-16x16.png", sizes: "16x16", type: "image/png" },
      { url: "/favicon-32x32.png", sizes: "32x32", type: "image/png" },
      { url: "/favicon-96x96.png", sizes: "96x96", type: "image/png" },
    ],
    apple: [{ url: "/apple-touch-icon.png", sizes: "180x180", type: "image/png" }],
    shortcut: "/vocalinux.png"
  },
  manifest: "/site.webmanifest",
  appleWebApp: {
    capable: true,
    statusBarStyle: "default",
    title: "Vocalinux"
  },
  formatDetection: {
    telephone: false
  },
  openGraph: {
    type: "website",
    locale: "en_US",
    url: "https://vocalinux.com",
    siteName: "Vocalinux",
    title: "Vocalinux - Voice Dictation for Linux, Finally Done Right",
    description: "Free, open-source voice dictation for Linux. 100% offline & private with Whisper AI and VOSK. Double-tap Ctrl to start dictating in any app.",
    images: [{
      url: "/og-image.png",
      width: 1200,
      height: 630,
      alt: "Vocalinux - Voice Dictation for Linux"
    }]
  },
  twitter: {
    card: "summary_large_image",
    title: "Vocalinux - Voice Dictation for Linux, Finally Done Right",
    description: "Free, open-source voice dictation for Linux. 100% offline & private. Double-tap Ctrl to start dictating in any app.",
    images: ["/og-image.png"],
    creator: "@jatinkrmalik"
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-video-preview": -1,
      "max-image-preview": "large",
      "max-snippet": -1,
    },
  },
  alternates: {
    canonical: "https://vocalinux.com",
  },
  category: "Technology",
};
export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  // SoftwareApplication schema
  const softwareAppJsonLd = {
    "@context": "https://schema.org",
    "@type": "SoftwareApplication",
    "name": "Vocalinux",
    "applicationCategory": "UtilitiesApplication",
    "operatingSystem": "Linux",
    "offers": {
      "@type": "Offer",
      "price": "0",
      "priceCurrency": "USD"
    },
    "description": "Free, open-source voice dictation for Linux. 100% offline with Whisper AI and VOSK. Works with X11 and Wayland.",
    "softwareVersion": "0.6.0-beta",
    "author": {
      "@type": "Person",
      "name": "Jatin K Malik",
      "url": "https://github.com/jatinkrmalik"
    },
    "url": "https://vocalinux.com",
    "downloadUrl": "https://github.com/jatinkrmalik/vocalinux",
    "screenshot": "https://vocalinux.com/og-image.png",
    "featureList": [
      "100% offline voice recognition",
      "Privacy-focused - no cloud dependencies",
      "Works with all Linux applications",
      "X11 and Wayland support",
      "Double-tap Ctrl activation",
      "Whisper AI and VOSK engines",
      "Voice commands for punctuation",
      "System tray integration"
    ]
  };

  // Organization schema
  const organizationJsonLd = {
    "@context": "https://schema.org",
    "@type": "Organization",
    "name": "Vocalinux",
    "url": "https://vocalinux.com",
    "logo": "https://vocalinux.com/vocalinux.png",
    "description": "Free, open-source voice dictation for Linux",
    "sameAs": [
      "https://github.com/jatinkrmalik/vocalinux"
    ],
    "author": {
      "@type": "Person",
      "name": "Jatin K Malik",
      "url": "https://github.com/jatinkrmalik"
    }
  };

  // WebSite schema
  const webSiteJsonLd = {
    "@context": "https://schema.org",
    "@type": "WebSite",
    "name": "Vocalinux",
    "url": "https://vocalinux.com",
    "description": "Voice dictation for Linux, finally done right. 100% offline and privacy-focused.",
    "potentialAction": {
      "@type": "SearchAction",
      "target": {
        "@type": "EntryPoint",
        "urlTemplate": "https://github.com/jatinkrmalik/vocalinux/issues?q={search_term_string}"
      },
      "query-input": {
        "@type": "PropertyValueSpecification",
        "valueRequired": true,
        "valueName": "search_term_string"
      }
    }
  };

  // FAQPage schema for rich results
  const faqJsonLd = {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    "mainEntity": [
      {
        "@type": "Question",
        "name": "Is Vocalinux really 100% offline?",
        "acceptedAnswer": {
          "@type": "Answer",
          "text": "Yes! All speech recognition processing happens locally on your machine. Your voice data never leaves your computer. No internet connection is required after installation."
        }
      },
      {
        "@type": "Question",
        "name": "Which Linux distributions are supported?",
        "acceptedAnswer": {
          "@type": "Answer",
          "text": "Vocalinux works on most modern Linux distributions including Ubuntu 22.04+, Fedora, Debian, Arch Linux, Linux Mint, Pop!_OS, and more. It supports both X11 and Wayland display servers."
        }
      },
      {
        "@type": "Question",
        "name": "How do I switch between Whisper and VOSK?",
        "acceptedAnswer": {
          "@type": "Answer",
          "text": "You can switch engines via the settings GUI or command line. Use 'vocalinux --engine whisper' or 'vocalinux --engine vosk'. Whisper is recommended for accuracy, VOSK for speed."
        }
      },
      {
        "@type": "Question",
        "name": "What are the system requirements?",
        "acceptedAnswer": {
          "@type": "Answer",
          "text": "Minimum: 4GB RAM, dual-core CPU, Python 3.8+. For Whisper large models: 8GB+ RAM recommended. The tiny/base Whisper models and VOSK work great on modest hardware."
        }
      },
      {
        "@type": "Question",
        "name": "Can I use it in languages other than English?",
        "acceptedAnswer": {
          "@type": "Answer",
          "text": "Yes! Whisper supports 99+ languages with varying accuracy levels. VOSK has models for 20+ languages. Download additional language models as needed."
        }
      },
      {
        "@type": "Question",
        "name": "How do I customize the activation shortcut?",
        "acceptedAnswer": {
          "@type": "Answer",
          "text": "The default is double-tap Ctrl. You can customize this via the GUI settings dialog or by editing ~/.config/vocalinux/config.yaml. Any key combination is supported."
        }
      },
      {
        "@type": "Question",
        "name": "Is Vocalinux free?",
        "acceptedAnswer": {
          "@type": "Answer",
          "text": "Yes, Vocalinux is completely free and open-source, licensed under GPL-3.0. No premium tiers, no subscriptions, no tracking — just free software."
        }
      }
    ]
  };

  // HowTo schema for installation guide
  const howToJsonLd = {
    "@context": "https://schema.org",
    "@type": "HowTo",
    "name": "How to Install Vocalinux on Linux",
    "description": "Step-by-step guide to install Vocalinux voice dictation software on Linux",
    "totalTime": "PT10M",
    "estimatedCost": {
      "@type": "MonetaryAmount",
      "currency": "USD",
      "value": "0"
    },
    "step": [
      {
        "@type": "HowToStep",
        "name": "Run the installation command",
        "text": "Open your terminal and run the one-liner installation command to download and install Vocalinux.",
        "url": "https://vocalinux.com/#install"
      },
      {
        "@type": "HowToStep",
        "name": "Wait for installation to complete",
        "text": "The installer will download dependencies, set up the environment, and download speech recognition models. This takes approximately 5-10 minutes.",
        "url": "https://vocalinux.com/#install"
      },
      {
        "@type": "HowToStep",
        "name": "Launch Vocalinux",
        "text": "After installation, launch Vocalinux from your terminal by typing 'vocalinux' or find it in your application menu.",
        "url": "https://vocalinux.com/#install"
      },
      {
        "@type": "HowToStep",
        "name": "Start dictating",
        "text": "Double-tap Ctrl to start voice dictation. Speak clearly into your microphone. Double-tap Ctrl again to stop.",
        "url": "https://vocalinux.com/#install"
      }
    ]
  };

  const jsonLd = [softwareAppJsonLd, organizationJsonLd, webSiteJsonLd, faqJsonLd, howToJsonLd];

  return (
    <html lang="en" className={`${GeistSans.variable} scroll-smooth`} suppressHydrationWarning>
      <head>
        {/* Preconnect to GitHub API for faster fetch of stars and release info (~300ms improvement) */}
        <link rel="preconnect" href="https://api.github.com" />
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
        />
      </head>
      <body>
        {/* Google tag (gtag.js) - deferred to prioritize page interactivity */}
        <Script
          src="https://www.googletagmanager.com/gtag/js?id=G-7NBBNJNNQ7"
          strategy="lazyOnload"
        />
        <Script id="google-analytics" strategy="lazyOnload">
          {`
            window.dataLayer = window.dataLayer || [];
            function gtag(){dataLayer.push(arguments);}
            gtag('js', new Date());
            gtag('config', 'G-7NBBNJNNQ7');
          `}
        </Script>
        <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
          {children}
        </ThemeProvider>
      </body>
    </html>
  );
}
