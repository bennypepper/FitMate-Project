import type { Metadata } from "next";
import { Inter, Source_Serif_4, Noto_Sans_SC } from "next/font/google";
import TopAppBar from "@/components/layout/TopAppBar";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

const sourceSerif = Source_Serif_4({
  variable: "--font-serif",
  subsets: ["latin"],
  weight: ["500", "600", "700"],
});

const notoSansSC = Noto_Sans_SC({
  variable: "--font-noto-sans-sc",
  subsets: ["latin"],
  weight: ["400", "500", "700"],
});

export const metadata: Metadata = {
  title: "FitMate TCM: Pindai Label dan Cek Keamanan Produk Herbal",
  description: "FitMate membantu membaca label komposisi obat tradisional China (TCM), menerjemahkan aksara Hanzi, dan mencocokkannya dengan daftar bahan resmi BPOM.",
  manifest: "/manifest.json",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="id"
      className={`${inter.variable} ${sourceSerif.variable} ${notoSansSC.variable} h-full antialiased`}
    >
      <head>
        <link
          href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="font-body bg-paper-deep text-ink min-h-screen flex flex-col selection:bg-trust-tint selection:text-trust-deep">
        <TopAppBar />
        <main className="flex-1 flex flex-col">{children}</main>
        <script
          dangerouslySetInnerHTML={{
            __html: `
              if (typeof window !== 'undefined' && 'serviceWorker' in navigator) {
                navigator.serviceWorker.register('/sw.js');
              }
            `,
          }}
        />
      </body>
    </html>
  );
}
