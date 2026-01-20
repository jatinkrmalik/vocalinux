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
      { url: "/vocalinux.svg", type: "image/svg+xml" },
    ],
    apple: [{ url: "/vocalinux.svg", type: "image/svg+xml" }],
    shortcut: "/vocalinux.svg"
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
  const jsonLd = {
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
    "softwareVersion": "0.2.0-alpha",
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

  return (
    <html lang="en" className={`${GeistSans.variable} scroll-smooth`} suppressHydrationWarning>
      <head>
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
        />
      </head>
      <body>
        {/* Google tag (gtag.js) */}
        <Script
          src="https://www.googletagmanager.com/gtag/js?id=G-7NBBNJNNQ7"
          strategy="afterInteractive"
        />
        <Script id="google-analytics" strategy="afterInteractive">
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
