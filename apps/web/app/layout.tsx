import "./globals.css";
import { Toaster } from "sonner";
import { AppShell } from "../components/app-shell";
import { ThemeProvider } from "../components/theme-provider";
import { CommandPalette } from "../components/command-palette";
import { cn } from "../lib/utils";

export const metadata = {
  title: "Reklai — AI-рекламный кабинет",
  description: "Умная платформа для создания и управления рекламой с помощью AI",
  icons: {
    icon: "/favicon.png",
    shortcut: "/favicon.png",
    apple: "/favicon.png",
  },
  openGraph: {
    title: "Reklai — AI-рекламный кабинет",
    description: "Умная платформа для создания и управления рекламой с помощью AI",
    siteName: "Reklai",
    locale: "ru_RU",
    type: "website",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ru">
      <body className={cn("font-sans bg-bg text-text")}>
        <ThemeProvider>
          <AppShell>{children}</AppShell>
          <CommandPalette />
        </ThemeProvider>
        <Toaster richColors theme="dark" position="top-right" />
      </body>
    </html>
  );
}
