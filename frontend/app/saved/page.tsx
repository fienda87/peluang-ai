"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api, getToken } from "../../lib/auth";

type Item = {
  id: string;
  title: string;
  slug: string;
  category: string;
  end_date?: string;
};

export default function SavedPage() {
  const [items, setItems] = useState<Item[] | null>(null);
  const [authed, setAuthed] = useState(true);

  useEffect(() => {
    if (!getToken()) {
      setAuthed(false);
      return;
    }
    api<Item[]>("/profile/saved")
      .then(setItems)
      .catch(() => setAuthed(false));
  }, []);

  return (
    <main className="page-shell">
      <a className="back-link" href="/">← Beranda</a>
      <h1>Peluang tersimpan</h1>
      <p className="page-sub">Semua peluang yang kamu simpan untuk dilamar nanti.</p>

      {!authed && (
        <div className="empty-state">
          <h3>Belum login.</h3>
          <p>
            <Link href="/login" style={{ color: "var(--accent)", fontWeight: 700 }}>
              Masuk dulu
            </Link>{" "}
            untuk menyimpan peluang.
          </p>
        </div>
      )}

      {authed && items && items.length === 0 && (
        <div className="empty-state">
          <h3>Belum ada yang disimpan.</h3>
          <p>Buka detail peluang lalu tekan &ldquo;Simpan&rdquo;.</p>
        </div>
      )}

      {items && items.length > 0 && (
        <div className="opportunity-list">
          {items.map((item) => (
            <article key={item.id} className="feed-card">
              <div className="feed-card-top">
                <span className="category-chip">{item.category}</span>
                <span className="deadline-chip">{item.end_date ?? "-"}</span>
              </div>
              <h3>
                <Link href={`/opportunity/${item.slug}`}>{item.title}</Link>
              </h3>
            </article>
          ))}
        </div>
      )}
    </main>
  );
}
