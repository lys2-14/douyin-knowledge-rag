"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { getSessionId, clearSessionId } from "@/lib/api";

const links = [
  { href: "/favorites", label: "\u6536\u85cf\u5939", icon: "\ud83d\udcc1" },
  { href: "/knowledge", label: "\u77e5\u8bc6\u5e93", icon: "\ud83d\udcda" },
  { href: "/chat", label: "\u5bf9\u8bdd", icon: "\ud83d\udcac" },
];

export default function NavBar() {
  const path = usePathname();
  const router = useRouter();
  const sid = getSessionId();
  if (!sid) return null;

  return (
    <aside className="fixed left-0 top-0 h-full w-56 bg-gray-900 border-r border-gray-800 flex flex-col z-40">
      {/* Logo */}
      <div className="p-5 border-b border-gray-800">
        <Link href="/favorites" className="text-lg font-bold text-white hover:text-indigo-400 transition-colors">
          Knowledge RAG
        </Link>
        <p className="text-xs text-gray-500 mt-1">v0.1.0</p>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-3 space-y-1">
        {links.map((l) => (
          <Link
            key={l.href}
            href={l.href}
            className={
              "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors " +
              (path.startsWith(l.href)
                ? "bg-indigo-500/15 text-indigo-400 font-medium"
                : "text-gray-400 hover:text-white hover:bg-gray-800")
            }
          >
            <span className="text-lg">{l.icon}</span>
            <span>{l.label}</span>
          </Link>
        ))}
      </nav>

      {/* User / Logout */}
      <div className="p-3 border-t border-gray-800">
        <button
          className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-gray-500 hover:text-red-400 hover:bg-gray-800 transition-colors w-full"
          onClick={() => {
            clearSessionId();
            router.replace("/login");
          }}
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
          </svg>
          <span>\u9000\u51fa\u767b\u5f55</span>
        </button>
      </div>
    </aside>
  );
}
