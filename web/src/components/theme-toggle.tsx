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
    return <div className="w-9 h-9 bg-muted rounded-md flex items-center justify-center" data-unique-id="4ef36b6f-5b83-4a67-a991-4f70aea4ec19" data-file-name="components/theme-toggle.tsx">
        <span className="sr-only" data-unique-id="9dc304c5-60b7-4f04-9561-9cf2c2a58e09" data-file-name="components/theme-toggle.tsx"><span className="editable-text" data-unique-id="97b0ebb5-1aad-4b0e-b031-21053ba12dc0" data-file-name="components/theme-toggle.tsx">Loading theme toggle</span></span>
      </div>;
  }
  return <motion.button whileTap={{
    scale: 0.95
  }} onClick={() => setTheme(theme === "dark" ? "light" : "dark")} className="w-8 h-8 sm:w-9 sm:h-9 bg-muted hover:bg-muted/80 rounded-md flex items-center justify-center transition-all" aria-label="Toggle theme" data-unique-id="5f422091-838a-431f-9e75-917f703ab13c" data-file-name="components/theme-toggle.tsx" data-dynamic-text="true">
      {theme === "dark" ? <Sun className="h-4 w-4 sm:h-[1.2rem] sm:w-[1.2rem] text-yellow-400" /> : <Moon className="h-4 w-4 sm:h-[1.2rem] sm:w-[1.2rem] text-slate-700" />}
      <span className="sr-only" data-unique-id="b525d238-cd43-45a3-9db2-cdc8027ff1eb" data-file-name="components/theme-toggle.tsx"><span className="editable-text" data-unique-id="4ba377eb-21c8-4b06-ac04-8faa338729a7" data-file-name="components/theme-toggle.tsx">Toggle theme</span></span>
    </motion.button>;
}