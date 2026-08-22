async function getFeed() {
  try {
    const res = await fetch("http://localhost:8000/recommendations?limit=20", {
      cache: "no-store",
    });
    if (!res.ok) return [];
    return await res.json();
  } catch {
    return [];
  }
}

export default async function HomePage() {
  const feed = await getFeed();

  return (
    <main className="container">
      <h1>Peluang.ai</h1>
      <p className="muted">Rekomendasi peluang terbaik untukmu</p>

      {feed.length === 0 && (
        <div className="card">
          <p>Belum ada rekomendasi. Login dan generate rekomendasi dulu.</p>
        </div>
      )}

      {feed.map((item: any) => (
        <div key={item.opportunity_id} className="card">
          <div style={{ display: "flex", justifyContent: "space-between" }}>
            <h2>
              <a href={`/opportunity/${item.slug}`}>{item.title}</a>
            </h2>
            <span className="score">{item.score.toFixed(2)}</span>
          </div>
          <span className="badge">{item.category}</span>
          <p className="muted">
            {item.organizer} · Deadline: {item.end_date ?? "N/A"}
          </p>
          {item.reasoning?.reason && <p>{item.reasoning.reason}</p>}
        </div>
      ))}
    </main>
  );
}
