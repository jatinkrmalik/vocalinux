import { Metadata } from "next";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { 
  Check, 
  X, 
  Shield, 
  Zap, 
  Globe,
  Lock,
  Cpu,
  Download
} from "lucide-react";

export const metadata: Metadata = {
  title: "Vocalinux vs Dragon NaturallySpeaking & Others | Linux Voice Dictation Comparison",
  description: "Compare Vocalinux to Dragon NaturallySpeaking, Windows Speech Recognition, and macOS Dictation. The only 100% offline, privacy-focused voice dictation for Linux. Free & open-source.",
  keywords: [
    "dragon naturallyspeaking linux alternative",
    "windows speech recognition linux",
    "macos dictation linux equivalent",
    "voice dictation software comparison",
    "offline voice recognition linux vs windows",
    "privacy focused dictation software",
    "dragon linux alternative",
    "best voice dictation software linux"
  ],
  alternates: {
    canonical: "https://vocalinux.com/compare",
  },
};

const comparisons = [
  {
    feature: "100% Offline",
    vocalinux: true,
    dragon: false,
    windows: false,
    macos: false,
    description: "No internet required, no cloud processing"
  },
  {
    feature: "Privacy - No Data Collection",
    vocalinux: true,
    dragon: false,
    windows: false,
    macos: false,
    description: "Voice data never leaves your machine"
  },
  {
    feature: "Works on Linux",
    vocalinux: true,
    dragon: false,
    windows: false,
    macos: false,
    description: "Native Linux application"
  },
  {
    feature: "Open Source",
    vocalinux: true,
    dragon: false,
    windows: false,
    macos: false,
    description: "GPL-3.0 licensed, auditable code"
  },
  {
    feature: "Free (No Subscription)",
    vocalinux: true,
    dragon: false,
    windows: true,
    macos: true,
    description: "No premium tiers or ongoing costs"
  },
  {
    feature: "GPU Acceleration",
    vocalinux: true,
    dragon: false,
    windows: false,
    macos: false,
    description: "Vulkan support for AMD, Intel, NVIDIA"
  },
  {
    feature: "Multiple Speech Engines",
    vocalinux: true,
    dragon: false,
    windows: false,
    macos: false,
    description: "Whisper, whisper.cpp, VOSK support"
  },
  {
    feature: "System-Wide Dictation",
    vocalinux: true,
    dragon: true,
    windows: false,
    macos: false,
    description: "Works in any application"
  }
];

const whyChoose = [
  {
    icon: Shield,
    title: "Privacy First",
    description: "While competitors send your voice to the cloud for processing, Vocalinux does everything locally. Your sensitive conversations, medical dictation, and personal notes stay on your machine."
  },
  {
    icon: Lock,
    title: "No Account Required",
    description: "No sign-ups, no logins, no telemetry. Just download and use. Your usage patterns aren't tracked, analyzed, or sold."
  },
  {
    icon: Cpu,
    title: "Superior Performance",
    description: "Thanks to whisper.cpp, Vocalinux offers faster transcription with lower resource usage than cloud-based alternatives. GPU acceleration works on ALL vendors, not just NVIDIA."
  },
  {
    icon: Globe,
    title: "True Linux Native",
    description: "Not a Windows app running in Wine, not a web wrapper - a genuine Linux application that integrates with your desktop environment, follows your themes, and respects your system."
  }
];

