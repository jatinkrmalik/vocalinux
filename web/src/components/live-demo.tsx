"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Mic, MicOff, AlertCircle, Chrome, Globe, Volume2, Sparkles, Keyboard } from "lucide-react";

// Define types for Web Speech API
interface SpeechRecognitionEvent {
    results: SpeechRecognitionResultList;
    resultIndex: number;
}

interface SpeechRecognitionErrorEvent {
    error: string;
    message?: string;
}

interface SpeechRecognition extends EventTarget {
    continuous: boolean;
    interimResults: boolean;
    lang: string;
    start(): void;
    stop(): void;
    abort(): void;
    onstart: ((this: SpeechRecognition, ev: Event) => void) | null;
    onend: ((this: SpeechRecognition, ev: Event) => void) | null;
    onresult: ((this: SpeechRecognition, ev: SpeechRecognitionEvent) => void) | null;
    onerror: ((this: SpeechRecognition, ev: SpeechRecognitionErrorEvent) => void) | null;
}

declare global {
    interface Window {
        SpeechRecognition?: new () => SpeechRecognition;
        webkitSpeechRecognition?: new () => SpeechRecognition;
    }
}

// Language code to display name and flag mapping
const LANGUAGE_MAP: Record<string, { name: string; flag: string }> = {
    "en": { name: "English", flag: "🇬🇧" },
    "en-US": { name: "English (US)", flag: "🇺🇸" },
    "en-GB": { name: "English (UK)", flag: "🇬🇧" },
    "en-CA": { name: "English (Canada)", flag: "🇨🇦" },
    "en-AU": { name: "English (Australia)", flag: "🇦🇺" },
    "fr": { name: "French", flag: "🇫🇷" },
    "fr-FR": { name: "French (France)", flag: "🇫🇷" },
    "fr-CA": { name: "French (Canada)", flag: "🇨🇦" },
    "de": { name: "German", flag: "🇩🇪" },
    "de-DE": { name: "German (Germany)", flag: "🇩🇪" },
    "es": { name: "Spanish", flag: "🇪🇸" },
    "es-ES": { name: "Spanish (Spain)", flag: "🇪🇸" },
    "es-MX": { name: "Spanish (Mexico)", flag: "🇲🇽" },
    "es-AR": { name: "Spanish (Argentina)", flag: "🇦🇷" },
    "it": { name: "Italian", flag: "🇮🇹" },
    "it-IT": { name: "Italian (Italy)", flag: "🇮🇹" },
    "pt": { name: "Portuguese", flag: "🇵🇹" },
    "pt-BR": { name: "Portuguese (Brazil)", flag: "🇧🇷" },
    "pt-PT": { name: "Portuguese (Portugal)", flag: "🇵🇹" },
    "nl": { name: "Dutch", flag: "🇳🇱" },
    "nl-NL": { name: "Dutch (Netherlands)", flag: "🇳🇱" },
    "ja": { name: "Japanese", flag: "🇯🇵" },
    "ja-JP": { name: "Japanese (Japan)", flag: "🇯🇵" },
    "ko": { name: "Korean", flag: "🇰🇷" },
    "ko-KR": { name: "Korean (Korea)", flag: "🇰🇷" },
    "zh": { name: "Chinese", flag: "🇨🇳" },
    "zh-CN": { name: "Chinese (Simplified)", flag: "🇨🇳" },
    "zh-TW": { name: "Chinese (Traditional)", flag: "🇹🇼" },
    "ru": { name: "Russian", flag: "🇷🇺" },
    "ru-RU": { name: "Russian (Russia)", flag: "🇷🇺" },
    "ar": { name: "Arabic", flag: "🇸🇦" },
    "ar-SA": { name: "Arabic (Saudi Arabia)", flag: "🇸🇦" },
    "hi": { name: "Hindi", flag: "🇮🇳" },
    "hi-IN": { name: "Hindi (India)", flag: "🇮🇳" },
    "pl": { name: "Polish", flag: "🇵🇱" },
    "pl-PL": { name: "Polish (Poland)", flag: "🇵🇱" },
    "tr": { name: "Turkish", flag: "🇹🇷" },
    "tr-TR": { name: "Turkish (Turkey)", flag: "🇹🇷" },
    "sv": { name: "Swedish", flag: "🇸🇪" },
    "sv-SE": { name: "Swedish (Sweden)", flag: "🇸🇪" },
    "da": { name: "Danish", flag: "🇩🇰" },
    "da-DK": { name: "Danish (Denmark)", flag: "🇩🇰" },
    "fi": { name: "Finnish", flag: "🇫🇮" },
    "fi-FI": { name: "Finnish (Finland)", flag: "🇫🇮" },
    "no": { name: "Norwegian", flag: "🇳🇴" },
    "no-NO": { name: "Norwegian (Norway)", flag: "🇳🇴" },
    "cs": { name: "Czech", flag: "🇨🇿" },
    "cs-CZ": { name: "Czech (Czech Republic)", flag: "🇨🇿" },
    "el": { name: "Greek", flag: "🇬🇷" },
    "el-GR": { name: "Greek (Greece)", flag: "🇬🇷" },
    "he": { name: "Hebrew", flag: "🇮🇱" },
    "he-IL": { name: "Hebrew (Israel)", flag: "🇮🇱" },
    "th": { name: "Thai", flag: "🇹🇭" },
    "th-TH": { name: "Thai (Thailand)", flag: "🇹🇭" },
    "vi": { name: "Vietnamese", flag: "🇻🇳" },
    "vi-VN": { name: "Vietnamese (Vietnam)", flag: "🇻🇳" },
    "id": { name: "Indonesian", flag: "🇮🇩" },
    "id-ID": { name: "Indonesian (Indonesia)", flag: "🇮🇩" },
    "ms": { name: "Malay", flag: "🇲🇾" },
    "ms-MY": { name: "Malay (Malaysia)", flag: "🇲🇾" },
};

