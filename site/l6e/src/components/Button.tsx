"use client";

import React from "react";
import Link from "next/link";
import clsx from "clsx";

type ButtonVariant = "primary" | "secondary" | "outline" | "ghost";

type CommonProps = {
  variant?: ButtonVariant;
  className?: string;
  children: React.ReactNode;
};

type ButtonAsButton = CommonProps &
  React.ButtonHTMLAttributes<HTMLButtonElement> & { href?: undefined };
type ButtonAsLink = CommonProps &
  React.AnchorHTMLAttributes<HTMLAnchorElement> & { href: string };
type ButtonProps = ButtonAsButton | ButtonAsLink;

const variantToClasses: Record<ButtonVariant, string> = {
  primary:
    "bg-[var(--accent)] text-white hover:bg-[#15803d] focus-visible:outline-[var(--accent)]",
  secondary:
    "bg-[#1a1a1a] text-white border border-white/10 hover:bg-[#222]",
  outline:
    "bg-transparent text-white border border-white/20 hover:bg-white/5",
  ghost: "bg-transparent text-white hover:bg-white/5",
};

export function Button(props: ButtonProps) {
  const { variant = "primary", className, children, href, ...rest } = props;
  const classes = clsx(
    "inline-flex items-center justify-center h-10 px-4 rounded-md text-sm font-medium transition-colors focus-visible:outline-2 focus-visible:outline-offset-2",
    variantToClasses[variant],
    className
  );

  if (href) {
    const anchorProps = rest as React.AnchorHTMLAttributes<HTMLAnchorElement>;
    return (
      <Link href={href} className={classes} {...anchorProps}>
        {children}
      </Link>
    );
  }

  const buttonProps = rest as React.ButtonHTMLAttributes<HTMLButtonElement>;
  return (
    <button className={classes} {...buttonProps}>
      {children}
    </button>
  );
}

export default Button;