export default function ComparePage() {
  return (
    <div className="min-h-screen bg-background">
      {/* Hero */}
      <section className="relative pt-20 pb-16 md:pt-32 md:pb-24 overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-primary/5 to-transparent" />
        <div className="container mx-auto px-4 relative">
          <div className="max-w-4xl mx-auto text-center">
            <Badge className="mb-6" variant="secondary">
              Comparison Guide
            </Badge>
            <h1 className="text-4xl md:text-6xl font-bold tracking-tight mb-6">
              Vocalinux vs{" "}
              <span className="bg-gradient-to-r from-primary to-primary/70 bg-clip-text text-transparent">
                The Competition
              </span>
            </h1>
            <p className="text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
              The only 100% offline, privacy-focused voice dictation solution for Linux. 
              See how Vocalinux compares to Dragon, Windows Speech Recognition, and macOS Dictation.
            </p>
            <Button size="lg" asChild>
              <Link href="/">
                Try Vocalinux Free
              </Link>
            </Button>
          </div>
        </div>
      </section>

      {/* Comparison Table */}
      <section className="py-16 bg-muted/50">
        <div className="container mx-auto px-4">
          <div className="max-w-5xl mx-auto">
            <h2 className="text-3xl font-bold text-center mb-12">
              Feature Comparison
            </h2>
            <div className="overflow-x-auto">
              <table className="w-full bg-background rounded-lg shadow-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-left p-4 font-semibold">Feature</th>
                    <th className="text-center p-4 font-semibold text-primary">Vocalinux</th>
                    <th className="text-center p-4 font-semibold">Dragon</th>
                    <th className="text-center p-4 font-semibold">Windows</th>
                    <th className="text-center p-4 font-semibold">macOS</th>
                  </tr>
                </thead>
                <tbody>
                  {comparisons.map((row, index) => (
                    <tr key={index} className="border-b last:border-0">
                      <td className="p-4">
                        <div className="font-medium">{row.feature}</div>
                        <div className="text-sm text-muted-foreground">{row.description}</div>
                      </td>
                      <td className="text-center p-4">
                        {row.vocalinux ? (
                          <Check className="h-6 w-6 text-green-500 mx-auto" />
                        ) : (
                          <X className="h-6 w-6 text-red-400 mx-auto" />
                        )}
                      </td>
                      <td className="text-center p-4">
                        {row.dragon ? (
                          <Check className="h-6 w-6 text-green-500 mx-auto" />
                        ) : (
                          <X className="h-6 w-6 text-red-400 mx-auto" />
                        )}
                      </td>
                      <td className="text-center p-4">
                        {row.windows ? (
                          <Check className="h-6 w-6 text-green-500 mx-auto" />
                        ) : (
                          <X className="h-6 w-6 text-red-400 mx-auto" />
                        )}
                      </td>
                      <td className="text-center p-4">
                        {row.macos ? (
                          <Check className="h-6 w-6 text-green-500 mx-auto" />
                        ) : (
                          <X className="h-6 w-6 text-red-400 mx-auto" />
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </section>

      {/* Why Choose Vocalinux */}
      <section className="py-16 md:py-24">
        <div className="container mx-auto px-4">
          <div className="max-w-4xl mx-auto">
            <h2 className="text-3xl font-bold text-center mb-12">
              Why Linux Users Choose Vocalinux
            </h2>
            <div className="grid md:grid-cols-2 gap-8">
              {whyChoose.map((item, index) => (
                <Card key={index} className="border-0 shadow-sm">
                  <CardHeader>
                    <item.icon className="h-10 w-10 text-primary mb-2" />
                    <CardTitle>{item.title}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-muted-foreground">{item.description}</p>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Detailed Comparisons */}
      <section className="py-16 bg-muted/50">
        <div className="container mx-auto px-4">
          <div className="max-w-4xl mx-auto space-y-12">
            <div>
              <h3 className="text-2xl font-bold mb-4">Vocalinux vs Dragon NaturallySpeaking</h3>
              <div className="prose prose-slate max-w-none">
                <p>
                  Dragon NaturallySpeaking is the industry standard for Windows, but it comes with significant drawbacks 
                  that Vocalinux solves for Linux users:
                </p>
                <ul>
                  <li><strong>Cost:</strong> Dragon costs $500+ while Vocalinux is completely free</li>
                  <li><strong>Platform:</strong> Dragon doesn't support Linux; Vocalinux is Linux-native</li>
                  <li><strong>Privacy:</strong> Dragon may use cloud processing; Vocalinux is 100% offline</li>
                  <li><strong>Customization:</strong> Dragon is closed-source; Vocalinux is GPL-3.0 open source</li>
                </ul>
              </div>
            </div>

            <div>
              <h3 className="text-2xl font-bold mb-4">Vocalinux vs Windows Speech Recognition</h3>
              <div className="prose prose-slate max-w-none">
                <p>
                  Windows Speech Recognition is built into Windows but has limitations that Vocalinux overcomes:
                </p>
                <ul>
                  <li><strong>Platform Lock-in:</strong> Windows-only vs Linux-native</li>
                  <li><strong>Offline Capability:</strong> Windows Speech may use cloud; Vocalinux is always offline</li>
                  <li><strong>Accuracy:</strong> Vocalinux uses Whisper AI, generally more accurate than Windows</li>
                  <li><strong>GPU Acceleration:</strong> Vocalinux supports AMD, Intel, and NVIDIA GPUs</li>
                </ul>
              </div>
            </div>

            <div>
              <h3 className="text-2xl font-bold mb-4">Vocalinux vs macOS Dictation</h3>
              <div className="prose prose-slate max-w-none">
                <p>
                  macOS Dictation is convenient but lacks the control and privacy that Linux users expect:
                </p>
                <ul>
                  <li><strong>Cloud Dependency:</strong> macOS sends audio to Apple servers; Vocalinux is local-only</li>
                  <li><strong>Customization:</strong> Limited options on macOS; extensive configuration with Vocalinux</li>
                  <li><strong>Engine Choice:</strong> macOS uses one engine; Vocalinux supports Whisper, whisper.cpp, and VOSK</li>
                  <li><strong>Open Source:</strong> macOS is proprietary; Vocalinux code is fully auditable</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-16 bg-primary text-primary-foreground">
        <div className="container mx-auto px-4 text-center">
          <h2 className="text-3xl font-bold mb-4">
            Make the Switch to Privacy-First Dictation
          </h2>
          <p className="text-xl mb-8 opacity-90 max-w-2xl mx-auto">
            Join thousands who have switched from cloud-based solutions to Vocalinux. 
            Free, open-source, and 100% offline.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button size="lg" variant="secondary" className="gap-2" asChild>
              <Link href="/">
                <Download className="h-5 w-5" />
                Download Vocalinux
              </Link>
            </Button>
            <Button size="lg" variant="outline" className="border-primary-foreground/20 hover:bg-primary-foreground/10" asChild>
              <Link href="/install/ubuntu">
                Ubuntu Install Guide
              </Link>
            </Button>
          </div>
        </div>
      </section>
    </div>
  );
}
