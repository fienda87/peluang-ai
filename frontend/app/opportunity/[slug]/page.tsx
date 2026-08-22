async function getOpportunity(slug: string) {
  try {
    const res = await fetch(`http://localhost:8000/opportunities?q=${slug}&limit=1`, {
      cache: "no-store",
    });
    if (!res.ok) return null;
    const data = await res.json();
    return data.find((o: any) => o.slug === slug) ?? data[0] ?? null;
  } catch {
    return null;
  }
}

export default async function OpportunityPage({ params }: { params: { slug: string } }) {
  const opp = await getOpportunity(params.slug);

  if (!opp) {
    return (
      <main className="container">
        <h1>Peluang tidak ditemukan</h1>
        <a href="/explore">Kembali ke jelajah</a>
      </main>
    );
  }

  return (
    <main className="container">
      <a href="/explore" className="muted">← Kembali</a>
      <h1>{opp.title}</h1>
      <span className="badge">{opp.category}</span>

      <div className="card" style={{ marginTop: 16 }}>
        <p><strong>Penyelenggara:</strong> {opp.organizer ?? "-"}</p>
        <p><strong>Lokasi:</strong> {opp.location ?? "-"}</p>
        <p><strong>Deadline:</strong> {opp.end_date ?? "-"}</p>
        {opp.prize && <p><strong>Hadiah:</strong> {opp.prize}</p>}
      </div>

      <div style={{ display: "flex", gap: 12, marginTop: 16 }}>
        <button style={{ padding: "10px 20px", borderRadius: 8, background: "#2563eb", color: "#fff", border: "none", cursor: "pointer" }}>
          Simpan
        </button>
        <button style={{ padding: "10px 20px", borderRadius: 8, background: "#16a34a", color: "#fff", border: "none", cursor: "pointer" }}>
          Daftar
        </button>
      </div>
    </main>
  );
}
