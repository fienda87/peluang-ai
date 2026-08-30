"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";

const NAV = [
  { href: "/", label: "Peluang" },
  { href: "/explore", label: "Jelajah" },
  { href: "/saved", label: "Tersimpan" },
  { href: "/applied", label: "Lamaran" },
  { href: "/profile", label: "Profil" },
  { href: "/settings", label: "Pipeline" },
  { href: "/dashboard", label: "Command" },
];

export default function Sidebar() {
  const path = usePathname();
  const [clock, setClock] = useState("--:--");
  const [apiUp, setApiUp] = useState(false);

  useEffect(() => {
    const t = setInterval(
      () =>
        setClock(
          new Date().toLocaleTimeString("id-ID", {
            timeZone: "Asia/Jakarta",
            hour: "2-digit",
            minute: "2-digit",
            hour12: false,
          })
        ),
      1000
    );
    const check = () =>
      fetch("http://localhost:8000/healthz")
        .then((r) => setApiUp(r.ok))
        .catch(() => setApiUp(false));
    check();
    const h = setInterval(check, 15000);
    return () => {
      clearInterval(t);
      clearInterval(h);
    };
  }, []);

  const isActive = (href: string) =>
    href === "/" ? path === "/" : path.startsWith(href);

  return (
    <aside className="sidebar">
      <Link href="/" className="sb-brand">
        <span className="sb-mark">P</span>
        <span className="sb-name">
          Peluang<span className="sb-dot">.ai</span>
        </span>
      </Link>

      <nav className="sb-nav">
        {NAV.map((n) => (
          <Link
            key={n.href}
            href={n.href}
            className={isActive(n.href) ? "sb-item active" : "sb-item"}
          >
            <span className="sb-bullet" />
            {n.label}
          </Link>
        ))}
      </nav>

      <div className="sb-foot">
        <span className="sb-sys">
          <i className={apiUp ? "dot up" : "dot"} />
          {apiUp ? "sistem hidup" : "api mati"}
        </span>
        <span className="sb-clock">{clock} WIB</span>
      </div>
    </aside>
  );
}
