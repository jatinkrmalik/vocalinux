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
      {isActive && <div className="fixed inset-0 flex items-center justify-center z-50 bg-background/40 backdrop-blur-sm">
          <div className="flex flex-col items-center">
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
        }} className="relative mb-6">
              <motion.div animate={{
            scale: [1, 1.2, 1]
          }} transition={{
            repeat: Infinity,
            duration: 1.5
          }} className="bg-primary/10 p-6 rounded-full">
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
          }} />
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
        }} className="bg-white dark:bg-zinc-800 p-4 rounded-lg shadow-lg min-w-[300px] border border-border">
              <div className="flex items-center gap-2 mb-2">
                <div className="h-2 w-2 rounded-full bg-green-500 animate-pulse"></div>
                <span className="text-sm font-medium">Transcribing...</span>
              </div>
              <div className="min-h-[24px]">
                {text}
                <motion.span animate={{
              opacity: [1, 0]
            }} transition={{
              repeat: Infinity,
              duration: 0.8
            }} className="inline-block w-2 h-4 bg-primary ml-0.5" />
              </div>
            </motion.div>
          </div>
        </div>}
    </AnimatePresence>;
}