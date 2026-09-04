import { API_URL } from "../../lib/api";
type Item = {
  id: string;
  title: string;
  slug: string;
  category: string;
  organizer?: string;
  end_date?: string;
};

async function getApplied(): Promise<Item[]> {
  try {
    const res = await fetch(`${API_URL}/profile/applied`, {
      cache: "no-store",
    });
    if (!res.ok) return [];
    return await res.json();
  } catch {
    return [];
  }
}

export default async function AppliedPage() {
  const items = await getApplied();

  return (
    <main className="page-shell">
      <a className="back-link" href="/">← Beranda</a>
      <h1>Lamaran kamu</h1>
      <p className="page-sub">Status setiap peluang yang sudah kamu daftari.</p>

      {items.length === 0 ? (
        <div className="empty-state">
          <h3>Belum ada lamaran.</h3>
          <p>Tekan &ldquo;Tandai Dilamar&rdquo; di halaman peluang untuk mulai melacak.</p>
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
