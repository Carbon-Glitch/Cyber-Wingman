import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Cyber Wingman",
  description: "AI Dating Assistant",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased bg-neutral-950 font-sans">
        {children}
      </body>
    </html>
  );
}
