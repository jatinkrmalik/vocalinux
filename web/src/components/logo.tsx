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
  return <div className={cn("flex items-center gap-2", className)}>
    <VocalinuxLogo className={cn("h-8 w-8", iconClassName)} />
    <span className={cn("font-bold text-xl", textClassName)}>Vocalinux</span>
  </div>;
}
