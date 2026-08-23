type Opportunity = {
  id: string;
  title: string;
  slug: string;
  category: string;
  organizer?: string;
  location?: string;
  end_date?: string;
};

async function searchOpportunities(q: string): Promise<Opportunity[]> {
  try {
    const res = await fetch(
      `http://localhost:8000/opportunities?q=${encodeURIComponent(q)}&limit=20`,
      { cache: "no-store" }
    );
    if (!res.ok) return [];
    return await res.json();
  } catch {
    return [];
  }
}

export default async function ExplorePage({
  searchParams,
}: {
  searchParams: { q?: string };
}) {
  const q = searchParams.q ?? "";
  const results = await searchOpportunities(q);

  return (
    <main className="page-shell">
      <a className="back-link" href="/">← Beranda</a>
      <h1>Jelajahi peluang</h1>
      <p className="page-sub">
        Cari beasiswa, lomba, magang, fellowship, dan peluang lain dari seluruh sumber yang sudah masuk pipeline.
      </p>

      <form className="search-form" action="/explore" method="GET">
        <input
          type="text"
          name="q"
          defaultValue={q}
          placeholder="Cari peluang… misalnya beasiswa, magang, riset"
        />
        <button className="primary-button" type="submit">Cari</button>
      </form>

      {q && (
        <p className="result-count">
          {results.length} hasil untuk &ldquo;{q}&rdquo;
        </p>
      )}

      {results.length === 0 ? (
        <div className="empty-state">
          <h3>{q ? "Tidak ada hasil." : "Mulai dengan mencari sesuatu."}</h3>
          <p>
            {q
              ? "Coba kata kunci lain seperti beasiswa, lomba, atau magang."
              : "Data berasal dari pipeline ingestion lokal. Jalankan seed bila database masih kosong."}
          </p>
        </div>
      ) : (
        <div className="opportunity-list">
          {results.map((item) => (
            <article key={item.id} className="feed-card">
              <div className="feed-card-top">
                <span className="category-chip">{item.category}</span>
                <span className="deadline-chip">{item.end_date ?? "Deadline belum pasti"}</span>
              </div>
              <h3>
                <a href={`/opportunity/${item.slug}`}>{item.title}</a>
              </h3>
              <p>
                {item.organizer ?? "Penyelenggara belum tercatat"} · {item.location ?? "Lokasi fleksibel"}
              </p>
            </article>
          ))}
        </div>
      )}
    </main>
  );
}
