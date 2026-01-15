import "./globals.css";
import { IBM_Plex_Sans } from "next/font/google";
import { Toaster } from "sonner";
import { AppShell } from "../components/app-shell";
import { ThemeProvider } from "../components/theme-provider";
import { cn } from "../lib/utils";

export const metadata = {
  title: "Рекламный кабинет",
  description: "Панель управления рекламой"
};

const ibm = IBM_Plex_Sans({
  subsets: ["latin", "cyrillic"],
  weight: ["400", "500", "600", "700"],
  display: "swap",
  variable: "--font-sans",
});

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ru">
      <body className={cn("font-sans bg-bg text-text", ibm.variable)}>
        <ThemeProvider>
          <AppShell>{children}</AppShell>
        </ThemeProvider>
        <Toaster richColors theme="dark" position="top-right" />
      </body>
    </html>
  );
}
