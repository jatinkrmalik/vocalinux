"use client";

import * as React from "react";
import { cn } from "@/lib/utils";
interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'default' | 'outline' | 'ghost' | 'link';
  size?: 'default' | 'sm' | 'lg';
  className?: string;
  asChild?: boolean;
  children?: React.ReactNode;
}
const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(({
  className,
  variant = "default",
  size = "default",
  asChild = false,
  ...props
}, ref) => {
  const Comp = asChild ? "span" : "button";
  return <Comp className={cn("inline-flex items-center justify-center rounded-lg font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50", {
    "bg-primary text-primary-foreground hover:bg-primary/90": variant === "default",
    "border border-input bg-background hover:bg-accent hover:text-accent-foreground": variant === "outline",
    "hover:bg-accent hover:text-accent-foreground": variant === "ghost",
    "text-primary underline-offset-4 hover:underline": variant === "link",
    "h-10 px-4 py-2": size === "default",
    "h-8 rounded-md px-3 text-xs": size === "sm",
    "h-12 rounded-md px-6": size === "lg"
  }, className)} ref={ref} {...props} />;
});
Button.displayName = "Button";
export { Button };