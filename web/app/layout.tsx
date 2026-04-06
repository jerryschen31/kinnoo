import type { Metadata } from "next";
import MainLayout from "../components/blocks/MainLayout";
import "./globals.css";

export const metadata: Metadata = {
  title: "kinnoo",
  description: "Package and share your AI agents",
  icons: {
    icon: "/icon",
    shortcut: "/icon",
    apple: "/icon",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full">
        <MainLayout>{children}</MainLayout>
      </body>
    </html>
  );
}
