import type { Metadata, Viewport } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Polyglot — Learn a language between Codex and Claude Code turns",
  description:
    "Turn the pauses between Codex and Claude Code turns into small, private language-learning moments.",
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
    title: "Polyglot — Learn a language while your coding agent works",
    description:
      "One useful word or phrase every few completed Codex or Claude Code turns.",
    type: "website",
    images: [
      "https://raw.githubusercontent.com/Amal-David/polyglot/main/site/public/og-preview.png",
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "Polyglot — Make the waiting teach you something",
    description:
      "Private, token-efficient language learning inside Codex and Claude Code sessions.",
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
