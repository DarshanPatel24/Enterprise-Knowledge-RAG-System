import type { Metadata } from "next";
import type { ReactNode } from "react";

import "./globals.css";

export const metadata: Metadata = {
  title: "EK-RAG Console",
  description: "Local-first enterprise knowledge chat UI for the EK-RAG platform.",
};

export default function RootLayout({
  children,
}: {
  children: ReactNode;
}): React.JSX.Element {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="min-h-screen antialiased">{children}</body>
    </html>
  );
}