// Helper function to get language display info
function getLanguageInfo(locale: string): { name: string; flag: string } {
    // Try exact match first
    if (LANGUAGE_MAP[locale]) {
        return LANGUAGE_MAP[locale];
    }
    // Try base language code (e.g., "en-US" -> "en")
    const baseCode = locale.split("-")[0];
    if (LANGUAGE_MAP[baseCode]) {
        return LANGUAGE_MAP[baseCode];
    }
    // Fallback to locale code itself
    return { name: locale, flag: "🌐" };
}

export function LiveDemo() {
    const [isSupported, setIsSupported] = useState<boolean | null>(null);
    const [isListening, setIsListening] = useState(false);
    const [transcript, setTranscript] = useState("");
    const [interimTranscript, setInterimTranscript] = useState("");
    const [error, setError] = useState<string | null>(null);
    const [hasPermission, setHasPermission] = useState<boolean | null>(null);
    const [lastCtrlPress, setLastCtrlPress] = useState<number | null>(null);
    const [showCtrlHint, setShowCtrlHint] = useState(false);
    const [detectedLanguage, setDetectedLanguage] = useState<string>("en-US");
    const recognitionRef = useRef<SpeechRecognition | null>(null);
    const isListeningRef = useRef(false);
    // Track the index up to which results have been processed to prevent duplicates on mobile
    const processedResultIndexRef = useRef(0);

    // Keep ref in sync with state for use in event handlers
    useEffect(() => {
        isListeningRef.current = isListening;
    }, [isListening]);

    // Check for browser support and detect language
    useEffect(() => {
        const SpeechRecognitionAPI = window.SpeechRecognition || window.webkitSpeechRecognition;
        setIsSupported(!!SpeechRecognitionAPI);
        
        // Detect browser language
        const browserLang = navigator.language || "en-US";
        setDetectedLanguage(browserLang);
    }, []);

    // Initialize recognition
    const initRecognition = useCallback(() => {
        const SpeechRecognitionAPI = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognitionAPI) return null;

        const recognition = new SpeechRecognitionAPI();
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = navigator.language || "en-US";

        recognition.onstart = () => {
            setIsListening(true);
            setError(null);
            setHasPermission(true);
        };

        recognition.onend = () => {
            setIsListening(false);
        };

        recognition.onresult = (event: SpeechRecognitionEvent) => {
            // Get the base index - on some browsers (especially mobile), resultIndex
            // may be 0 but the array contains all previous results. We need to
            // track which results we've already processed to avoid duplicates.
            const startIndex = Math.max(event.resultIndex, processedResultIndexRef.current);

            let interim = "";
            let final = "";

            // Only process new results (from startIndex to end)
            for (let i = startIndex; i < event.results.length; i++) {
                const transcript = event.results[i][0].transcript;
                if (event.results[i].isFinal) {
                    final += transcript + " ";
                } else {
                    interim += transcript;
                }
            }

            // Update processed index to the end of current results
            // Any results before this have been handled
            processedResultIndexRef.current = event.results.length;

            if (final) {
                setTranscript((prev) => prev + final);
                setInterimTranscript("");
            } else {
                setInterimTranscript(interim);
            }
        };

        recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
            if (event.error === "not-allowed") {
                setHasPermission(false);
                setError("Microphone access denied. Please allow microphone permissions.");
            } else if (event.error === "no-speech") {
                // Ignore no-speech errors
            } else {
                setError(`Error: ${event.error}`);
            }
            setIsListening(false);
        };

        return recognition;
    }, []);

    const startListening = useCallback(() => {
        if (recognitionRef.current) {
            recognitionRef.current.abort();
        }
        recognitionRef.current = initRecognition();
        if (recognitionRef.current) {
            setTranscript("");
            setInterimTranscript("");
            processedResultIndexRef.current = 0; // Reset processed result index
            try {
                recognitionRef.current.start();
            } catch (e) {
                setError("Could not start recognition. Please try again.");
            }
        }
    }, [initRecognition]);

    const stopListening = useCallback(() => {
        if (recognitionRef.current) {
            recognitionRef.current.stop();
        }
    }, []);

    // Toggle listening state
    const toggleListening = useCallback(() => {
        if (isListeningRef.current) {
            stopListening();
        } else {
            startListening();
        }
    }, [startListening, stopListening]);

    const clearTranscript = useCallback(() => {
        setTranscript("");
        setInterimTranscript("");
    }, []);

    // Double-tap Ctrl detection
    useEffect(() => {
        const handleKeyDown = (event: KeyboardEvent) => {
            if (event.key !== "Control") return;

            const now = Date.now();
            const DOUBLE_TAP_DELAY = 400;

            // Show hint on first Ctrl press
            setShowCtrlHint(true);
            setTimeout(() => setShowCtrlHint(false), 600);

            if (lastCtrlPress && now - lastCtrlPress <= DOUBLE_TAP_DELAY) {
                // Double-tap detected!
                toggleListening();
                setLastCtrlPress(null);
                setShowCtrlHint(false);
            } else {
                setLastCtrlPress(now);
            }
        };

        window.addEventListener("keydown", handleKeyDown);
        return () => window.removeEventListener("keydown", handleKeyDown);
    }, [lastCtrlPress, toggleListening]);

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            if (recognitionRef.current) {
                recognitionRef.current.abort();
            }
        };
    }, []);

    // Not supported fallback
    if (isSupported === false) {
        return (
            <div className="bg-zinc-900 rounded-2xl p-6 sm:p-8 border border-zinc-800">
                <div className="text-center">
                    <div className="inline-flex items-center justify-center h-16 w-16 rounded-full bg-yellow-500/10 mb-4">
                        <AlertCircle className="h-8 w-8 text-yellow-500" />
                    </div>
                    <h3 className="text-xl font-semibold text-white mb-2">
                        Browser Demo Not Available
                    </h3>
                    <p className="text-zinc-400 mb-6 max-w-md mx-auto">
                        Your browser doesn&apos;t support the Web Speech API. Try opening this page in:
                    </p>
                    <div className="flex justify-center gap-4 mb-6">
                        <div className="flex items-center gap-2 text-zinc-300">
                            <Chrome className="h-5 w-5" />
                            <span>Chrome</span>
                        </div>
                        <div className="flex items-center gap-2 text-zinc-300">
                            <Globe className="h-5 w-5" />
                            <span>Edge</span>
                        </div>
                    </div>
                    <p className="text-sm text-zinc-500">
                        Or better yet — <a href="#install" className="text-primary hover:underline">install Vocalinux</a> for
                        the full offline experience with Whisper AI!
                    </p>
                </div>
            </div>
        );
    }

    // Loading state
    if (isSupported === null) {
        return (
            <div className="bg-zinc-900 rounded-2xl p-8 border border-zinc-800 animate-pulse">
                <div className="h-48 flex items-center justify-center">
                    <div className="text-zinc-500">Checking browser support...</div>
                </div>
            </div>
        );
    }

    return (
        <div className="bg-gradient-to-br from-zinc-900 to-zinc-950 rounded-2xl overflow-hidden border border-zinc-800">
            {/* Header */}
            <div className="px-4 sm:px-6 py-3 bg-zinc-800/50 border-b border-zinc-800 flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className="flex gap-1.5">
                        <div className="h-3 w-3 rounded-full bg-red-500/70" />
                        <div className="h-3 w-3 rounded-full bg-yellow-500/70" />
                        <div className="h-3 w-3 rounded-full bg-green-500/70" />
                    </div>
                    <span className="text-sm text-zinc-400 font-medium">
                        Live Browser Demo
                    </span>
                    <span className="text-xs bg-primary/20 text-primary px-2 py-0.5 rounded-full">
                        Web Speech API
                    </span>
                    {(() => {
                        const langInfo = getLanguageInfo(detectedLanguage);
                        return (
                            <span 
                                className="text-xs bg-zinc-700/50 text-zinc-300 px-2 py-0.5 rounded-full flex items-center gap-1"
                                title={`Detected language: ${langInfo.name} (${detectedLanguage})`}
                            >
                                <span>{langInfo.flag}</span>
                                <span className="hidden sm:inline">{langInfo.name}</span>
                            </span>
                        );
                    })()}
                </div>
                {transcript && (
                    <button
                        onClick={clearTranscript}
                        className="text-xs text-zinc-500 hover:text-zinc-300 transition-colors"
                    >
                        Clear
                    </button>
                )}
            </div>

            {/* Main content */}
            <div className="p-6 sm:p-8">
                {/* Error message */}
                <AnimatePresence>
                    {error && (
                        <motion.div
                            initial={{ opacity: 0, y: -10 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -10 }}
                            className="mb-6 p-4 bg-red-500/10 border border-red-500/20 rounded-lg flex items-start gap-3"
                        >
                            <AlertCircle className="h-5 w-5 text-red-400 flex-shrink-0 mt-0.5" />
                            <div>
                                <p className="text-sm text-red-400">{error}</p>
                                {hasPermission === false && (
                                    <p className="text-xs text-red-400/70 mt-1">
                                        Click the lock icon in your browser&apos;s address bar to enable microphone access.
                                    </p>
                                )}
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>

                {/* Microphone button */}
                <div className="flex flex-col items-center mb-6">
                    {/* Double-tap Ctrl hint */}
                    <AnimatePresence>
                        {showCtrlHint && !isListening && (
                            <motion.div
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, y: -10 }}
                                className="mb-4 px-4 py-2 bg-primary/20 rounded-full text-sm text-primary flex items-center gap-2"
                            >
                                <Keyboard className="h-4 w-4" />
                                Tap Ctrl again to start!
                            </motion.div>
                        )}
                    </AnimatePresence>

                    <motion.button
                        onClick={toggleListening}
                        className={`relative h-20 w-20 sm:h-24 sm:w-24 rounded-full flex items-center justify-center transition-all ${isListening
                                ? "bg-red-500 hover:bg-red-600 shadow-lg shadow-red-500/30"
                                : "bg-primary hover:bg-primary/90 shadow-lg shadow-primary/30"
                            }`}
                        whileTap={{ scale: 0.95 }}
                        aria-label={isListening ? "Stop listening" : "Start listening"}
                    >
                        {/* Pulse animation when listening */}
                        {isListening && (
                            <>
                                <motion.div
                                    className="absolute inset-0 rounded-full bg-red-500"
                                    animate={{ scale: [1, 1.2], opacity: [0.5, 0] }}
                                    transition={{ duration: 1.5, repeat: Infinity }}
                                />
                                <motion.div
                                    className="absolute inset-0 rounded-full bg-red-500"
                                    animate={{ scale: [1, 1.4], opacity: [0.3, 0] }}
                                    transition={{ duration: 1.5, repeat: Infinity, delay: 0.5 }}
                                />
                            </>
                        )}
                        {isListening ? (
                            <MicOff className="h-8 w-8 sm:h-10 sm:w-10 text-zinc-900 relative z-10" />
                        ) : (
                            <Mic className="h-8 w-8 sm:h-10 sm:w-10 text-zinc-900 relative z-10" />
                        )}
                    </motion.button>

                    <div className="text-center mt-4">
                        {isListening ? (
                            <div className="space-y-2">
                                <p className="text-sm font-medium text-zinc-200 flex items-center justify-center gap-2">
                                    {(() => {
                                        const langInfo = getLanguageInfo(detectedLanguage);
                                        return (
                                            <>
                                                <span>{langInfo.flag}</span>
                                                <span>Listening in {langInfo.name}</span>
                                            </>
                                        );
                                    })()}
                                </p>
                                <p className="text-xs text-zinc-400">
                                    <span className="flex items-center justify-center gap-2">
                                        <span className="relative flex h-2 w-2">
                                            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                                            <span className="relative inline-flex rounded-full h-2 w-2 bg-red-500"></span>
                                        </span>
                                        Double-tap <kbd className="px-2 py-1 bg-zinc-800 border border-zinc-600 rounded text-xs mx-1 text-zinc-200 font-mono">Ctrl</kbd> or click to stop
                                    </span>
                                </p>
                            </div>
                        ) : (
                            <div className="space-y-1">
                                <p className="text-sm text-zinc-200">
                                    Double-tap <kbd className="px-2 py-1 bg-zinc-800 border border-zinc-600 rounded text-xs mx-1 text-zinc-200 font-mono">Ctrl</kbd> to start
                                </p>
                                <p className="text-xs text-zinc-400">or click the microphone</p>
                            </div>
                        )}
                    </div>
                </div>

                {/* Transcript area */}
                <div className="bg-zinc-950/50 rounded-xl p-4 sm:p-6 min-h-[120px] border border-zinc-800/50">
                    {transcript || interimTranscript ? (
                        <div className="text-zinc-200 leading-relaxed">
                            <span>{transcript}</span>
                            {interimTranscript && (
                                <span className="text-zinc-500 italic">{interimTranscript}</span>
                            )}
                        </div>
                    ) : (
                        <div className="text-zinc-500 text-center py-4">
                            <Volume2 className="h-8 w-8 mx-auto mb-2 opacity-50" />
                            <p>Your transcribed speech will appear here</p>
                        </div>
                    )}
                </div>

                {/* Info banner */}
                <div className="mt-6 flex items-start gap-3 p-4 bg-primary/5 rounded-lg border border-primary/10">
                    <Sparkles className="h-5 w-5 text-primary flex-shrink-0 mt-0.5" />
                    <div className="text-sm">
                        <p className="text-zinc-300">
                            <strong>This is just a preview!</strong> The browser demo uses Web Speech API (cloud-based).
                        </p>
                        <p className="text-zinc-500 mt-1">
                            Vocalinux runs <strong>100% offline</strong> using Whisper AI — no cloud, no data sharing,
                            complete privacy. <a href="#install" className="text-primary hover:underline">Install it</a> to
                            experience the real deal!
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}
