import React from "react";
import clsx from "clsx";

type SectionProps = {
  id?: string;
  className?: string;
  children: React.ReactNode;
};

export default function Section({ id, className, children }: SectionProps) {
  return (
    <section id={id} className={clsx("w-full", className)}>
      <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">{children}</div>
    </section>
  );
}


