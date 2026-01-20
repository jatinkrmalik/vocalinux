"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Mic, MicOff, AlertCircle, Chrome, Globe, Volume2, Sparkles } from "lucide-react";

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

export function LiveDemo() {
  const [isSupported, setIsSupported] = useState<boolean | null>(null);
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [interimTranscript, setInterimTranscript] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [hasPermission, setHasPermission] = useState<boolean | null>(null);
  const recognitionRef = useRef<SpeechRecognition | null>(null);

  // Check for browser support
  useEffect(() => {
    const SpeechRecognitionAPI = window.SpeechRecognition || window.webkitSpeechRecognition;
    setIsSupported(!!SpeechRecognitionAPI);
  }, []);

  // Initialize recognition
  const initRecognition = useCallback(() => {
    const SpeechRecognitionAPI = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognitionAPI) return null;

    const recognition = new SpeechRecognitionAPI();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = "en-US";

    recognition.onstart = () => {
      setIsListening(true);
      setError(null);
      setHasPermission(true);
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognition.onresult = (event: SpeechRecognitionEvent) => {
      let interim = "";
      let final = "";

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          final += transcript;
        } else {
          interim += transcript;
        }
      }

      if (final) {
        setTranscript((prev) => prev + final + " ");
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

  const clearTranscript = useCallback(() => {
    setTranscript("");
    setInterimTranscript("");
  }, []);

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
          <motion.button
            onClick={isListening ? stopListening : startListening}
            className={`relative h-20 w-20 sm:h-24 sm:w-24 rounded-full flex items-center justify-center transition-all ${
              isListening
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
              <MicOff className="h-8 w-8 sm:h-10 sm:w-10 text-white relative z-10" />
            ) : (
              <Mic className="h-8 w-8 sm:h-10 sm:w-10 text-white relative z-10" />
            )}
          </motion.button>
          
          <p className="text-sm text-zinc-400 mt-4">
            {isListening ? (
              <span className="flex items-center gap-2">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-red-500"></span>
                </span>
                Listening... Click to stop
              </span>
            ) : (
              "Click the microphone to try voice recognition"
            )}
          </p>
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
