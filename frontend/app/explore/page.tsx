async function searchOpportunities(q: string) {
  try {
    const res = await fetch(`http://localhost:8000/opportunities?q=${encodeURIComponent(q)}&limit=20`, {
      cache: "no-store",
    });
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
    <main className="container">
      <h1>Jelajahi Peluang</h1>
      <form action="/explore" method="GET" style={{ marginBottom: 20 }}>
        <input
          type="text"
          name="q"
          defaultValue={q}
          placeholder="Cari beasiswa, lomba, magang..."
          style={{ padding: "10px 14px", width: "100%", borderRadius: 8, border: "1px solid #d1d5db" }}
        />
      </form>

      {results.length === 0 && <p className="muted">Tidak ada hasil.</p>}

      {results.map((item: any) => (
        <div key={item.id} className="card">
          <h2>
            <a href={`/opportunity/${item.slug}`}>{item.title}</a>
          </h2>
          <span className="badge">{item.category}</span>
          <p className="muted">
            {item.organizer} · {item.location} · Deadline: {item.end_date ?? "N/A"}
          </p>
        </div>
      ))}
    </main>
  );
}
