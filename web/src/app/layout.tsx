import "@/styles/globals.css";
import React from "react";
import { GeistSans } from "geist/font/sans";
import { type Metadata } from "next";
import { ThemeProvider } from "@/components/theme-provider";
import { DevtoolsProvider } from 'creatr-devtools';
export const viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1
};
export const metadata: Metadata = {
  title: {
    default: "Vocalinux - Open-Source Voice Dictation for Linux",
    template: "%s | Vocalinux"
  },
  description: "Open-source offline voice dictation for Linux using Whisper models. Privacy-focused with no cloud dependencies.",
  applicationName: "Vocalinux",
  keywords: ["voice dictation", "linux", "speech recognition", "whisper", "offline", "privacy", "x11", "wayland", "open-source"],
  authors: [{
    name: "Vocalinux Team"
  }],
  creator: "Vocalinux Team",
  publisher: "Vocalinux Team",
  icons: {
    icon: [{
      url: "/favicon-16x16.png",
      sizes: "16x16",
      type: "image/png"
    }, {
      url: "/favicon-32x32.png",
      sizes: "32x32",
      type: "image/png"
    }, {
      url: "/favicon.ico",
      sizes: "48x48",
      type: "image/x-icon"
    }],
    apple: [{
      url: "/apple-touch-icon.png",
      sizes: "180x180",
      type: "image/png"
    }]
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
    url: "https://github.com/jatinkrmalik/vocalinux",
    siteName: "Vocalinux",
    title: "Vocalinux - Open-Source Voice Dictation for Linux",
    description: "Open-source offline voice dictation for Linux using Whisper models. Works with X11 and Wayland.",
    images: [{
      url: "https://picsum.photos/200",
      width: 1280,
      height: 640,
      alt: "Vocalinux Open-Source Voice Dictation"
    }]
  },
  twitter: {
    card: "summary_large_image",
    title: "Vocalinux - Open-Source Voice Dictation for Linux",
    description: "Open-source offline voice dictation for Linux using Whisper models. Works with X11 and Wayland.",
    images: ["https://picsum.photos/200"]
  }
};
export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  return <html lang="en" className={`${GeistSans.variable} scroll-smooth`} suppressHydrationWarning data-unique-id="e40c53aa-a38b-4d6a-8168-f4c83a429623" data-file-name="app/layout.tsx">
      <body data-unique-id="ae9bfce5-4f02-4d18-943e-7fdb835c2363" data-file-name="app/layout.tsx">
        <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
          <DevtoolsProvider>{children}</DevtoolsProvider>
        </ThemeProvider>
      </body>
    </html>;
}