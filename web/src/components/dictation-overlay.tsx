"use client";

import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Mic } from "lucide-react";
interface DictationOverlayProps {
  isActive: boolean;
  onAnimationComplete?: () => void;
}
export function DictationOverlay({
  isActive,
  onAnimationComplete
}: DictationOverlayProps) {
  const [text, setText] = useState("");
  const fullText = "Hello world";

  // Handle text typing animation
  useEffect(() => {
    if (!isActive) {
      setText("");
      return;
    }
    let currentIndex = 0;
    const interval = setInterval(() => {
      if (currentIndex < fullText.length) {
        setText(fullText.substring(0, currentIndex + 1));
        currentIndex++;
      } else {
        clearInterval(interval);
        // Wait a bit before triggering the fade out
        setTimeout(() => {
          if (onAnimationComplete) onAnimationComplete();
        }, 800);
      }
    }, 100); // Speed of typing

    return () => clearInterval(interval);
  }, [isActive, onAnimationComplete]);
  return <AnimatePresence>
      {isActive && <div className="fixed inset-0 flex items-center justify-center z-50 bg-background/40 backdrop-blur-sm" data-unique-id="73f29596-a34d-4d7b-9c33-94c994beba56" data-file-name="components/dictation-overlay.tsx">
          <div className="flex flex-col items-center" data-unique-id="a63e27a7-6607-4e2f-ac18-22f36aa5177c" data-file-name="components/dictation-overlay.tsx" data-dynamic-text="true">
            {/* Microphone Icon */}
            <motion.div initial={{
          opacity: 0,
          scale: 0.5
        }} animate={{
          opacity: 1,
          scale: 1
        }} exit={{
          opacity: 0,
          scale: 0.5
        }} transition={{
          duration: 0.5
        }} className="relative mb-6" data-unique-id="a51981e6-39f5-44b0-b5b8-badaeff800ec" data-file-name="components/dictation-overlay.tsx" data-dynamic-text="true">
              <motion.div animate={{
            scale: [1, 1.2, 1]
          }} transition={{
            repeat: Infinity,
            duration: 1.5
          }} className="bg-primary/10 p-6 rounded-full" data-unique-id="475ec395-9c1e-4800-af6f-40ce7ee6e266" data-file-name="components/dictation-overlay.tsx">
                <Mic className="h-12 w-12 text-primary" />
              </motion.div>
              
              {/* Ripple effect */}
              <motion.div className="absolute inset-0 rounded-full border-2 border-primary" initial={{
            opacity: 0.6,
            scale: 1
          }} animate={{
            opacity: 0,
            scale: 1.8
          }} transition={{
            repeat: Infinity,
            duration: 1.5,
            ease: "easeOut"
          }} data-unique-id="f5b542bd-f5bb-4809-af37-2a72a44184e1" data-file-name="components/dictation-overlay.tsx" />
            </motion.div>
            
            {/* Text Box */}
            <motion.div initial={{
          opacity: 0,
          y: 10
        }} animate={{
          opacity: 1,
          y: 0
        }} exit={{
          opacity: 0,
          y: 10
        }} transition={{
          delay: 0.3,
          duration: 0.5
        }} className="bg-white dark:bg-zinc-800 p-4 rounded-lg shadow-lg min-w-[300px] border border-border" data-unique-id="99680bc6-f0b8-4ef7-ac31-f6ea7035ecdf" data-file-name="components/dictation-overlay.tsx">
              <div className="flex items-center gap-2 mb-2" data-unique-id="675b73f9-04de-4b87-be56-4fae6927b795" data-file-name="components/dictation-overlay.tsx">
                <div className="h-2 w-2 rounded-full bg-green-500 animate-pulse" data-unique-id="d99993f3-871f-4c25-805d-b15e7ae14fa5" data-file-name="components/dictation-overlay.tsx"></div>
                <span className="text-sm font-medium" data-unique-id="29e50d52-8aa2-46e1-b2a4-bd91ab9874f0" data-file-name="components/dictation-overlay.tsx"><span className="editable-text" data-unique-id="c833a664-84bf-4bc8-b23c-ff2f384bf175" data-file-name="components/dictation-overlay.tsx">Transcribing...</span></span>
              </div>
              <div className="min-h-[24px]" data-unique-id="81d6cdf1-a7ff-4d8c-9f15-1949329685bb" data-file-name="components/dictation-overlay.tsx" data-dynamic-text="true">
                {text}
                <motion.span animate={{
              opacity: [1, 0]
            }} transition={{
              repeat: Infinity,
              duration: 0.8
            }} className="inline-block w-2 h-4 bg-primary ml-0.5" data-unique-id="d10f4ecc-fbc2-4201-96a1-3ffb9dd816db" data-file-name="components/dictation-overlay.tsx" />
              </div>
            </motion.div>
          </div>
        </div>}
    </AnimatePresence>;
}