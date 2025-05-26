import React from "react";
import { VocalinuxLogo } from "./icons";
import { cn } from "@/lib/utils";
interface LogoProps {
  className?: string;
  iconClassName?: string;
  textClassName?: string;
}
export function Logo({
  className,
  iconClassName,
  textClassName
}: LogoProps) {
  return <div className={cn("flex items-center gap-2", className)} data-unique-id="a1b7626e-adb6-498a-97dc-21507a6c6e22" data-file-name="components/logo.tsx">
      <VocalinuxLogo className={cn("h-8 w-8 text-primary", iconClassName)} />
      <span className={cn("font-bold text-xl", textClassName)} data-unique-id="c9a54c54-3c8e-4667-a3c1-ea265d7df166" data-file-name="components/logo.tsx"><span className="editable-text" data-unique-id="73a6ea30-8bd2-4f6c-9fe3-048638d1848b" data-file-name="components/logo.tsx">Vocalinux</span></span>
    </div>;
}