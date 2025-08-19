import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";

const inter = Inter({ variable: "--font-inter", subsets: ["latin"] });
const jbMono = JetBrains_Mono({ variable: "--font-jbmono", subsets: ["latin"] });

export const metadata: Metadata = {
  title: "l6e AI - Portable AI Agents | Localize AI for Any Machine",
  description:
    "Create portable AI agents that run anywhere. l6e AI lets you build, package, and deploy AI on any machine. No cloud required, complete data sovereignty.",
  metadataBase: new URL("https://l6e.ai"),
  openGraph: {
    title: "l6e AI - Portable AI Agents for Any Machine",
    description:
      "Build, package, and deploy AI agents anywhere. Complete data sovereignty with portable AI.",
    url: "https://l6e.ai",
    images: [
      { url: "/og-image.png", width: 1200, height: 630, alt: "l6e AI" },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "l6e AI - Portable AI Agents",
    description:
      "Create AI agents that run anywhere. Build once, deploy everywhere.",
    images: ["/twitter-image.png"],
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${inter.variable} ${jbMono.variable} antialiased`}
      >
        {children}
      </body>
    </html>
  );
}
