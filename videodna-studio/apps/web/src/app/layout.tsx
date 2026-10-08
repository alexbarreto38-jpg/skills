import type { Metadata, Viewport } from "next";

import { Providers } from "./providers";

import "./globals.css";

export const metadata: Metadata = {
  title: "VideoDNA Studio",
  description: "Desmonte, edite e reconstrua vídeos com IA — preservando história, ritmo e câmera.",
};

export const viewport: Viewport = {
  themeColor: "#0a0c11",
  colorScheme: "dark",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR" className="dark">
      <body className="min-h-screen">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
