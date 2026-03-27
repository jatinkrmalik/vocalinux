"use client";

import { useState, useEffect, useCallback } from "react";

interface UseDoublePressOptions {
  key: string;
  delay?: number;
  onDoublePress?: () => void;
}

export function useDoublePress({
  key,
  delay = 400,
  onDoublePress,
}: UseDoublePressOptions) {
  const [lastPressed, setLastPressed] = useState<number | null>(null);
  const [isActive, setIsActive] = useState(false);

  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      // Only respond to the specified key
      if (event.key.toLowerCase() !== key.toLowerCase()) {
        return;
      }

      const now = Date.now();

      // First press or too much time has passed
      if (lastPressed === null || now - lastPressed > delay) {
        setLastPressed(now);
        return;
      }

      // Double press detected within the delay timeframe
      if (now - lastPressed <= delay) {
        setIsActive(true);
        if (onDoublePress) onDoublePress();
        setLastPressed(null);
      }
    },
    [key, delay, lastPressed, onDoublePress]
  );

  // Reset the active state
  const resetActive = useCallback(() => {
    setIsActive(false);
  }, []);

  useEffect(() => {
    // Add event listener for key press
    window.addEventListener("keydown", handleKeyDown);

    // Cleanup
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [handleKeyDown]);

  return { isActive, resetActive };
}
