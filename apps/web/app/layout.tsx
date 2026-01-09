import "../styles/globals.css";
import { Toaster } from "sonner";
import { AppShell } from "../components/app-shell";

export const metadata = {
  title: "Рекламный кабинет",
  description: "Панель управления рекламой"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ru">
      <body className="font-sans">
        <AppShell>{children}</AppShell>
        <Toaster richColors theme="dark" position="top-right" />
      </body>
    </html>
  );
}
