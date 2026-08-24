import OpportunityActions from "./actions";

type Opportunity = {
  id: string;
  title: string;
  slug: string;
  category: string;
  organizer?: string;
  location?: string;
  end_date?: string;
  prize?: string;
  url?: string;
};

async function getOpportunity(slug: string): Promise<Opportunity | null> {
  try {
    const res = await fetch(
      `http://localhost:8000/opportunities?q=${encodeURIComponent(slug)}&limit=5`,
      { cache: "no-store" }
    );
    if (!res.ok) return null;
    const data: Opportunity[] = await res.json();
    return data.find((o) => o.slug === slug) ?? data[0] ?? null;
  } catch {
    return null;
  }
}

export default async function OpportunityPage({
  params,
}: {
  params: { slug: string };
}) {
  const opp = await getOpportunity(params.slug);

  if (!opp) {
    return (
      <main className="page-shell">
        <a className="back-link" href="/explore">← Kembali ke jelajah</a>
        <div className="empty-state">
          <h3>Peluang tidak ditemukan.</h3>
          <p>Tautan mungkin sudah kedaluwarsa atau peluang belum masuk database.</p>
        </div>
      </main>
    );
  }

  const facts: Array<[string, string]> = [
    ["Kategori", opp.category],
    ["Penyelenggara", opp.organizer ?? "Belum tercatat"],
    ["Lokasi", opp.location ?? "Fleksibel"],
    ["Deadline", opp.end_date ?? "Belum ditentukan"],
    ...(opp.prize ? ([["Hadiah", opp.prize]] as Array<[string, string]>) : []),
  ];

  return (
    <main className="page-shell">
      <a className="back-link" href="/explore">← Kembali ke jelajah</a>

      <span className="category-chip">{opp.category}</span>
      <h1 className="detail-title">{opp.title}</h1>

      <div className="simple-card">
        <dl className="detail-facts">
          {facts.map(([label, value]) => (
            <div key={label}>
              <dt>{label}</dt>
              <dd>{value}</dd>
            </div>
          ))}
        </dl>

        <div className="action-row">
          <OpportunityActions slug={opp.slug} />
          <a
            className="secondary-button"
            href={opp.url || "#"}
            target="_blank"
            rel="noreferrer"
          >
            Buka sumber asli
          </a>
        </div>
      </div>
    </main>
  );
}
