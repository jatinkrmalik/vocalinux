"use client";

import { useEffect, useState } from "react";
import { Moon, Sun } from "lucide-react";
import { useTheme } from "next-themes";
import { motion } from "framer-motion";
export function ThemeToggle() {
  const [mounted, setMounted] = useState(false);
  const {
    theme,
    setTheme
  } = useTheme();

  // Wait for component to be mounted to avoid hydration mismatch
  useEffect(() => {
    setMounted(true);
  }, []);
  if (!mounted) {
    return <div className="w-9 h-9 bg-muted rounded-md flex items-center justify-center">
        <span className="sr-only">Loading theme toggle</span>
      </div>;
  }
  return <motion.button whileTap={{
    scale: 0.95
  }} onClick={() => setTheme(theme === "dark" ? "light" : "dark")} className="w-8 h-8 sm:w-9 sm:h-9 bg-muted hover:bg-muted/80 rounded-md flex items-center justify-center transition-all" aria-label="Toggle theme">
      {theme === "dark" ? <Sun className="h-4 w-4 sm:h-[1.2rem] sm:w-[1.2rem] text-yellow-400" /> : <Moon className="h-4 w-4 sm:h-[1.2rem] sm:w-[1.2rem] text-slate-700" />}
      <span className="sr-only">Toggle theme</span>
    </motion.button>;
}