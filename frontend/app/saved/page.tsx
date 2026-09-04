import { API_URL } from "../../lib/api";
type Item = {
  id: string;
  title: string;
  slug: string;
  category: string;
  organizer?: string;
  end_date?: string;
};

async function getSaved(): Promise<Item[]> {
  try {
    const res = await fetch(`${API_URL}/profile/saved`, {
      cache: "no-store",
    });
    if (!res.ok) return [];
    return await res.json();
  } catch {
    return [];
  }
}

export default async function SavedPage() {
  const items = await getSaved();

  return (
    <main className="page-shell">
      <a className="back-link" href="/">← Beranda</a>
      <h1>Peluang tersimpan</h1>
      <p className="page-sub">Semua peluang yang kamu simpan untuk dilamar nanti.</p>

      {items.length === 0 ? (
        <div className="empty-state">
          <h3>Belum ada yang disimpan.</h3>
          <p>
            Buka detail peluang dari <a href="/explore" style={{ color: "var(--accent)", fontWeight: 600 }}>jelajah</a> lalu
            tekan tombol Simpan.
          </p>
        </div>
      ) : (
        <div className="opportunity-list">
          {items.map((item) => (
            <article key={item.id} className="feed-card">
              <div className="feed-card-top">
                <span className="category-chip">{item.category}</span>
                <span className="deadline-chip">{item.end_date ?? "-"}</span>
              </div>
              <h3>
                <a href={`/opportunity/${item.slug}`}>{item.title}</a>
              </h3>
              <p>{item.organizer ?? "Penyelenggara belum tercatat"}</p>
            </article>
          ))}
        </div>
      )}
    </main>
  );
}
