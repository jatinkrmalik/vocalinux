"use client";

import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { useDoublePress } from "@/hooks/use-double-press";
import { DictationOverlay } from "@/components/dictation-overlay";
import { Mic, Terminal, Lock, Zap, Laptop, Keyboard, Settings, Code, Github, BookOpen, MessageSquare, Edit, Star, Download, ExternalLink, ChevronRight, CheckCircle2, Menu, X } from "lucide-react";
import { ThemeToggle } from "@/components/theme-toggle";
import { VocalinuxLogo } from "@/components/icons";
import SyntaxHighlighter from "react-syntax-highlighter";
import { atomOneDark } from "react-syntax-highlighter/dist/esm/styles/hljs";
import { useInView } from "react-intersection-observer";
const installCommand = `# Install Vocalinux
git clone https://github.com/jatinkrmalik/vocalinux.git
cd vocalinux
pip install -r requirements.txt
python cli.py install`;
const FeatureCard = ({
  icon,
  title,
  description
}) => {
  const [ref, inView] = useInView({
    triggerOnce: true,
    threshold: 0.1
  });
  return <motion.div ref={ref} initial={{
    opacity: 0,
    y: 20
  }} animate={inView ? {
    opacity: 1,
    y: 0
  } : {
    opacity: 0,
    y: 20
  }} transition={{
    duration: 0.5
  }} className="bg-white dark:bg-zinc-800 p-4 sm:p-6 rounded-xl shadow-md hover:shadow-lg transition-all h-full">
      <div className="flex items-center gap-3 sm:gap-4 mb-3 sm:mb-4">
        <div className="bg-primary/10 p-2 sm:p-3 rounded-lg">
          {icon}
        </div>
        <h3 className="text-lg sm:text-xl font-semibold">{title}</h3>
      </div>
      <p className="text-sm sm:text-base text-muted-foreground">{description}</p>
    </motion.div>;
};
const CopyToClipboard = ({
  text
}) => {
  const [copied, setCopied] = useState(false);
  const handleCopy = () => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };
  return <button onClick={handleCopy} className="absolute top-2 sm:top-4 right-2 sm:right-4 bg-zinc-700 hover:bg-zinc-600 text-white px-2 sm:px-3 py-0.5 sm:py-1 rounded text-xs sm:text-sm transition-colors" aria-label={copied ? "Copied to clipboard" : "Copy to clipboard"}>
      {copied ? "Copied!" : "Copy"}
    </button>;
};
const FadeInSection = ({
  children,
  delay = 0
}) => {
  const [ref, inView] = useInView({
    triggerOnce: true,
    threshold: 0.1,
    rootMargin: "0px 0px -50px 0px"
  });
  return <motion.div ref={ref} initial={{
    opacity: 0,
    y: 20
  }} animate={inView ? {
    opacity: 1,
    y: 0
  } : {
    opacity: 0,
    y: 20
  }} transition={{
    duration: 0.5,
    delay
  }} className="w-full">
      {children}
    </motion.div>;
};
export default function HomePage() {
  const [stars, setStars] = useState(0);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const {
    isActive: isDictating,
    resetActive: resetDictation
  } = useDoublePress({
    key: "Control",
    onDoublePress: () => {
      // When double Ctrl press is detected, the overlay will show automatically
      console.log("Double Ctrl press detected!");
    }
  });
  useEffect(() => {
    // Set a placeholder value for stars
    setStars(1247);
  }, []);
  return <main className="min-h-screen bg-[#f9f9fb] dark:bg-zinc-900" data-unique-id="df2e9c82-c659-4949-8956-6373352b02e4" data-file-name="app/page.tsx" data-dynamic-text="true">
      {/* Dictation Overlay */}
      <DictationOverlay isActive={isDictating} onAnimationComplete={resetDictation} />
      {/* Header with Theme Toggle */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-background/80 backdrop-blur-md border-b border-border py-3" data-unique-id="a9887d87-037e-4467-8ff8-ab1727f90ccf" data-file-name="app/page.tsx" data-dynamic-text="true">
        <nav className="max-w-7xl mx-auto px-4 sm:px-6 flex items-center justify-between" data-unique-id="f6d83077-8a68-4ae0-90fe-499ae61acd42" data-file-name="app/page.tsx" data-dynamic-text="true">
          <div className="flex items-center gap-2" data-unique-id="d4720bef-9520-425d-9d92-53745c848cf1" data-file-name="app/page.tsx">
            <VocalinuxLogo className="h-6 w-6 sm:h-8 sm:w-8 text-primary" />
            <span className="font-bold text-lg sm:text-xl" data-unique-id="819241f4-07a0-42a3-a42e-c8983acca42c" data-file-name="app/page.tsx"><span className="editable-text" data-unique-id="7288898b-2d18-4ff3-84b7-26cba8d239a4" data-file-name="app/page.tsx">Vocalinux</span></span>
          </div>
      
          {/* Desktop navigation */}
          <div className="hidden md:flex items-center gap-4" data-unique-id="20286544-b308-4b2b-98bd-77741a4ae713" data-file-name="app/page.tsx">
            <a href="#problem-statement" className="text-muted-foreground hover:text-foreground transition-colors" data-unique-id="68561601-c17c-492d-b374-873c11bdcb05" data-file-name="app/page.tsx"><span className="editable-text" data-unique-id="09c350f1-8736-4b2f-84d1-688966ad8bd7" data-file-name="app/page.tsx">Overview</span></a>
            <a href="#features-section" className="text-muted-foreground hover:text-foreground transition-colors" data-unique-id="324b04d2-5397-468c-8da7-a032b66497f7" data-file-name="app/page.tsx"><span className="editable-text" data-unique-id="1ffa5370-9586-4235-b851-13d6ececcd13" data-file-name="app/page.tsx">Features</span></a>
            <a href="#how-it-works" className="text-muted-foreground hover:text-foreground transition-colors" data-unique-id="ecea679a-f6fc-4f8b-ac06-87eeb67af6de" data-file-name="app/page.tsx"><span className="editable-text" data-unique-id="ef216326-9032-4ddd-af0b-a8e2cf4c294e" data-file-name="app/page.tsx">How It Works</span></a>
            <a href="#demo-section" className="text-muted-foreground hover:text-foreground transition-colors" data-unique-id="a5a560ba-e4f8-432a-8b60-6b9e6cd6e0b2" data-file-name="app/page.tsx"><span className="editable-text" data-unique-id="adba17ff-1d85-4b26-bbb6-416b8a03d954" data-file-name="app/page.tsx">Demo</span></a>
            <a href="#installation" className="text-muted-foreground hover:text-foreground transition-colors" data-unique-id="cb007b08-2202-4fec-84ef-9ef39fb13bd6" data-file-name="app/page.tsx"><span className="editable-text" data-unique-id="08efd2b0-513e-41b9-b834-d0ceca887e1d" data-file-name="app/page.tsx">Install</span></a>
            <a href="https://github.com/jatinkrmalik/vocalinux" target="_blank" rel="noopener noreferrer" className="text-muted-foreground hover:text-foreground transition-colors" data-unique-id="468ff9db-2b92-41f1-a28d-6827f94968a0" data-file-name="app/page.tsx"><span className="editable-text" data-unique-id="23f46fa0-8e0e-444a-88bf-534b94ddd745" data-file-name="app/page.tsx">GitHub</span></a>
            <ThemeToggle />
          </div>
      
          {/* Mobile navigation toggle */}
          <div className="flex md:hidden items-center gap-3" data-unique-id="bcbea083-c6cb-4be6-b9a7-2c011a40d0ca" data-file-name="app/page.tsx">
            <ThemeToggle />
            <button onClick={() => setMobileMenuOpen(!mobileMenuOpen)} className="p-2 text-foreground focus:outline-none" aria-label="Toggle menu" data-unique-id="7e26d308-72f2-46c9-8f4f-0b9c431406c3" data-file-name="app/page.tsx">
              <motion.div animate={mobileMenuOpen ? "open" : "closed"} data-unique-id="9155865b-a563-4fab-a4d2-a30e66456902" data-file-name="app/page.tsx" data-dynamic-text="true">
                {mobileMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
              </motion.div>
            </button>
          </div>
        </nav>
    
        {/* Mobile menu */}
        <motion.div initial={{
        height: 0,
        opacity: 0
      }} animate={{
        height: mobileMenuOpen ? 'auto' : 0,
        opacity: mobileMenuOpen ? 1 : 0
      }} transition={{
        duration: 0.3
      }} className="md:hidden overflow-hidden bg-background border-b border-border" data-unique-id="1a8b9a37-adc2-4fa1-bc44-f29fd71c9174" data-file-name="app/page.tsx">
          <div className="px-4 py-3 space-y-4" data-unique-id="4bd61896-ee44-4274-ae20-79d0d4b8a600" data-file-name="app/page.tsx">
            <a href="#problem-statement" className="block py-2 text-foreground hover:text-primary transition-colors" onClick={() => setMobileMenuOpen(false)} data-unique-id="3fe8df1d-51bb-4259-a515-76042509ea18" data-file-name="app/page.tsx"><span className="editable-text" data-unique-id="ee267f61-8f9e-49e8-b1c5-712b4b67129c" data-file-name="app/page.tsx">
              Overview
            </span></a>
            <a href="#features-section" className="block py-2 text-foreground hover:text-primary transition-colors" onClick={() => setMobileMenuOpen(false)} data-unique-id="6289aba8-f47e-4b78-9dc2-503802a50e7f" data-file-name="app/page.tsx"><span className="editable-text" data-unique-id="78733e38-8308-4415-852b-ec53a61f9017" data-file-name="app/page.tsx">
              Features
            </span></a>
            <a href="#how-it-works" className="block py-2 text-foreground hover:text-primary transition-colors" onClick={() => setMobileMenuOpen(false)} data-unique-id="696f274a-d6de-44cc-a484-c4b7882286f3" data-file-name="app/page.tsx"><span className="editable-text" data-unique-id="80d1370a-5c5f-4b23-8096-1d15d0ce4da7" data-file-name="app/page.tsx">
              How It Works
            </span></a>
            <a href="#demo-section" className="block py-2 text-foreground hover:text-primary transition-colors" onClick={() => setMobileMenuOpen(false)} data-unique-id="3ec55f5c-6335-4508-bf84-0854ebdb4edb" data-file-name="app/page.tsx"><span className="editable-text" data-unique-id="a9f5eadf-c7bf-4f67-aeab-9791dfed19cb" data-file-name="app/page.tsx">
              Demo
            </span></a>
            <a href="#installation" className="block py-2 text-foreground hover:text-primary transition-colors" onClick={() => setMobileMenuOpen(false)} data-unique-id="019a6817-9855-4820-9727-5504a22e8894" data-file-name="app/page.tsx"><span className="editable-text" data-unique-id="07ac5588-7ed0-4ebb-ad62-81f054466662" data-file-name="app/page.tsx">
              Install
            </span></a>
            <a href="https://github.com/jatinkrmalik/vocalinux" target="_blank" rel="noopener noreferrer" className="block py-2 text-foreground hover:text-primary transition-colors" onClick={() => setMobileMenuOpen(false)} data-unique-id="4a73221b-bead-45fe-9e71-b21d65bb363f" data-file-name="app/page.tsx"><span className="editable-text" data-unique-id="a3f0e792-fdaf-47b1-a3d3-9baef58028e7" data-file-name="app/page.tsx">
              GitHub
            </span></a>
          </div>
        </motion.div>
      </header>

      {/* Hero Section */}
      <section className="relative pt-24 sm:pt-28 md:pt-40 pb-12 sm:pb-16 md:pb-32 px-4 sm:px-6 overflow-hidden" data-unique-id="606c411a-3268-437b-9091-3da641cbfe63" data-file-name="app/page.tsx">
        <div className="absolute inset-0 bg-gradient-to-b from-primary/5 to-transparent dark:from-primary/10" data-unique-id="feb86fae-95d5-40a3-9c00-dd0da7b3e6a6" data-file-name="app/page.tsx"></div>
        <div className="max-w-7xl mx-auto relative" data-unique-id="6daa3245-1781-4458-8c44-7bd838681621" data-file-name="app/page.tsx">
          <div className="flex flex-col md:flex-row items-center justify-between gap-8 md:gap-10" data-unique-id="d2f0bd08-12b1-447d-bf14-8292a8cf8cb2" data-file-name="app/page.tsx">
            <div className="w-full md:flex-1" data-unique-id="a7152976-0675-4068-9c15-880f8393de96" data-file-name="app/page.tsx">
              <motion.div initial={{
              opacity: 0,
              y: 20
            }} animate={{
              opacity: 1,
              y: 0
            }} transition={{
              duration: 0.7
            }} data-unique-id="ca216bef-7248-47f4-be03-b30f7133295f" data-file-name="app/page.tsx">
                <div className="flex flex-wrap items-center gap-2 mb-4 sm:mb-6" data-unique-id="49ff5b6d-f99b-4bc7-af66-3d02388be767" data-file-name="app/page.tsx">
                  <div className="flex items-center gap-2 bg-primary/10 px-3 sm:px-4 py-1 rounded-full" data-unique-id="bf7c1f66-536f-4016-97c5-42782bd4576b" data-file-name="app/page.tsx">
                    <Mic className="h-3 w-3 sm:h-4 sm:w-4 text-primary" />
                    <span className="text-xs sm:text-sm font-medium text-primary whitespace-nowrap" data-unique-id="32780a75-ca84-41eb-aa0f-3892528af425" data-file-name="app/page.tsx"><span className="editable-text" data-unique-id="7198b162-a179-45b6-b46e-bc591f58295f" data-file-name="app/page.tsx">Open-Source Voice Dictation for Linux</span></span>
                  </div>
                </div>
                <h1 className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl font-bold tracking-tight mb-4 sm:mb-6" data-unique-id="675f4957-2fe7-4ff8-af26-b5eac38f48fd" data-file-name="app/page.tsx"><span className="editable-text" data-unique-id="86c130bf-fb2f-4d1c-8eb4-d6f2cc5881d6" data-file-name="app/page.tsx">
                  Linux Voice Dictation with</span>{" "}
                  <span className="text-primary" data-unique-id="64cc624a-a832-4669-bfc5-5777172a6a40" data-file-name="app/page.tsx"><span className="editable-text" data-unique-id="304a84d8-d43e-4a06-9139-7c3fce718ae4" data-file-name="app/page.tsx">Vocalinux</span></span>
                </h1>
                <p className="text-base sm:text-lg md:text-xl text-muted-foreground mb-6 sm:mb-8 max-w-2xl" data-unique-id="166bc072-44ce-4b8d-bed0-8ef174a5fb37" data-file-name="app/page.tsx"><span className="editable-text" data-unique-id="02cc0486-531e-4ac4-81ca-90f77b7bea9d" data-file-name="app/page.tsx">
                  Open-source offline voice dictation for Linux with universal application support.
                  Privacy-focused speech-to-text with no cloud dependencies.
                </span></p>
                <div className="flex flex-wrap gap-3 sm:gap-4" data-unique-id="048cfeef-fc60-45b7-9452-fb0c7b107f83" data-file-name="app/page.tsx">
                  <a href="#installation" className="bg-primary text-primary-foreground hover:bg-primary/90 px-4 sm:px-6 py-2 sm:py-3 rounded-lg text-sm sm:text-base font-medium flex items-center gap-2 transition-colors" data-unique-id="3179f301-2344-48d5-a9f6-1eea8b9c3d3e" data-file-name="app/page.tsx">
                    <Download className="h-4 w-4 sm:h-5 sm:w-5" /><span className="editable-text" data-unique-id="43178628-5fd6-43cc-8fa2-c840b848f802" data-file-name="app/page.tsx">
                    Install Vocalinux
                  </span></a>
                  <a href="https://github.com/jatinkrmalik/vocalinux" target="_blank" rel="noopener noreferrer" className="bg-secondary text-secondary-foreground hover:bg-secondary/80 px-4 sm:px-6 py-2 sm:py-3 rounded-lg text-sm sm:text-base font-medium flex items-center gap-2 transition-colors" data-unique-id="758f601f-a825-4a85-a2b1-fb477d94bc4b" data-file-name="app/page.tsx">
                    <Github className="h-4 w-4 sm:h-5 sm:w-5" /><span className="editable-text" data-unique-id="64197fe8-8af8-40a6-9e07-e440e82eaf18" data-file-name="app/page.tsx">
                    Star on GitHub
                    </span><div className="flex items-center bg-white/20 dark:bg-black/20 px-2 py-0.5 rounded text-xs sm:text-sm" data-unique-id="31e83170-84c8-42ee-a1ac-65b741afd090" data-file-name="app/page.tsx" data-dynamic-text="true">
                      {stars}
                    </div>
                  </a>
                </div>
              </motion.div>
            </div>
            <div className="w-full md:flex-1 mt-8 md:mt-0" data-unique-id="995c40e2-0fb8-4ee2-8040-29d4668600ce" data-file-name="app/page.tsx">
              <motion.div initial={{
              opacity: 0,
              y: 30
            }} animate={{
              opacity: 1,
              y: 0
            }} transition={{
              duration: 0.7,
              delay: 0.2
            }} className="relative" data-unique-id="573bf9ad-3264-4b52-9724-a851fb765e9a" data-file-name="app/page.tsx">
                <div className="bg-white dark:bg-zinc-800 rounded-xl shadow-xl overflow-hidden h-[400px] flex items-center justify-center" data-unique-id="c348722a-e60c-45e1-adb7-7724157107c2" data-file-name="app/page.tsx">
                  <div className="relative w-full h-full flex flex-col items-center justify-center" data-unique-id="c428f61e-ac56-4f9d-8e2b-7aaaac9a8117" data-file-name="app/page.tsx" data-dynamic-text="true">
                    {/* Clean space with gradient background */}
                    <div className="absolute inset-0 bg-gradient-to-br from-background to-background/50" data-unique-id="3478d3cd-fdaa-41ef-b512-d62ff035f42a" data-file-name="app/page.tsx"></div>
                    
                    {/* Double Ctrl Key Visualization */}
                    <div className="relative z-10 flex flex-col items-center" data-unique-id="780fcacc-df3a-435d-8a42-a399e268c4de" data-file-name="app/page.tsx" data-dynamic-text="true">
                      {/* First Ctrl Key - Already Pressed */}
                      <motion.div initial={{
                      y: 0
                    }} animate={{
                      y: 8
                    }} transition={{
                      repeat: Infinity,
                      repeatType: "reverse",
                      duration: 1.2,
                      delay: 0
                    }} className="mb-6 relative" data-unique-id="7543f8bd-588e-479b-a000-0ae4671081b8" data-file-name="app/page.tsx" data-dynamic-text="true">
                        <div className="w-40 h-14 bg-primary/10 rounded-lg flex items-center justify-center border-2 border-primary shadow-inner transform" data-unique-id="dead6850-a337-4184-98e1-8cfa68ee3c42" data-file-name="app/page.tsx">
                          <span className="text-xl font-bold text-primary" data-unique-id="254184b4-e459-4c86-9374-869a5dd3c598" data-file-name="app/page.tsx"><span className="editable-text" data-unique-id="23448304-049c-4a70-8d62-ef47db3cde2c" data-file-name="app/page.tsx">Ctrl</span></span>
                        </div>
                        {/* Press indicator */}
                        <motion.div initial={{
                        opacity: 0.3
                      }} animate={{
                        opacity: 0.7
                      }} transition={{
                        repeat: Infinity,
                        repeatType: "reverse",
                        duration: 1.2,
                        delay: 0
                      }} className="absolute -bottom-3 left-0 right-0 mx-auto w-32 h-1 bg-primary rounded-full" data-unique-id="f3ca7e01-198d-4800-9c37-438181e145bf" data-file-name="app/page.tsx" />
                      </motion.div>
                      
                      {/* Second Ctrl Key - Being Pressed */}
                      <motion.div initial={{
                      y: 0
                    }} animate={{
                      y: 8
                    }} transition={{
                      repeat: Infinity,
                      repeatType: "reverse",
                      duration: 1.2,
                      delay: 0.3
                    }} className="relative" data-unique-id="f5ed4f96-d9d7-4d70-8d51-df8ea96ee24a" data-file-name="app/page.tsx" data-dynamic-text="true">
                        <div className="w-40 h-14 bg-primary/20 rounded-lg flex items-center justify-center border-2 border-primary shadow-lg" data-unique-id="211a9bf9-798f-4aca-bbec-7bc8511edf33" data-file-name="app/page.tsx">
                          <span className="text-xl font-bold text-primary" data-unique-id="aee09585-653c-490a-a413-a25d61cf7c7c" data-file-name="app/page.tsx"><span className="editable-text" data-unique-id="3fb25fba-700d-48f4-b8d4-0d81c5b1055e" data-file-name="app/page.tsx">Ctrl</span></span>
                        </div>
                        {/* Press indicator */}
                        <motion.div initial={{
                        opacity: 0.3
                      }} animate={{
                        opacity: 0.7
                      }} transition={{
                        repeat: Infinity,
                        repeatType: "reverse",
                        duration: 1.2,
                        delay: 0.3
                      }} className="absolute -bottom-3 left-0 right-0 mx-auto w-32 h-1 bg-primary rounded-full" data-unique-id="73ce6a0b-cdda-4205-a7af-326927c24fc2" data-file-name="app/page.tsx" />
                      </motion.div>

                      {/* Tap Indicators - Circular ripples */}
                      <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 pointer-events-none" data-unique-id="33bc3aef-54af-4f6c-be05-74f7206f25a6" data-file-name="app/page.tsx">
                        <motion.div initial={{
                        scale: 0,
                        opacity: 0.7
                      }} animate={{
                        scale: 2,
                        opacity: 0
                      }} transition={{
                        repeat: Infinity,
                        duration: 1.2,
                        delay: 0.1
                      }} className="w-40 h-40 rounded-full border border-primary/30 absolute top-0 left-0" data-unique-id="b97098c2-ca32-4ae7-8334-96e2a85535ab" data-file-name="app/page.tsx" />
                        <motion.div initial={{
                        scale: 0,
                        opacity: 0.7
                      }} animate={{
                        scale: 2,
                        opacity: 0
                      }} transition={{
                        repeat: Infinity,
                        duration: 1.2,
                        delay: 0.6
                      }} className="w-40 h-40 rounded-full border border-primary/30 absolute top-0 left-0" data-unique-id="248178a5-1243-4e2c-97d7-c91a70a6734a" data-file-name="app/page.tsx" />
                      </div>
                    </div>
                    
                    {/* Double-Press Indicator */}
                    <motion.div initial={{
                    opacity: 0
                  }} animate={{
                    opacity: 1
                  }} transition={{
                    repeat: Infinity,
                    repeatType: "reverse",
                    duration: 1.2
                  }} className="absolute bottom-10 flex items-center gap-2" data-unique-id="7389ff43-979d-40f6-acff-58c1c486d950" data-file-name="app/page.tsx">
                      <div className="w-2 h-2 bg-primary rounded-full" data-unique-id="4c9650e0-c721-43c1-9030-0b46a339fa65" data-file-name="app/page.tsx"></div>
                      <div className="w-2 h-2 bg-primary rounded-full" data-unique-id="03866187-668f-49b2-bd66-a11dd9ce4ba7" data-file-name="app/page.tsx"></div>
                    </motion.div>
                  </div>
                </div>
                <div className="absolute -z-10 -bottom-6 -right-6 h-32 w-32 sm:h-48 sm:w-48 md:h-64 md:w-64 bg-primary/20 rounded-full blur-3xl" data-unique-id="8c3d1bd4-d4c5-42f9-9823-91d803f7571b" data-file-name="app/page.tsx"></div>
              </motion.div>
            </div>
          </div>
        </div>
      </section>

      {/* Problem Statement */}
      <section id="problem-statement" className="py-10 sm:py-16 px-4 sm:px-6" data-unique-id="6a583f19-9e7f-4c61-a481-928cce2547e6" data-file-name="app/page.tsx">
        <div className="max-w-7xl mx-auto" data-unique-id="802249aa-73cb-4aa6-b4f7-6594531f5716" data-file-name="app/page.tsx">
          <FadeInSection>
            <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold text-center mb-8 sm:mb-12" data-unique-id="3291bc42-820f-43b2-ad8d-f05669379b81" data-file-name="app/page.tsx"><span className="editable-text" data-unique-id="d11361f4-543d-48e9-9058-a6d48192c316" data-file-name="app/page.tsx">
              Voice Dictation on Linux </span><span className="text-primary" data-unique-id="7f0091a3-70ff-4175-aaee-ad9524eb1c92" data-file-name="app/page.tsx"><span className="editable-text" data-unique-id="2278edc4-4540-4871-a0bd-7cb04e3498a6" data-file-name="app/page.tsx">Finally Solved</span></span>
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 md:gap-10 items-start" data-unique-id="75bc5ccd-07d5-40e4-b0b5-852e5498f89e" data-file-name="app/page.tsx">
              <div className="bg-background/50 p-5 rounded-lg shadow-sm" data-unique-id="27acc0db-a970-403d-979e-0521447b1699" data-file-name="app/page.tsx">
                <h3 className="text-xl sm:text-2xl font-semibold mb-3 sm:mb-4" data-unique-id="a688b274-4e5c-4a9f-8014-f68207578ead" data-file-name="app/page.tsx"><span className="editable-text" data-unique-id="0b0dadc4-650c-455f-9dce-c81edd3ae8e3" data-file-name="app/page.tsx">The Linux Voice Gap</span></h3>
                <p className="text-muted-foreground mb-4 sm:mb-6 text-sm sm:text-base" data-unique-id="6db34509-9743-4632-a4fc-4081642d6c44" data-file-name="app/page.tsx"><span className="editable-text" data-unique-id="a225ecc7-b17f-4366-b493-f4d66eb111e6" data-file-name="app/page.tsx">
                  While macOS and Windows offer built-in voice dictation capabilities, Linux users have been left without a comprehensive, privacy-focused solution—until now.
                </span></p>
                <ul className="space-y-2 sm:space-y-3" data-unique-id="d4259205-0791-4f60-9254-e8ec2d2583e2" data-file-name="app/page.tsx" data-dynamic-text="true">
                  {["Cloud services compromise privacy and require constant internet", "Existing solutions lack system-wide integration", "Poor performance with specialized Linux terminology", "Complicated setup processes for casual users"].map((item, i) => <li key={i} className="flex items-start gap-2 sm:gap-3 text-sm sm:text-base" data-is-mapped="true" data-unique-id="2736eb23-4188-4340-ab03-f37abcfbb408" data-file-name="app/page.tsx">
                      <div className="mt-0.5 sm:mt-1 bg-red-100 dark:bg-red-900/30 p-1 rounded" data-is-mapped="true" data-unique-id="8454b8c8-af54-468c-8aae-704b52ff563d" data-file-name="app/page.tsx">
                        <CheckCircle2 className="h-3 w-3 sm:h-4 sm:w-4 text-red-600 dark:text-red-400" data-unique-id="13eddb95-28ac-473a-b3c3-76b7e595e892" data-file-name="app/page.tsx" data-dynamic-text="true" />
                      </div>
                      <span data-is-mapped="true" data-unique-id="452824d0-1295-4c89-9908-cb822c1e1433" data-file-name="app/page.tsx" data-dynamic-text="true">{item}</span>
                    </li>)}
                </ul>
              </div>
              <div className="bg-background/50 p-5 rounded-lg shadow-sm" data-unique-id="a41eb1e1-67f1-42ac-a334-13543ce89c99" data-file-name="app/page.tsx">
                <h3 className="text-xl sm:text-2xl font-semibold mb-3 sm:mb-4" data-unique-id="25386fcd-9720-4c69-adb6-6064a3b1c686" data-file-name="app/page.tsx"><span className="editable-text" data-unique-id="a4df7eb3-a359-42a4-a6c0-fbed5286aa03" data-file-name="app/page.tsx">The Vocalinux Solution</span></h3>
                <p className="text-muted-foreground mb-4 sm:mb-6 text-sm sm:text-base" data-unique-id="b87c452a-ff29-43c5-a1e8-16da1829230a" data-file-name="app/page.tsx"><span className="editable-text" data-unique-id="2ed9a341-51a9-4679-83ca-3661936558df" data-file-name="app/page.tsx">
                  Vocalinux bridges this gap with a comprehensive voice dictation system built specifically for the Linux ecosystem.
                </span></p>
                <ul className="space-y-2 sm:space-y-3" data-unique-id="50ace9bc-f81e-405d-951c-6b0102934f9c" data-file-name="app/page.tsx" data-dynamic-text="true">
                  {["100% offline processing protects your privacy", "Universal application support across Linux environments", "Simple, global activation with keyboard shortcut", "Works with both X11 and Wayland display servers"].map((item, i) => <li key={i} className="flex items-start gap-2 sm:gap-3 text-sm sm:text-base" data-is-mapped="true" data-unique-id="0b28f32a-0ed7-419d-917f-24a5e07a1ed3" data-file-name="app/page.tsx">
                      <div className="mt-0.5 sm:mt-1 bg-green-100 dark:bg-green-900/30 p-1 rounded" data-is-mapped="true" data-unique-id="a614e1ac-668b-44e0-8b2b-acdba073cad8" data-file-name="app/page.tsx">
                        <CheckCircle2 className="h-3 w-3 sm:h-4 sm:w-4 text-green-600 dark:text-green-400" data-unique-id="1df13264-acbe-482c-892e-637672655014" data-file-name="app/page.tsx" data-dynamic-text="true" />
                      </div>
                      <span data-is-mapped="true" data-unique-id="651696c3-b469-47d6-858a-152fac35e0dd" data-file-name="app/page.tsx" data-dynamic-text="true">{item}</span>
                    </li>)}
                </ul>
              </div>
            </div>
          </FadeInSection>
        </div>
      </section>

      {/* Features */}
      <section id="features-section" className="py-10 sm:py-16 px-4 sm:px-6 bg-white dark:bg-zinc-800/50" data-unique-id="42ef7b71-60cd-4fcd-b9a2-3d29c712a047" data-file-name="app/page.tsx">
        <div className="max-w-7xl mx-auto" data-unique-id="bad4ca17-3adc-4ae9-a465-0f91c29152e5" data-file-name="app/page.tsx">
          <FadeInSection>
            <div className="text-center mb-10 sm:mb-16" data-unique-id="f3dd3ce3-8b6d-4361-a11b-ddc77892df11" data-file-name="app/page.tsx">
              <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold mb-2 sm:mb-4" data-unique-id="9e13e2c4-01ab-44d8-9aeb-ccf2c8e3ee75" data-file-name="app/page.tsx"><span className="editable-text" data-unique-id="a965c5a0-0db4-4fd3-89cf-f00774c8ac54" data-file-name="app/page.tsx">Powerful Features</span></h2>
              <p className="text-base sm:text-lg md:text-xl text-muted-foreground max-w-3xl mx-auto px-4" data-unique-id="de107aa5-54f6-4bfd-a609-58c3614864dd" data-file-name="app/page.tsx"><span className="editable-text" data-unique-id="0231a449-8e7d-4fdd-9026-8ca4598d97b9" data-file-name="app/page.tsx">
                Vocalinux combines privacy, performance, and flexibility to provide a seamless voice dictation experience on Linux.
              </span></p>
            </div>
          </FadeInSection>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6 md:gap-8" data-unique-id="10d2a8b2-63a6-4508-9d7b-11498d8b34c0" data-file-name="app/page.tsx">
            <FeatureCard icon={<Lock className="h-5 w-5 sm:h-6 sm:w-6 text-primary" />} title="Offline & Private" description="Runs completely offline using Whisper models - your voice data never leaves your computer." />
            <FeatureCard icon={<Laptop className="h-5 w-5 sm:h-6 sm:w-6 text-primary" />} title="Universal Support" description="Works with all Linux applications - from terminals to browsers to office suites." />
            <FeatureCard icon={<Zap className="h-5 w-5 sm:h-6 sm:w-6 text-primary" />} title="Blazing Fast" description="Uses optimized local models for real-time transcription with minimal latency." />
            <FeatureCard icon={<Keyboard className="h-5 w-5 sm:h-6 sm:w-6 text-primary" />} title="Global Shortcut" description="Activate from anywhere with a keyboard shortcut (default: Ctrl+Alt+Shift+V)." />
            <FeatureCard icon={<Terminal className="h-5 w-5 sm:h-6 sm:w-6 text-primary" />} title="X11 & Wayland" description="Compatible with both X11 and Wayland display servers out of the box." />
            <FeatureCard icon={<Settings className="h-5 w-5 sm:h-6 sm:w-6 text-primary" />} title="Configurable" description="Choose model size, language, activation method, and other settings via config file." />
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-10 sm:py-16 px-4 sm:px-6" id="how-it-works" data-unique-id="95264468-fc14-408f-828e-ecc8921c7378" data-file-name="app/page.tsx">
        <div className="max-w-7xl mx-auto" data-unique-id="cd126436-eba2-4273-99e3-9adcbb83cdb8" data-file-name="app/page.tsx">
          <FadeInSection>
            <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold text-center mb-10 sm:mb-16" data-unique-id="081b97c9-fc7a-4985-bee6-78f45ba30ae5" data-file-name="app/page.tsx"><span className="editable-text" data-unique-id="5d1da64d-4eab-4474-96c9-91c549a04886" data-file-name="app/page.tsx">How Vocalinux Works</span></h2>
          </FadeInSection>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6 md:gap-8" data-unique-id="28467223-46ea-4d64-a167-4c31ee41b281" data-file-name="app/page.tsx" data-dynamic-text="true">
            {[{
            step: "01",
            title: "Installation",
            description: "Install Vocalinux with our simple setup script that handles dependencies and configuration automatically.",
            icon: <Download className="h-6 w-6 sm:h-8 sm:w-8 text-primary" data-unique-id="9764ca70-c93a-44c1-806d-04be558b4e5a" data-file-name="app/page.tsx" data-dynamic-text="true" />
          }, {
            step: "02",
            title: "Activation",
            description: "Double-tap the Ctrl key (or your custom shortcut) to start dictating in any application.",
            icon: <Keyboard className="h-6 w-6 sm:h-8 sm:w-8 text-primary" data-unique-id="922f81c8-a02f-481e-864b-bfb14ee8e5ad" data-file-name="app/page.tsx" data-dynamic-text="true" />
          }, {
            step: "03",
            title: "Dictation",
            description: "Speak naturally, including voice commands for punctuation and formatting.",
            icon: <Mic className="h-6 w-6 sm:h-8 sm:w-8 text-primary" data-unique-id="0222e2a3-c435-44c6-b6dc-45df1f5c8f3d" data-file-name="app/page.tsx" data-dynamic-text="true" />
          }].map((item, index) => <FadeInSection key={index} delay={index * 0.1} data-unique-id="bad9aeaf-5687-4cfb-9aec-a4054bafa39d" data-file-name="app/page.tsx" data-dynamic-text="true">
                <div className="bg-white dark:bg-zinc-800 rounded-xl p-4 sm:p-6 shadow-md h-full" data-is-mapped="true" data-unique-id="404c05f0-d564-439d-9a7c-e50391b2eef3" data-file-name="app/page.tsx">
                  <div className="flex items-center gap-3 sm:gap-4 mb-4 sm:mb-6" data-is-mapped="true" data-unique-id="4b2c80da-1d76-4d1d-a465-bc9ac072c337" data-file-name="app/page.tsx">
                    <div className="bg-primary/10 h-10 w-10 sm:h-12 sm:w-12 rounded-full flex items-center justify-center" data-is-mapped="true" data-unique-id="ff772e1e-7d05-4202-95cc-0a7479af94b9" data-file-name="app/page.tsx" data-dynamic-text="true">
                      {item.icon}
                    </div>
                    <span className="text-2xl sm:text-4xl font-bold text-primary/20" data-is-mapped="true" data-unique-id="1fe70d54-7d45-45f9-b4fe-f32b314d3b2e" data-file-name="app/page.tsx" data-dynamic-text="true">{item.step}</span>
                  </div>
                  <h3 className="text-lg sm:text-xl font-semibold mb-2 sm:mb-3" data-is-mapped="true" data-unique-id="1515081b-6072-497f-83b4-9446faa42936" data-file-name="app/page.tsx" data-dynamic-text="true">{item.title}</h3>
                  <p className="text-sm sm:text-base text-muted-foreground" data-is-mapped="true" data-unique-id="6500cb7e-8637-44cf-a2a6-f583e065e96e" data-file-name="app/page.tsx" data-dynamic-text="true">{item.description}</p>
                </div>
              </FadeInSection>)}
          </div>
        </div>
      </section>

      {/* Demo */}
      <section id="demo-section" className="py-10 sm:py-16 px-4 sm:px-6 bg-white dark:bg-zinc-800/50" data-unique-id="486ac47c-fe1f-4a68-b252-8d188951f031" data-file-name="app/page.tsx">
        <div className="max-w-7xl mx-auto" data-unique-id="3197da12-efd7-49cb-8231-73cb1bbd44db" data-file-name="app/page.tsx">
          <FadeInSection>
            <div className="text-center mb-8 sm:mb-12" data-unique-id="0401aaf2-591a-4896-ab1c-61cd42cd8b32" data-file-name="app/page.tsx">
              <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold mb-2 sm:mb-4" data-unique-id="210cf2f6-8a63-49d1-96af-b2ec7f0ff12e" data-file-name="app/page.tsx"><span className="editable-text" data-unique-id="52ffd3d6-42a9-4fb9-931c-a141aeb16d4a" data-file-name="app/page.tsx">See Vocalinux in Action</span></h2>
              <p className="text-base sm:text-lg md:text-xl text-muted-foreground max-w-3xl mx-auto px-4" data-unique-id="98b40c06-1d98-4223-b897-1c4d2f44a49d" data-file-name="app/page.tsx"><span className="editable-text" data-unique-id="02cbb26b-8265-474d-a9e4-010df6724343" data-file-name="app/page.tsx">
                Watch how Vocalinux transforms the way you interact with your Linux system.
              </span></p>
            </div>
          </FadeInSection>

          <FadeInSection delay={0.2}>
            <div className="relative aspect-video rounded-lg sm:rounded-xl overflow-hidden shadow-xl sm:shadow-2xl mx-auto max-w-4xl" data-unique-id="e9b481c6-0593-48bf-8968-f79b2c0b02b7" data-file-name="app/page.tsx">
              <video className="w-full h-full object-cover" controls poster="https://images.unsplash.com/photo-1629654297299-c8506221ca97?q=80&w=1000&auto=format&fit=crop" preload="none" data-unique-id="552a28ae-5b2a-4365-b9a4-db5fa96a4b83" data-file-name="app/page.tsx">
                <source src="https://sample-videos.com/video321/mp4/720/big_buck_bunny_720p_1mb.mp4" type="video/mp4" data-unique-id="4e3c43b5-4f60-4baa-8f8e-d15baba708b9" data-file-name="app/page.tsx" /><span className="editable-text" data-unique-id="2de9d0ef-9cc4-42e8-ab5f-4868263c0455" data-file-name="app/page.tsx">
                Your browser does not support the video tag.
              </span></video>
              <div className="absolute inset-0 flex items-center justify-center pointer-events-none" data-unique-id="20ad9eac-90d3-4d62-865d-5b5133a6326b" data-file-name="app/page.tsx">
                <div className="bg-black/50 p-3 sm:p-5 rounded-full" data-unique-id="d0bcd9cd-e5bf-4821-9809-9811f0ca4653" data-file-name="app/page.tsx">
                  <svg xmlns="http://www.w3.org/2000/svg" fill="white" viewBox="0 0 24 24" strokeWidth={1.5} stroke="white" className="w-8 h-8 sm:w-12 sm:h-12" data-unique-id="9698e523-8a54-4aea-a424-81c60184f12c" data-file-name="app/page.tsx">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5.25 5.653c0-.856.917-1.398 1.667-.986l11.54 6.348a1.125 1.125 0 010 1.971l-11.54 6.347a1.125 1.125 0 01-1.667-.986V5.653z" />
                  </svg>
                </div>
              </div>
            </div>
          </FadeInSection>
        </div>
      </section>

      {/* Installation */}
      <section className="py-10 sm:py-16 px-4 sm:px-6" id="installation" data-unique-id="eff7c869-f396-46ad-a2b3-55ae10c2272e" data-file-name="app/page.tsx">
        <div className="max-w-7xl mx-auto" data-unique-id="be39c309-3894-45b2-ad0d-164c55c11619" data-file-name="app/page.tsx">
          <FadeInSection>
            <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold text-center mb-8 sm:mb-12" data-unique-id="eec5fd53-849a-4894-8686-08166abd1e71" data-file-name="app/page.tsx"><span className="editable-text" data-unique-id="8d89e659-aef5-4007-9de0-1186410fef8f" data-file-name="app/page.tsx">Installation Guide</span></h2>
          </FadeInSection>

          <FadeInSection delay={0.1}>
            <div className="bg-white dark:bg-zinc-800 rounded-xl shadow-lg overflow-hidden max-w-4xl mx-auto" data-unique-id="8167ce01-b205-4751-bdad-0c95e350d085" data-file-name="app/page.tsx">
              <div className="p-4 sm:p-6 md:p-10" data-unique-id="03067182-afbe-4621-887b-f78b4db4219e" data-file-name="app/page.tsx">
                <h3 className="text-xl sm:text-2xl font-semibold mb-4 sm:mb-6" data-unique-id="5d9f970d-9e3e-455b-9bec-d80d417352e2" data-file-name="app/page.tsx"><span className="editable-text" data-unique-id="2931905a-e33f-4240-b4b4-6dabb2e07a77" data-file-name="app/page.tsx">Quick Install</span></h3>
                <div className="relative" data-unique-id="5975ffcf-e2ec-4798-8421-012a31769780" data-file-name="app/page.tsx">
                  <SyntaxHighlighter language="bash" style={atomOneDark} className="rounded-lg text-xs sm:text-sm md:text-base overflow-x-auto" wrapLines={true}>
                    {installCommand}
                  </SyntaxHighlighter>
                  <CopyToClipboard text={installCommand} />
                </div>
                
                <h3 className="text-xl sm:text-2xl font-semibold mt-8 sm:mt-12 mb-4 sm:mb-6" data-unique-id="36c9d420-28d8-4058-b3c7-e6795f129c0a" data-file-name="app/page.tsx"><span className="editable-text" data-unique-id="f15161e5-7dd9-4f9b-a3f1-51c6d4ceccab" data-file-name="app/page.tsx">Manual Setup</span></h3>
                <ol className="space-y-4 sm:space-y-6" data-unique-id="aa0c0882-b624-4cd8-afc4-a7b10eba7357" data-file-name="app/page.tsx">
                  <li className="flex flex-col sm:flex-row gap-3 sm:gap-4" data-unique-id="6fcf942c-2818-4a4e-8220-10ec3d495bfa" data-file-name="app/page.tsx">
                    <div className="bg-primary/10 h-7 w-7 sm:h-8 sm:w-8 rounded-full flex items-center justify-center flex-shrink-0 mt-0 sm:mt-1" data-unique-id="56eed138-a960-4b77-a1d8-90358dfc3279" data-file-name="app/page.tsx">
                      <span className="font-semibold text-sm sm:text-base" data-unique-id="5b7b090c-0bb0-49d1-a7a5-778fc4e79aeb" data-file-name="app/page.tsx"><span className="editable-text" data-unique-id="0d9a3af2-9008-4fea-a12f-1b19c88dec4a" data-file-name="app/page.tsx">1</span></span>
                    </div>
                    <div className="flex-1" data-unique-id="6d9c873e-6c44-49ee-8278-bf2275127dff" data-file-name="app/page.tsx">
                      <h4 className="font-semibold text-base sm:text-lg mb-1 sm:mb-2" data-unique-id="ed032f36-3f4c-4549-a04c-e0fe27ce2558" data-file-name="app/page.tsx"><span className="editable-text" data-unique-id="397813c2-e45c-4c35-a2e6-0594c7ad2432" data-file-name="app/page.tsx">Install Dependencies</span></h4>
                      <p className="text-sm sm:text-base text-muted-foreground mb-2 sm:mb-3" data-unique-id="2db48257-2203-40ec-aab9-bca82fb4ab82" data-file-name="app/page.tsx"><span className="editable-text" data-unique-id="7fa14e70-e3c8-4c18-b954-57875ea6151a" data-file-name="app/page.tsx">
                        Ensure you have the necessary dependencies installed:
                      </span></p>
                      <div className="relative" data-unique-id="6db31a7b-97e4-4820-a129-ef4804b3fa12" data-file-name="app/page.tsx">
                        <SyntaxHighlighter language="bash" style={atomOneDark} className="rounded-lg text-xs sm:text-sm overflow-x-auto">
                          {"sudo apt install python3-pip portaudio19-dev python3-pyaudio git"}
                        </SyntaxHighlighter>
                        <CopyToClipboard text="sudo apt install python3-pip portaudio19-dev python3-pyaudio git" />
                      </div>
                    </div>
                  </li>
                  
                  <li className="flex flex-col sm:flex-row gap-3 sm:gap-4" data-unique-id="a536800b-6b09-461a-b67d-a64dc4ad0a3a" data-file-name="app/page.tsx">
                    <div className="bg-primary/10 h-7 w-7 sm:h-8 sm:w-8 rounded-full flex items-center justify-center flex-shrink-0 mt-0 sm:mt-1" data-unique-id="1f70a651-5f60-4691-8f25-9412a75b7c3f" data-file-name="app/page.tsx">
                      <span className="font-semibold text-sm sm:text-base" data-unique-id="c3046b9a-4d1c-4871-8cb1-0e0d136ee0ee" data-file-name="app/page.tsx"><span className="editable-text" data-unique-id="2db4adc9-1847-4087-a22b-25f3824a71bd" data-file-name="app/page.tsx">2</span></span>
                    </div>
                    <div className="flex-1" data-unique-id="b8ee40c3-e78f-472c-90bc-fb8e902afea4" data-file-name="app/page.tsx">
                      <h4 className="font-semibold text-base sm:text-lg mb-1 sm:mb-2" data-unique-id="19003fdf-7c23-4972-ae01-82e5e2a8e643" data-file-name="app/page.tsx"><span className="editable-text" data-unique-id="bdac8e57-67d4-4b7f-af27-305c6386b338" data-file-name="app/page.tsx">Clone Repository</span></h4>
                      <p className="text-sm sm:text-base text-muted-foreground mb-2 sm:mb-3" data-unique-id="ae90c417-d72f-49d0-80e6-c0c357f76907" data-file-name="app/page.tsx"><span className="editable-text" data-unique-id="951654ed-3829-437e-80eb-e61dc6090659" data-file-name="app/page.tsx">
                        Clone the Vocalinux repository to your local machine:
                      </span></p>
                      <div className="relative" data-unique-id="54713c4d-defe-4e47-a7af-ee87faafcb0d" data-file-name="app/page.tsx">
                        <SyntaxHighlighter language="bash" style={atomOneDark} className="rounded-lg text-xs sm:text-sm overflow-x-auto">
                          {"git clone https://github.com/jatinkrmalik/vocalinux.git\ncd vocalinux"}
                        </SyntaxHighlighter>
                        <CopyToClipboard text="git clone https://github.com/jatinkrmalik/vocalinux.git\ncd vocalinux" />
                      </div>
                    </div>
                  </li>
                  
                  <li className="flex flex-col sm:flex-row gap-3 sm:gap-4" data-unique-id="4ebd1fee-1920-49c4-ba03-5661cff6a129" data-file-name="app/page.tsx">
                    <div className="bg-primary/10 h-7 w-7 sm:h-8 sm:w-8 rounded-full flex items-center justify-center flex-shrink-0 mt-0 sm:mt-1" data-unique-id="d3721b30-3866-42b8-855e-5b088bbf0895" data-file-name="app/page.tsx">
                      <span className="font-semibold text-sm sm:text-base" data-unique-id="d9cb5e08-ddd0-46b8-a9c3-0aaee0e41e5a" data-file-name="app/page.tsx"><span className="editable-text" data-unique-id="9d3a207f-99d7-4e16-9532-054c0aec6e2e" data-file-name="app/page.tsx">3</span></span>
                    </div>
                    <div className="flex-1" data-unique-id="34c74ac0-a1f6-4107-8454-e10e88e4598c" data-file-name="app/page.tsx">
                      <h4 className="font-semibold text-base sm:text-lg mb-1 sm:mb-2" data-unique-id="758aeacc-b393-418d-8b42-1c54f3d6d026" data-file-name="app/page.tsx"><span className="editable-text" data-unique-id="cc0f45cb-1447-4ea1-8d8c-9f67e72ee8d6" data-file-name="app/page.tsx">Install Python Requirements</span></h4>
                      <p className="text-sm sm:text-base text-muted-foreground mb-2 sm:mb-3" data-unique-id="251977ba-1d1c-41d4-b3f7-b2a27109a004" data-file-name="app/page.tsx"><span className="editable-text" data-unique-id="91d55bda-6607-47c2-9e04-7b099588010f" data-file-name="app/page.tsx">
                        Install the required Python packages:
                      </span></p>
                      <div className="relative" data-unique-id="12eaeeec-4c7c-4d72-b08d-a75768eea22c" data-file-name="app/page.tsx">
                        <SyntaxHighlighter language="bash" style={atomOneDark} className="rounded-lg text-xs sm:text-sm overflow-x-auto">
                          {"pip install -r requirements.txt"}
                        </SyntaxHighlighter>
                        <CopyToClipboard text="pip install -r requirements.txt" />
                      </div>
                    </div>
                  </li>
                  
                  <li className="flex flex-col sm:flex-row gap-3 sm:gap-4" data-unique-id="04931ba3-4fc8-410d-a557-f62273dd4d50" data-file-name="app/page.tsx">
                    <div className="bg-primary/10 h-7 w-7 sm:h-8 sm:w-8 rounded-full flex items-center justify-center flex-shrink-0 mt-0 sm:mt-1" data-unique-id="ed0805da-3baa-43d5-a249-356860433b4e" data-file-name="app/page.tsx">
                      <span className="font-semibold text-sm sm:text-base" data-unique-id="8a2cfffb-2c46-480f-a343-577a28defce3" data-file-name="app/page.tsx"><span className="editable-text" data-unique-id="38aa0c5f-0e26-49e8-ab94-90ef78f89d36" data-file-name="app/page.tsx">4</span></span>
                    </div>
                    <div className="flex-1" data-unique-id="d52c5e18-6625-4c2f-aae2-625033fbdd7c" data-file-name="app/page.tsx">
                      <h4 className="font-semibold text-base sm:text-lg mb-1 sm:mb-2" data-unique-id="c4d232bb-3b78-4cce-a3bf-011b92206138" data-file-name="app/page.tsx"><span className="editable-text" data-unique-id="bd904443-a2dd-47c8-8451-18301c97a930" data-file-name="app/page.tsx">Install Vocalinux</span></h4>
                      <p className="text-sm sm:text-base text-muted-foreground mb-2 sm:mb-3" data-unique-id="7c5f7d28-6bcc-4402-9b55-da5cfa2aa6f3" data-file-name="app/page.tsx"><span className="editable-text" data-unique-id="c8530011-bd33-4ca1-af3d-9684d41e74df" data-file-name="app/page.tsx">
                        Install Vocalinux on your system:
                      </span></p>
                      <div className="relative" data-unique-id="6905313b-3c7c-45e8-8ab3-f483a9fd7c25" data-file-name="app/page.tsx">
                        <SyntaxHighlighter language="bash" style={atomOneDark} className="rounded-lg text-xs sm:text-sm overflow-x-auto">
                          {"python cli.py install"}
                        </SyntaxHighlighter>
                        <CopyToClipboard text="python cli.py install" />
                      </div>
                    </div>
                  </li>
                  
                  <li className="flex flex-col sm:flex-row gap-3 sm:gap-4" data-unique-id="3a7d37cc-12c6-4092-9b99-c8af4b12a562" data-file-name="app/page.tsx">
                    <div className="bg-primary/10 h-7 w-7 sm:h-8 sm:w-8 rounded-full flex items-center justify-center flex-shrink-0 mt-0 sm:mt-1" data-unique-id="eb22d5a5-0bbf-47e5-9330-5a2376072762" data-file-name="app/page.tsx">
                      <span className="font-semibold text-sm sm:text-base" data-unique-id="12be647c-51c5-43aa-b977-c623792f1276" data-file-name="app/page.tsx"><span className="editable-text" data-unique-id="981fedde-9269-4a61-8d50-4351a6a5ff88" data-file-name="app/page.tsx">5</span></span>
                    </div>
                    <div className="flex-1" data-unique-id="d555acb1-8207-4716-99f9-8df50ee3263f" data-file-name="app/page.tsx">
                      <h4 className="font-semibold text-base sm:text-lg mb-1 sm:mb-2" data-unique-id="328e58cf-dd92-4bee-aa61-7b5d4872e598" data-file-name="app/page.tsx"><span className="editable-text" data-unique-id="0038d6e0-61bc-41ac-909e-95fe40916774" data-file-name="app/page.tsx">Start Using Vocalinux</span></h4>
                      <p className="text-sm sm:text-base text-muted-foreground mb-2 sm:mb-3" data-unique-id="31e7dbca-092d-4af2-943f-6aafc8605139" data-file-name="app/page.tsx"><span className="editable-text" data-unique-id="3ac5eced-74ea-4d90-888e-e037043cc2d6" data-file-name="app/page.tsx">
                        Launch Vocalinux and begin dictating with the default keyboard shortcut (Ctrl+Alt+Shift+V) or customize it in the config file.
                      </span></p>
                      <div className="relative" data-unique-id="38ecffda-6e7b-4904-a874-9769c6010c44" data-file-name="app/page.tsx">
                        <SyntaxHighlighter language="bash" style={atomOneDark} className="rounded-lg text-xs sm:text-sm overflow-x-auto">
                          {"python cli.py start"}
                        </SyntaxHighlighter>
                        <CopyToClipboard text="python cli.py start" />
                      </div>
                    </div>
                  </li>
                </ol>
              </div>
            </div>
          </FadeInSection>
        </div>
      </section>

      {/* Voice Commands */}
      <section id="voice-commands" className="py-10 sm:py-16 px-4 sm:px-6 bg-white dark:bg-zinc-800/50" data-unique-id="a0a59f12-2b83-46e7-90bc-a68cb56a67b6" data-file-name="app/page.tsx">
        <div className="max-w-7xl mx-auto" data-unique-id="f045add1-857a-4c19-bea7-8878917d0232" data-file-name="app/page.tsx">
          <FadeInSection>
            <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold text-center mb-6 sm:mb-12" data-unique-id="76b3fe90-4807-4893-9508-182af4828f74" data-file-name="app/page.tsx"><span className="editable-text" data-unique-id="ca3d4d31-35b7-4698-97ee-b80f827549ce" data-file-name="app/page.tsx">Voice Commands</span></h2>
            <p className="text-base sm:text-lg md:text-xl text-muted-foreground text-center max-w-3xl mx-auto mb-8 sm:mb-12 px-4" data-unique-id="901ee2a3-434f-49af-bee0-7ef59d53caca" data-file-name="app/page.tsx"><span className="editable-text" data-unique-id="326b01ff-7e18-4931-af21-ccfa78015d04" data-file-name="app/page.tsx">
              Control your dictation experience with these built-in voice commands.
            </span></p>
          </FadeInSection>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 sm:gap-8 max-w-4xl mx-auto" data-unique-id="400acfc3-0de4-410e-8d3a-ee74ecc2a737" data-file-name="app/page.tsx">
            <FadeInSection delay={0.1}>
              <div className="bg-[#f9f9fb] dark:bg-zinc-900 rounded-xl p-4 sm:p-6 h-full" data-unique-id="56cc979e-4556-4d71-ad80-bcd1186ddcd9" data-file-name="app/page.tsx">
                <h3 className="text-lg sm:text-xl font-semibold mb-4 sm:mb-6 flex items-center" data-unique-id="6b0158de-1bf0-41ce-9e74-db68e72a1e8d" data-file-name="app/page.tsx">
                  <Edit className="h-4 w-4 sm:h-5 sm:w-5 text-primary mr-2" /><span className="editable-text" data-unique-id="b3eb3432-841c-461a-9070-01683df560bc" data-file-name="app/page.tsx">
                  Text Formatting
                </span></h3>
                <ul className="space-y-2 sm:space-y-4" data-unique-id="8e69bdcc-0641-493c-ba29-38a66fb21a97" data-file-name="app/page.tsx" data-dynamic-text="true">
                  {[{
                  command: "new line",
                  description: "Inserts a line break"
                }, {
                  command: "new paragraph",
                  description: "Inserts two line breaks"
                }, {
                  command: "period",
                  description: "Inserts a period (.)"
                }, {
                  command: "question mark",
                  description: "Inserts a question mark (?)"
                }, {
                  command: "exclamation mark",
                  description: "Inserts an exclamation mark (!)"
                }, {
                  command: "comma",
                  description: "Inserts a comma (,)"
                }, {
                  command: "colon",
                  description: "Inserts a colon (:)"
                }, {
                  command: "semicolon",
                  description: "Inserts a semicolon (;)"
                }, {
                  command: "hyphen",
                  description: "Inserts a hyphen (-)"
                }].map((item, i) => <li key={i} className="flex flex-col sm:flex-row sm:justify-between text-sm sm:text-base" data-is-mapped="true" data-unique-id="3fcda2cc-dcad-4b0e-b04d-e9198e4930fe" data-file-name="app/page.tsx">
                      <span className="font-medium" data-is-mapped="true" data-unique-id="8318bd0e-c16a-4523-9fe4-71482794abe3" data-file-name="app/page.tsx" data-dynamic-text="true">{item.command}</span>
                      <span className="text-muted-foreground" data-is-mapped="true" data-unique-id="eacb3e79-362f-4896-9776-920796669f78" data-file-name="app/page.tsx" data-dynamic-text="true">{item.description}</span>
                    </li>)}
                </ul>
              </div>
            </FadeInSection>

            <FadeInSection delay={0.2}>
              <div className="bg-[#f9f9fb] dark:bg-zinc-900 rounded-xl p-4 sm:p-6 h-full" data-unique-id="a4bd0d24-1dbb-42a1-a746-d12ccf784e5f" data-file-name="app/page.tsx">
                <h3 className="text-lg sm:text-xl font-semibold mb-4 sm:mb-6 flex items-center" data-unique-id="faf26125-81b8-4a92-9d11-0ee19abb1053" data-file-name="app/page.tsx">
                  <Edit className="h-4 w-4 sm:h-5 sm:w-5 text-primary mr-2" /><span className="editable-text" data-unique-id="369a8b74-a1c7-4a1a-9f9a-40a59d5d780c" data-file-name="app/page.tsx">
                  Editing Commands
                </span></h3>
                <ul className="space-y-2 sm:space-y-4" data-unique-id="6ba763d5-d483-48ad-a5d7-61e9fd762592" data-file-name="app/page.tsx" data-dynamic-text="true">
                  {[{
                  command: "backspace",
                  description: "Deletes the previous character"
                }, {
                  command: "delete that",
                  description: "Deletes the last phrase"
                }, {
                  command: "clear all",
                  description: "Clears all text"
                }, {
                  command: "select all",
                  description: "Selects all text"
                }, {
                  command: "copy",
                  description: "Copies selected text"
                }, {
                  command: "paste",
                  description: "Pastes from clipboard"
                }, {
                  command: "undo",
                  description: "Undoes last action"
                }, {
                  command: "redo",
                  description: "Redoes last action"
                }, {
                  command: "tab",
                  description: "Inserts a tab character"
                }].map((item, i) => <li key={i} className="flex flex-col sm:flex-row sm:justify-between text-sm sm:text-base" data-is-mapped="true" data-unique-id="eec142d3-8cc6-4ab0-b82c-2ee6552f26b9" data-file-name="app/page.tsx">
                      <span className="font-medium" data-is-mapped="true" data-unique-id="4a3d648d-bfb2-4ae7-bb70-7032b3666956" data-file-name="app/page.tsx" data-dynamic-text="true">{item.command}</span>
                      <span className="text-muted-foreground" data-is-mapped="true" data-unique-id="ea8a5870-cda0-439c-b3ef-9a88cf8f44c3" data-file-name="app/page.tsx" data-dynamic-text="true">{item.description}</span>
                    </li>)}
                </ul>
              </div>
            </FadeInSection>
          </div>
        </div>
      </section>

      {/* Customization Options */}
      <section id="customization" className="py-10 sm:py-16 px-4 sm:px-6" data-unique-id="b99b0c1e-0a62-4db9-9a4a-fb79c43885fc" data-file-name="app/page.tsx">
        <div className="max-w-7xl mx-auto" data-unique-id="2fd5cff1-173a-4a7e-8a9a-29788199b384" data-file-name="app/page.tsx">
          <FadeInSection>
            <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold text-center mb-8 sm:mb-12" data-unique-id="12e10c2b-e571-42b4-8fec-f68e3cadbe45" data-file-name="app/page.tsx"><span className="editable-text" data-unique-id="fceef222-6ba7-4f50-b60e-f84862d2ca91" data-file-name="app/page.tsx">Customization Options</span></h2>
          </FadeInSection>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 sm:gap-8 md:gap-12 items-center" data-unique-id="95153480-0bc4-44ce-b4aa-cdbdf3b2895d" data-file-name="app/page.tsx">
            <FadeInSection delay={0.1}>
              <div className="space-y-4 sm:space-y-6" data-unique-id="c8918e0d-cb2b-420f-bc35-f5efe54cee47" data-file-name="app/page.tsx">
                <div className="bg-white dark:bg-zinc-800 p-4 sm:p-6 rounded-xl shadow-md" data-unique-id="b3b57be6-cc90-4ceb-b149-8469c59e06bb" data-file-name="app/page.tsx">
                  <h3 className="text-lg sm:text-xl font-semibold mb-2 sm:mb-4" data-unique-id="5b2ae94c-b9e0-4c77-ac99-ed859e5cb98f" data-file-name="app/page.tsx"><span className="editable-text" data-unique-id="56015fc3-b8b0-451f-86ed-7a029c99ce9f" data-file-name="app/page.tsx">Whisper Models</span></h3>
                  <p className="text-sm sm:text-base text-muted-foreground mb-3 sm:mb-4" data-unique-id="c2e7a1ae-30b9-43bb-aba6-4a91568c5670" data-file-name="app/page.tsx"><span className="editable-text" data-unique-id="f46688ac-69ac-4b02-b214-bace3f3507b9" data-file-name="app/page.tsx">
                    Choose from different Whisper model sizes depending on your hardware and accuracy needs.
                  </span></p>
                  <div className="flex flex-wrap gap-2 sm:gap-3" data-unique-id="f73be6b2-5857-447e-b463-755f5800c0e2" data-file-name="app/page.tsx">
                    <div className="bg-primary/10 px-3 sm:px-4 py-1.5 sm:py-2 rounded-full text-xs sm:text-sm font-medium text-primary" data-unique-id="9f6df803-a9f7-4fc2-85e1-a54e78d1517d" data-file-name="app/page.tsx"><span className="editable-text" data-unique-id="9d2b472e-d3a6-4206-9386-51ab364cc2ac" data-file-name="app/page.tsx">Tiny (75MB)</span></div>
                    <div className="bg-primary/10 px-3 sm:px-4 py-1.5 sm:py-2 rounded-full text-xs sm:text-sm font-medium text-primary" data-unique-id="254021f4-415d-4c0d-9e20-60e279a98af1" data-file-name="app/page.tsx"><span className="editable-text" data-unique-id="fa0e6cf4-48a5-416d-90df-a1c841c0479e" data-file-name="app/page.tsx">Base (142MB)</span></div>
                    <div className="bg-primary/10 px-3 sm:px-4 py-1.5 sm:py-2 rounded-full text-xs sm:text-sm font-medium text-primary" data-unique-id="90119276-a20e-4f21-b2a4-2b52790d0a33" data-file-name="app/page.tsx"><span className="editable-text" data-unique-id="3bfffd25-fecd-4b83-bc50-b6cd280a7aad" data-file-name="app/page.tsx">Small (466MB)</span></div>
                    <div className="bg-primary/10 px-3 sm:px-4 py-1.5 sm:py-2 rounded-full text-xs sm:text-sm font-medium text-primary" data-unique-id="cb71a553-669f-441f-a7e4-ec752515b32f" data-file-name="app/page.tsx"><span className="editable-text" data-unique-id="931ffc86-9cd0-42c0-99ec-3028b526c550" data-file-name="app/page.tsx">Medium (1.5GB)</span></div>
                    <div className="bg-primary/10 px-3 sm:px-4 py-1.5 sm:py-2 rounded-full text-xs sm:text-sm font-medium text-primary" data-unique-id="f36f0ffd-8f6b-42a0-9fe1-6fc219ccef1e" data-file-name="app/page.tsx"><span className="editable-text" data-unique-id="5848c173-e012-40a6-a6d7-b471113d49eb" data-file-name="app/page.tsx">Large (3GB)</span></div>
                  </div>
                </div>
                
                <div className="bg-white dark:bg-zinc-800 p-4 sm:p-6 rounded-xl shadow-md" data-unique-id="91a454f4-7d65-4b53-9bc3-c3e118b36b8c" data-file-name="app/page.tsx">
                  <h3 className="text-lg sm:text-xl font-semibold mb-2 sm:mb-4" data-unique-id="e56251b3-de28-4c23-a820-58d12516fee8" data-file-name="app/page.tsx"><span className="editable-text" data-unique-id="df8b807e-ae57-4d8a-a350-09e111ec4296" data-file-name="app/page.tsx">Model Size & Language</span></h3>
                  <p className="text-sm sm:text-base text-muted-foreground mb-3 sm:mb-4" data-unique-id="770492aa-28c8-4803-9267-9199b725ab82" data-file-name="app/page.tsx"><span className="editable-text" data-unique-id="50fc97a9-f708-48fa-99a2-c20af8d9f53f" data-file-name="app/page.tsx">
                    Balance between accuracy and resource usage with different model sizes.
                  </span></p>
                  <div className="space-y-3 sm:space-y-4" data-unique-id="9f0b4dd7-c2ad-452e-9839-af4e84c5b950" data-file-name="app/page.tsx">
                    <div className="flex flex-wrap justify-between items-center text-sm sm:text-base" data-unique-id="9efc9deb-82d2-468a-b09f-a82c78f05a63" data-file-name="app/page.tsx">
                      <span data-unique-id="e4b66266-3ff4-479f-92df-9709e8ba68b7" data-file-name="app/page.tsx"><span className="editable-text" data-unique-id="fc88b2ea-ab26-4e89-8e2c-da38df655a5c" data-file-name="app/page.tsx">Small (150MB)</span></span>
                      <span className="text-muted-foreground" data-unique-id="7bd27783-ea77-4020-84fc-50c5bd7958c8" data-file-name="app/page.tsx"><span className="editable-text" data-unique-id="d9598049-1bcb-4dee-97ff-2f527a6f8db2" data-file-name="app/page.tsx">Lower resource usage</span></span>
                    </div>
                    <div className="flex flex-wrap justify-between items-center text-sm sm:text-base" data-unique-id="07684946-4f32-4d4a-9a7c-457e4b5d2d13" data-file-name="app/page.tsx">
                      <span data-unique-id="f687babc-c869-471c-a141-f430c7dfd709" data-file-name="app/page.tsx"><span className="editable-text" data-unique-id="13b18d7f-0d7d-42a8-b7e4-e30dc60f80f0" data-file-name="app/page.tsx">Medium (450MB)</span></span>
                      <span className="text-muted-foreground" data-unique-id="ecb683a3-ef5f-4621-be23-59d51326b103" data-file-name="app/page.tsx"><span className="editable-text" data-unique-id="724ebe12-8590-4fd1-9bb5-6a8ae54efc2e" data-file-name="app/page.tsx">Balanced performance</span></span>
                    </div>
                    <div className="flex flex-wrap justify-between items-center text-sm sm:text-base" data-unique-id="5587cc4e-7e55-4845-a6fd-53cf7d4678f0" data-file-name="app/page.tsx">
                      <span data-unique-id="656369b8-e2bb-4a9a-9b64-8a61505947bb" data-file-name="app/page.tsx"><span className="editable-text" data-unique-id="2aaa95f2-8f66-493a-93d5-d30153f7b354" data-file-name="app/page.tsx">Large (1.2GB)</span></span>
                      <span className="text-muted-foreground" data-unique-id="fffda5de-f94f-438b-92d3-b38c3c9aead1" data-file-name="app/page.tsx"><span className="editable-text" data-unique-id="ee0c30f3-4689-4fa7-95a2-bdf5b4b5e8a7" data-file-name="app/page.tsx">Highest accuracy</span></span>
                    </div>
                  </div>
                </div>
                
                <div className="bg-white dark:bg-zinc-800 p-4 sm:p-6 rounded-xl shadow-md" data-unique-id="e7d81679-57f8-4ce5-b92c-8b995581c4f8" data-file-name="app/page.tsx">
                  <h3 className="text-lg sm:text-xl font-semibold mb-2 sm:mb-4" data-unique-id="4d0e01d6-21ae-4fd7-9986-47e8b5ec64a6" data-file-name="app/page.tsx"><span className="editable-text" data-unique-id="1be60ba6-70bc-4f6e-8fe5-516f2bae3311" data-file-name="app/page.tsx">Custom Activation</span></h3>
                  <p className="text-sm sm:text-base text-muted-foreground" data-unique-id="8e7df2ba-8b78-42a2-95d2-15c648f1f79c" data-file-name="app/page.tsx"><span className="editable-text" data-unique-id="dfc1aaac-27a2-4ec4-a1dc-14bd9859834d" data-file-name="app/page.tsx">
                    Configure your own keyboard shortcuts or even voice activation phrases.
                  </span></p>
                </div>
              </div>
            </FadeInSection>
            
            <FadeInSection delay={0.2}>
              <div className="bg-white dark:bg-zinc-800 rounded-xl shadow-lg overflow-hidden" data-unique-id="5c7a08bf-dd93-46e8-aa96-2a514b41cdc8" data-file-name="app/page.tsx">
                <div className="bg-zinc-800 p-2 sm:p-3 flex items-center gap-2" data-unique-id="ea4364b7-ca98-4838-bcd4-af605eb3a9f8" data-file-name="app/page.tsx">
                  <div className="flex gap-1.5" data-unique-id="2d51368e-b91a-4741-a5fe-b4bd090ec1f7" data-file-name="app/page.tsx">
                    <div className="h-2 w-2 sm:h-3 sm:w-3 rounded-full bg-red-500" data-unique-id="165a5640-c7b1-4e99-be38-9276503be5af" data-file-name="app/page.tsx"></div>
                    <div className="h-2 w-2 sm:h-3 sm:w-3 rounded-full bg-yellow-500" data-unique-id="c77af577-fda7-437f-8726-a251be84e55d" data-file-name="app/page.tsx"></div>
                    <div className="h-2 w-2 sm:h-3 sm:w-3 rounded-full bg-green-500" data-unique-id="14f59e9d-5147-40a6-8767-691117204875" data-file-name="app/page.tsx"></div>
                  </div>
                  <div className="flex-1 text-center" data-unique-id="8216be05-1e92-4e01-b5f4-24f4429ffcd4" data-file-name="app/page.tsx">
                    <span className="text-[10px] sm:text-xs text-zinc-400" data-unique-id="490e12fb-f863-4309-ab26-c1fbc21df642" data-file-name="app/page.tsx"><span className="editable-text" data-unique-id="d7fc6e29-4e84-4976-8de6-dcbcf7c47f53" data-file-name="app/page.tsx">vocalinux-config.yaml</span></span>
                  </div>
                </div>
                <SyntaxHighlighter language="yaml" style={atomOneDark} className="p-3 sm:p-6 text-xs sm:text-sm overflow-x-auto" wrapLines={true} showLineNumbers={false}>
                  {"# Vocalinux Configuration File\n\n# Set this to 'true' if you want the app to start automatically\nauto_start: false\n\n# Default global shortcut to start/stop dictation \n# Uses the same format as the keyboard library\nshortcut: 'ctrl+alt+shift+v'\n\n# Model settings\nmodel:\n  # Options: tiny, base, small, medium, large\n  size: 'tiny'\n  \n  # Language code (determines the model downloaded)\n  language: 'en'\n\n# Thread settings\nthreads: 2\n\n# Audio settings\naudio:\n  # Pause detection to automatically stop recording after silence\n  pause_detection: true\n  # Seconds of silence to wait before stopping\n  pause_threshold: 2.0\n  \n# Notification settings\nnotifications: true"}
                </SyntaxHighlighter>
              </div>
            </FadeInSection>
          </div>
        </div>
      </section>

      {/* Community & Contribution */}
      <section id="community" className="py-10 sm:py-16 px-4 sm:px-6 bg-white dark:bg-zinc-800/50" data-unique-id="c0a6f7c6-b1a8-4776-8aea-3dd3385d84fe" data-file-name="app/page.tsx">
        <div className="max-w-7xl mx-auto" data-unique-id="0f2572a2-fd74-40ad-874a-f1ae9702404a" data-file-name="app/page.tsx">
          <FadeInSection>
            <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold text-center mb-3 sm:mb-6" data-unique-id="dd485b56-4560-44ad-a704-e7fd265934f8" data-file-name="app/page.tsx"><span className="editable-text" data-unique-id="c8d95ec0-3d04-4f9c-8cba-7e92e45fd41c" data-file-name="app/page.tsx">Join the Community</span></h2>
            <p className="text-base sm:text-lg md:text-xl text-muted-foreground text-center max-w-3xl mx-auto mb-8 sm:mb-16 px-4" data-unique-id="1afc8f63-1110-4a2f-aa4e-ae8097f787a9" data-file-name="app/page.tsx"><span className="editable-text" data-unique-id="d71f3510-2209-46c6-a2f9-31a475504dcc" data-file-name="app/page.tsx">
              Vocalinux is community-driven and welcomes contributors of all skill levels.
            </span></p>
          </FadeInSection>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-5 sm:gap-8" data-unique-id="e840e1c7-89bf-4f87-85a3-f214ad0e441f" data-file-name="app/page.tsx">
            <FadeInSection delay={0.1}>
              <div className="bg-[#f9f9fb] dark:bg-zinc-900 p-4 sm:p-6 rounded-xl h-full" data-unique-id="5eea1a75-c654-4bcb-bee9-f5e478b1db4d" data-file-name="app/page.tsx">
                <div className="h-10 w-10 sm:h-12 sm:w-12 bg-primary/10 rounded-full flex items-center justify-center mb-4 sm:mb-6" data-unique-id="0db3f551-65a7-4678-9707-06684594ba0c" data-file-name="app/page.tsx">
                  <Code className="h-5 w-5 sm:h-6 sm:w-6 text-primary" />
                </div>
                <h3 className="text-lg sm:text-xl font-semibold mb-2 sm:mb-4" data-unique-id="64e2b399-109c-476f-b270-d66afedab7c1" data-file-name="app/page.tsx"><span className="editable-text" data-unique-id="28015a22-81e3-40cc-8171-eab288aea2cf" data-file-name="app/page.tsx">Contribute Code</span></h3>
                <p className="text-sm sm:text-base text-muted-foreground mb-4 sm:mb-6" data-unique-id="b3d932ef-9a9e-450f-b264-36f1a3a58ba4" data-file-name="app/page.tsx"><span className="editable-text" data-unique-id="27dd3b2c-e01f-4ad2-8256-22bce59f51e9" data-file-name="app/page.tsx">
                  Help improve Vocalinux by contributing code, fixing bugs, or adding new features through pull requests.
                </span></p>
                <a href="https://github.com/jatinkrmalik/vocalinux/contribute" target="_blank" rel="noopener noreferrer" className="flex items-center text-primary font-medium hover:underline text-sm sm:text-base" data-unique-id="1e9cb66f-e2b4-4792-a3ae-28d23a788df4" data-file-name="app/page.tsx"><span className="editable-text" data-unique-id="a930ac77-88af-4ca0-ba7e-2ad4693b8aa1" data-file-name="app/page.tsx">
                  View GitHub Repository </span><ChevronRight className="h-3 w-3 sm:h-4 sm:w-4 ml-1" />
                </a>
              </div>
            </FadeInSection>

            <FadeInSection delay={0.2}>
              <div className="bg-[#f9f9fb] dark:bg-zinc-900 p-4 sm:p-6 rounded-xl h-full" data-unique-id="8c0de20c-7506-4285-a1dd-1d645dba0b46" data-file-name="app/page.tsx">
                <div className="h-10 w-10 sm:h-12 sm:w-12 bg-primary/10 rounded-full flex items-center justify-center mb-4 sm:mb-6" data-unique-id="e0951dad-8ab7-4fc8-9a15-af6b608aaa38" data-file-name="app/page.tsx">
                  <BookOpen className="h-5 w-5 sm:h-6 sm:w-6 text-primary" />
                </div>
                <h3 className="text-lg sm:text-xl font-semibold mb-2 sm:mb-4" data-unique-id="d94c9876-9107-43ad-b4d7-5c8b4dea77a0" data-file-name="app/page.tsx"><span className="editable-text" data-unique-id="daa8d08f-623e-42ed-8e31-974b3b9991e2" data-file-name="app/page.tsx">Improve Documentation</span></h3>
                <p className="text-sm sm:text-base text-muted-foreground mb-4 sm:mb-6" data-unique-id="c7ffc213-0e5e-49c9-b8a4-46c1ef7adf8b" data-file-name="app/page.tsx"><span className="editable-text" data-unique-id="efb3afb4-a8d5-473c-a2c9-5d646f08013d" data-file-name="app/page.tsx">
                  Help make Vocalinux more accessible by improving documentation, writing tutorials, or creating guides.
                </span></p>
                <a href="https://github.com/jatinkrmalik/vocalinux/wiki" target="_blank" rel="noopener noreferrer" className="flex items-center text-primary font-medium hover:underline text-sm sm:text-base" data-unique-id="8a2e2cf8-a06b-41b2-80e2-1a919c2d944c" data-file-name="app/page.tsx"><span className="editable-text" data-unique-id="077c1cd5-3027-48d3-b6b5-e6ae99a9e159" data-file-name="app/page.tsx">
                  View Documentation </span><ChevronRight className="h-3 w-3 sm:h-4 sm:w-4 ml-1" />
                </a>
              </div>
            </FadeInSection>

            <FadeInSection delay={0.3}>
              <div className="bg-[#f9f9fb] dark:bg-zinc-900 p-4 sm:p-6 rounded-xl h-full" data-unique-id="a0f7c496-0258-4317-b32d-e1e61d7ff299" data-file-name="app/page.tsx">
                <div className="h-10 w-10 sm:h-12 sm:w-12 bg-primary/10 rounded-full flex items-center justify-center mb-4 sm:mb-6" data-unique-id="0c262315-a266-441b-aa89-350d084675b7" data-file-name="app/page.tsx">
                  <MessageSquare className="h-5 w-5 sm:h-6 sm:w-6 text-primary" />
                </div>
                <h3 className="text-lg sm:text-xl font-semibold mb-2 sm:mb-4" data-unique-id="bcc8a0ad-c115-4274-ae3e-909c8f5a568d" data-file-name="app/page.tsx"><span className="editable-text" data-unique-id="90e20e8d-c16e-485f-8d7e-db7fb7e7bed2" data-file-name="app/page.tsx">Join Discussions</span></h3>
                <p className="text-sm sm:text-base text-muted-foreground mb-4 sm:mb-6" data-unique-id="a4e825a3-acd4-4374-ba52-2dfebc90b614" data-file-name="app/page.tsx"><span className="editable-text" data-unique-id="666c0461-4bd6-4c22-8e51-25d28b26ecf2" data-file-name="app/page.tsx">
                  Participate in discussions, share your experiences, report bugs, and suggest new features.
                </span></p>
                <a href="https://github.com/jatinkrmalik/vocalinux/discussions" target="_blank" rel="noopener noreferrer" className="flex items-center text-primary font-medium hover:underline text-sm sm:text-base" data-unique-id="e5a5dbd4-eb24-43a5-8fdf-25f227029822" data-file-name="app/page.tsx"><span className="editable-text" data-unique-id="d61229b9-3ac8-4b31-bca3-74d793fc842f" data-file-name="app/page.tsx">
                  Join Community </span><ChevronRight className="h-3 w-3 sm:h-4 sm:w-4 ml-1" />
                </a>
              </div>
            </FadeInSection>
          </div>

          <FadeInSection delay={0.4}>
            <div className="mt-10 sm:mt-16 text-center" data-unique-id="d35c67b0-7108-4925-8875-211a4dfe63f5" data-file-name="app/page.tsx">
              <div className="inline-block bg-primary/10 px-3 sm:px-4 py-1.5 sm:py-2 rounded-full text-xs sm:text-sm font-medium text-primary mb-3 sm:mb-4" data-unique-id="bfa21f5b-06bd-4e1f-8f46-420c9a7d7b1f" data-file-name="app/page.tsx" data-dynamic-text="true">
                <Star className="h-3 w-3 sm:h-4 sm:w-4 inline mr-1" /> 
                {stars}<span className="editable-text" data-unique-id="6901eff6-d179-4081-ac5f-517dc0f763a3" data-file-name="app/page.tsx"> GitHub Stars
              </span></div>
              <h3 className="text-xl sm:text-2xl font-semibold mb-4 sm:mb-6" data-unique-id="84204bfb-691c-47b7-8805-4de577f6fa0b" data-file-name="app/page.tsx"><span className="editable-text" data-unique-id="19df7b53-f6f1-4936-88b6-d7fbaebabaad" data-file-name="app/page.tsx">Support the Project</span></h3>
              <div className="flex flex-wrap justify-center gap-3 sm:gap-4" data-unique-id="7d9596cf-3ec8-45eb-8cbc-b7c8ba61bba1" data-file-name="app/page.tsx">
                <a href="https://github.com/jatinkrmalik/vocalinux" target="_blank" rel="noopener noreferrer" className="bg-secondary text-secondary-foreground hover:bg-secondary/80 px-4 sm:px-6 py-2 sm:py-3 rounded-lg text-sm sm:text-base font-medium flex items-center gap-2 transition-colors" data-unique-id="6bf21716-2bd2-41bc-b474-3c443eaf2c6d" data-file-name="app/page.tsx">
                  <Star className="h-4 w-4 sm:h-5 sm:w-5" /><span className="editable-text" data-unique-id="4e1ae6bc-00f1-4e78-abb8-3cfd5888eca3" data-file-name="app/page.tsx">
                  Star on GitHub
                </span></a>
                <a href="https://github.com/jatinkrmalik/vocalinux/issues" target="_blank" rel="noopener noreferrer" className="bg-secondary text-secondary-foreground hover:bg-secondary/80 px-4 sm:px-6 py-2 sm:py-3 rounded-lg text-sm sm:text-base font-medium flex items-center gap-2 transition-colors" data-unique-id="dcaaf5c3-7ce6-46ce-b025-a542c4019933" data-file-name="app/page.tsx">
                  <ExternalLink className="h-4 w-4 sm:h-5 sm:w-5" /><span className="editable-text" data-unique-id="187a832d-f856-4b1d-9745-f0da9425c7ea" data-file-name="app/page.tsx">
                  Report Issues
                </span></a>
              </div>
            </div>
          </FadeInSection>
        </div>
      </section>

      {/* FAQ */}
      <section id="faq" className="py-10 sm:py-16 px-4 sm:px-6" data-unique-id="75411b0d-1f86-4dbd-acfe-c7480de810b5" data-file-name="app/page.tsx">
        <div className="max-w-7xl mx-auto" data-unique-id="7e51faa3-b789-4f7b-9922-d3026062d434" data-file-name="app/page.tsx">
          <FadeInSection>
            <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold text-center mb-10 sm:mb-16" data-unique-id="9c6407a7-d279-4d1d-8b7d-37f71d38ca09" data-file-name="app/page.tsx"><span className="editable-text" data-unique-id="401251c2-3458-4c00-aa19-0f7d51ce95d4" data-file-name="app/page.tsx">Frequently Asked Questions</span></h2>
          </FadeInSection>

          <div className="max-w-3xl mx-auto space-y-4 sm:space-y-8" data-unique-id="e10c04e9-7366-48bc-aef8-9d46e30e8919" data-file-name="app/page.tsx" data-dynamic-text="true">
            {[{
            question: "Is Vocalinux really 100% offline?",
            answer: "Yes, Vocalinux processes all voice recognition locally on your machine. Your voice data never leaves your computer, ensuring complete privacy and security."
          }, {
            question: "Which Linux distributions are supported?",
            answer: "Vocalinux is designed to work with most major Linux distributions including Ubuntu, Fedora, Debian, Arch Linux, Linux Mint, and more. It's compatible with both X11 and Wayland display servers."
          }, {
            question: "How accurate is the speech recognition?",
            answer: "Recognition accuracy depends on several factors including microphone quality, background noise, and the model size selected. With a good microphone and the large model, accuracy can exceed 95% for most users speaking clearly."
          }, {
            question: "What are the system requirements?",
            answer: "Minimum requirements: 4GB RAM, dual-core CPU, and 500MB disk space for the small model. For optimal performance with the large model, we recommend 8GB RAM, a quad-core CPU, and 2GB of disk space."
          }, {
            question: "Can I use Vocalinux in languages other than English?",
            answer: "Yes, Vocalinux supports multiple languages depending on the recognition engine selected. VOSK and Whisper engines support dozens of languages with varying levels of accuracy."
          }, {
            question: "How can I customize Vocalinux for my needs?",
            answer: "Vocalinux can be customized through its configuration file. You can change the recognition engine, model size, activation method, keyboard shortcuts, and add custom voice commands."
          }].map((item, i) => <FadeInSection key={i} delay={i * 0.1} data-unique-id="d32e423f-bcb2-47a2-a5fe-1f8cd02571a6" data-file-name="app/page.tsx" data-dynamic-text="true">
                <div className="bg-white dark:bg-zinc-800 rounded-xl p-4 sm:p-6 shadow-md" data-is-mapped="true" data-unique-id="e47c139b-3621-4fb6-a1d0-c2e2c4e3cf62" data-file-name="app/page.tsx">
                  <h3 className="text-lg sm:text-xl font-semibold mb-2 sm:mb-3" data-is-mapped="true" data-unique-id="d5261468-afc9-440e-b4d2-a371ca4e22d8" data-file-name="app/page.tsx" data-dynamic-text="true">{item.question}</h3>
                  <p className="text-sm sm:text-base text-muted-foreground" data-is-mapped="true" data-unique-id="2a42d8e3-20c5-4707-953f-36be59db69c6" data-file-name="app/page.tsx" data-dynamic-text="true">{item.answer}</p>
                </div>
              </FadeInSection>)}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-10 sm:py-16 px-4 sm:px-6 bg-zinc-800 text-white" data-unique-id="aa7b9671-7a39-47aa-bcbe-a70923066fae" data-file-name="app/page.tsx">
        <div className="max-w-7xl mx-auto" data-unique-id="c93969fb-f819-48da-af3a-d52ef52e05fc" data-file-name="app/page.tsx">
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-8 sm:gap-10" data-unique-id="7dda5c0e-d288-4823-9693-aa8ced23e69a" data-file-name="app/page.tsx">
            <div className="md:col-span-2" data-unique-id="e143d15f-cf23-4807-9411-f51eb27b6b45" data-file-name="app/page.tsx">
              <div className="flex items-center gap-2 mb-3 sm:mb-4" data-unique-id="7871f739-dd39-481b-b595-6c13ecabe27a" data-file-name="app/page.tsx">
                <Mic className="h-5 w-5 sm:h-6 sm:w-6 text-primary" />
                <h2 className="text-lg sm:text-xl font-bold" data-unique-id="9678d441-3944-42a9-a516-326cf82a4a48" data-file-name="app/page.tsx"><span className="editable-text" data-unique-id="9fcbd524-accd-48bd-8764-478a95c8b549" data-file-name="app/page.tsx">Vocalinux</span></h2>
              </div>
              <p className="text-zinc-300 text-sm sm:text-base mb-4 sm:mb-6" data-unique-id="a3eccae8-dbca-4e8c-a3f8-0899c82ad20e" data-file-name="app/page.tsx"><span className="editable-text" data-unique-id="9aa77815-6dc5-4dde-b96e-13011ed76f82" data-file-name="app/page.tsx">
                Open-source voice dictation for Linux that respects your privacy.
              </span></p>
              <div className="flex gap-4" data-unique-id="54761849-bee1-4c1a-acf5-046148f5a509" data-file-name="app/page.tsx">
                <a href="https://github.com/jatinkrmalik/vocalinux" target="_blank" rel="noopener noreferrer" className="text-zinc-300 hover:text-white transition-colors" data-unique-id="932d3ab1-d0cf-4f91-a952-baad8d57ce33" data-file-name="app/page.tsx">
                  <Github className="h-4 w-4 sm:h-5 sm:w-5" />
                </a>
              </div>
            </div>
            
            <div data-unique-id="ac788080-1307-48e3-b974-1f1f924b3373" data-file-name="app/page.tsx">
              <h3 className="font-semibold mb-3 sm:mb-4 text-sm sm:text-base" data-unique-id="b5d00fe3-96b1-41ff-9fc9-5072341743e9" data-file-name="app/page.tsx"><span className="editable-text" data-unique-id="15105fda-5929-4481-8026-ace2515e7c1e" data-file-name="app/page.tsx">Resources</span></h3>
              <ul className="space-y-1 sm:space-y-2 text-xs sm:text-sm" data-unique-id="f11a18d3-b47a-4867-9143-fc70cd9a93a9" data-file-name="app/page.tsx">
                <li data-unique-id="4a8c5367-174c-4516-9ae1-dc2518c90fb6" data-file-name="app/page.tsx">
                  <a href="https://github.com/jatinkrmalik/vocalinux/wiki" target="_blank" rel="noopener noreferrer" className="text-zinc-300 hover:text-white transition-colors" data-unique-id="39b2661c-585d-40b9-8a48-8269cf7d6b48" data-file-name="app/page.tsx"><span className="editable-text" data-unique-id="a8121ab7-fd59-4750-8fa4-c5b6f40d4a8b" data-file-name="app/page.tsx">
                    Documentation
                  </span></a>
                </li>
                <li data-unique-id="f017044b-8f48-4253-8380-6cac196fdaa0" data-file-name="app/page.tsx">
                  <a href="https://github.com/jatinkrmalik/vocalinux/issues" target="_blank" rel="noopener noreferrer" className="text-zinc-300 hover:text-white transition-colors" data-unique-id="96d37a09-90bf-4167-ac37-136d9d8e3c3e" data-file-name="app/page.tsx"><span className="editable-text" data-unique-id="0f8e9c43-3c4b-400f-b28d-44de3ea48996" data-file-name="app/page.tsx">
                    Issue Tracker
                  </span></a>
                </li>
                <li data-unique-id="c00e9c19-de1b-4371-ad08-28b04e590a9b" data-file-name="app/page.tsx">
                  <a href="https://github.com/jatinkrmalik/vocalinux/releases" target="_blank" rel="noopener noreferrer" className="text-zinc-300 hover:text-white transition-colors" data-unique-id="619b532f-c2ac-453c-937c-874b2fc44969" data-file-name="app/page.tsx"><span className="editable-text" data-unique-id="eb9c7e2c-b862-4a0b-be13-eca55f5a2e90" data-file-name="app/page.tsx">
                    Releases
                  </span></a>
                </li>
                <li data-unique-id="31042125-2dd9-480e-867f-37996e99d709" data-file-name="app/page.tsx">
                  <a href="#faq" className="text-zinc-300 hover:text-white transition-colors" onClick={() => setMobileMenuOpen(false)} data-unique-id="5c5ab1c2-c408-48da-bec3-a86fced1aca3" data-file-name="app/page.tsx"><span className="editable-text" data-unique-id="ac792131-2aa4-4916-89b4-6e03e74a581a" data-file-name="app/page.tsx">
                    FAQ
                  </span></a>
                </li>
              </ul>
            </div>
            
            <div data-unique-id="246358b4-3469-4c23-a984-f1481b9f299a" data-file-name="app/page.tsx">
              <h3 className="font-semibold mb-3 sm:mb-4 text-sm sm:text-base" data-unique-id="79ce0b94-653c-4d34-871a-7b82f83652d6" data-file-name="app/page.tsx"><span className="editable-text" data-unique-id="f3b0fd7f-87ba-49b2-8136-dba303395235" data-file-name="app/page.tsx">Community</span></h3>
              <ul className="space-y-1 sm:space-y-2 text-xs sm:text-sm" data-unique-id="6022dc30-1d11-4acd-ba68-20baab1ae99c" data-file-name="app/page.tsx">
                <li data-unique-id="0a7d65b4-7188-4029-9ba5-b6de95cf450b" data-file-name="app/page.tsx">
                  <a href="https://github.com/jatinkrmalik/vocalinux" target="_blank" rel="noopener noreferrer" className="text-zinc-300 hover:text-white transition-colors" data-unique-id="49dffae1-f447-4611-b6f6-8404ae3880cc" data-file-name="app/page.tsx"><span className="editable-text" data-unique-id="799a94c5-44d2-4977-9102-14c265402ec0" data-file-name="app/page.tsx">
                    GitHub
                  </span></a>
                </li>
                <li data-unique-id="70588474-7115-454d-9460-13f760ade26a" data-file-name="app/page.tsx">
                  <a href="https://github.com/jatinkrmalik/vocalinux/discussions" target="_blank" rel="noopener noreferrer" className="text-zinc-300 hover:text-white transition-colors" data-unique-id="05ce2a2b-1833-4a94-aceb-99c38ba4265a" data-file-name="app/page.tsx"><span className="editable-text" data-unique-id="8442239e-88c9-4f46-a0a6-7f3b44c65cec" data-file-name="app/page.tsx">
                    Discussions
                  </span></a>
                </li>
                <li data-unique-id="3478d3d4-f263-4375-9bf1-04cf910a371a" data-file-name="app/page.tsx">
                  <a href="https://github.com/jatinkrmalik/vocalinux/contribute" target="_blank" rel="noopener noreferrer" className="text-zinc-300 hover:text-white transition-colors" data-unique-id="2dc2cd69-c664-45fc-9c06-c164f2876630" data-file-name="app/page.tsx"><span className="editable-text" data-unique-id="4fe9b355-4fa6-4583-9a06-768012acc6dc" data-file-name="app/page.tsx">
                    Contribute
                  </span></a>
                </li>
                <li data-unique-id="b464302a-df39-426a-8942-58d6936c3abd" data-file-name="app/page.tsx">
                  <a href="mailto:contact@vocalinux.com" className="text-zinc-300 hover:text-white transition-colors" data-unique-id="fd42e264-5681-4837-9fe9-a8437bfac1b6" data-file-name="app/page.tsx"><span className="editable-text" data-unique-id="f6e33e4e-a366-4c19-82a4-5c48475bbfab" data-file-name="app/page.tsx">
                    Contact
                  </span></a>
                </li>
              </ul>
            </div>
          </div>
          
          <div className="mt-8 sm:mt-12 pt-4 sm:pt-6 border-t border-zinc-700" data-unique-id="edac703a-78ba-45d3-9525-22b77cc0a39f" data-file-name="app/page.tsx">
            <p className="text-zinc-400 text-xs sm:text-sm" data-unique-id="3631f1ff-773d-45d0-b534-34419e8d4479" data-file-name="app/page.tsx" data-dynamic-text="true"><span className="editable-text" data-unique-id="60be5801-7d70-4fc1-b4fd-4a3f91d6f549" data-file-name="app/page.tsx">
              © </span>{new Date().getFullYear()}<span className="editable-text" data-unique-id="30f1701c-65ce-4efc-8f3c-98f17c99c065" data-file-name="app/page.tsx"> Vocalinux. Open-source software released under the MIT License.
            </span></p>
          </div>
        </div>
      </footer>
    </main>;
}