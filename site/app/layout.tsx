import type { Metadata, Viewport } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Polyglot — Ambient language learning for coding agents",
  description:
    "18,235 phrases across 70 language pairs, available as an Agent Skill for Codex, Claude, Hermes, and Pi.",
  keywords: [
    "Agent Skills",
    "Codex",
    "Claude Code",
    "Hermes Agent",
    "Pi coding agent",
    "language learning",
    "vocabulary",
  ],
  openGraph: {
    title: "Polyglot — Learn as you build",
    description:
      "One useful phrase at a time, inside the AI coding tools you already use.",
    type: "website",
    images: [
      "https://raw.githubusercontent.com/Amal-David/polyglot/main/site/public/og-preview.png",
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "Polyglot — Learn as you build",
    description:
      "One useful phrase at a time, inside the AI coding tools you already use.",
    images: [
      "https://raw.githubusercontent.com/Amal-David/polyglot/main/site/public/og-preview.png",
    ],
  },
  icons: {
    icon: "/favicon.svg",
    shortcut: "/favicon.svg",
  },
};

export const viewport: Viewport = {
  themeColor: "#eee9d8",
  colorScheme: "light",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
