import "../styles/globals.css";
import Link from "next/link";

export const metadata = {
  title: "Ads Admin",
  description: "Ads aggregator admin panel"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen">
        <div className="max-w-5xl mx-auto px-6 py-6">
          <header className="flex items-center justify-between mb-6">
            <div className="text-xl font-semibold">Ads Admin</div>
            <nav className="flex gap-4 text-sm text-slate-300">
              <Link href="/login">Login</Link>
              <Link href="/orgs">Orgs</Link>
              <Link href="/connections">Connections</Link>
              <Link href="/sync-runs">Sync Runs</Link>
              <Link href="/metrics">Metrics</Link>
              <Link href="/plans/new">Plans</Link>
              <Link href="/experiments">Experiments</Link>
            </nav>
          </header>
          {children}
        </div>
      </body>
    </html>
  );
}
