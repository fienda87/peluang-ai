type Opportunity = {
  id: string;
  title: string;
  slug: string;
  category: string;
  organizer?: string;
  location?: string;
  end_date?: string;
  prize?: string;
};

async function getOpportunities(): Promise<Opportunity[]> {
  try {
    const res = await fetch("http://localhost:8000/opportunities?limit=12", { cache: "no-store" });
    if (!res.ok) return [];
    return await res.json();
  } catch {
    return [];
  }
}

const categoryLabels: Record<string, string> = {
  beasiswa: "Beasiswa",
  lomba: "Lomba",
  magang: "Magang",
  fellowship: "Fellowship",
  konferensi: "Konferensi",
  volunteer: "Volunteer",
  pelatihan: "Pelatihan",
  riset: "Riset",
  kompetisi: "Kompetisi",
};

function daysLeft(endDate?: string) {
  if (!endDate) return "Deadline belum pasti";
  const diff = Math.ceil((new Date(endDate).getTime() - Date.now()) / 86_400_000);
  if (diff < 0) return "Expired";
  if (diff === 0) return "Hari ini";
  return `${diff} hari lagi`;
}

function formatShort(iso?: string) {
  if (!iso) return "Belum ada";
  return new Date(iso).toLocaleDateString("id-ID", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

export default async function HomePage() {
  const opportunities = await getOpportunities();
  const featured = opportunities.slice(0, 6);
  const activeCount = opportunities.length;
  const categoryCount = new Set(opportunities.map((item) => item.category)).size;
  const soonest = formatShort(opportunities.find((item) => item.end_date)?.end_date);

  return (
    <main className="app-shell">
      <nav className="topbar">
        <a className="brand-lockup" href="/">
          <span className="brand-mark">P</span>
          <span>Peluang.ai</span>
        </a>
        <div className="nav-pills">
          <a href="/dashboard">Dashboard</a>
          <a href="/explore">Explore</a>
          <a href="/saved">Saved</a>
          <a href="/applied">Applied</a>
          <a href="/profile">Profile</a>
        </div>
        <a className="topbar-cta" href="/explore">Cari peluang</a>
      </nav>

      <section className="hero-dashboard">
        <div className="hero-copy-block">
          <div className="status-row">
            <span className="live-dot" /> Local beta running
          </div>
          <h1>Peluang yang pantas masuk waktumu.</h1>
          <p>
            Satu ruang kerja untuk menemukan, mengecek eligibility, menyimpan, dan mengejar peluang mahasiswa Indonesia.
          </p>
          <div className="hero-actions">
            <a className="primary-button" href="/explore">Jelajahi</a>
            <a className="secondary-button" href="/profile">Lengkapi profil</a>
          </div>
        </div>

        <aside className="control-panel">
          <div className="panel-header">
            <span>Opportunity intelligence</span>
            <strong>Beta</strong>
          </div>
          <div className="stats-grid">
            <div className="stat-card stat-primary">
              <strong>{activeCount}</strong>
              <span>Peluang aktif</span>
            </div>
            <div className="stat-card">
              <strong>{categoryCount}</strong>
              <span>Kategori</span>
            </div>
            <div className="stat-card">
              <strong>{soonest}</strong>
              <span>Deadline terdekat</span>
            </div>
          </div>
          <div className="pipeline-list">
            <div><span /> Deterministic extraction</div>
            <div><span /> LLM fallback</div>
            <div><span /> Three-state eligibility</div>
          </div>
        </aside>
      </section>

      <section className="content-grid">
        <div className="main-column">
          <div className="section-title-row">
            <div>
              <h2>Peluang terbaru</h2>
              <p>Seed data lokal sudah masuk. Rekomendasi personal muncul setelah login dan generate feed.</p>
            </div>
            <a href="/explore">Lihat semua</a>
          </div>

          {featured.length === 0 ? (
            <div className="empty-state premium-empty">
              <h3>Database masih kosong.</h3>
              <p>Jalankan <code>make seed</code> atau ingestion pipeline untuk mengisi peluang.</p>
            </div>
          ) : (
            <div className="opportunity-list">
              {featured.map((item, index) => (
                <article key={item.id} className={index === 0 ? "feed-card feed-card-featured" : "feed-card"}>
                  <div className="feed-card-top">
                    <span className="category-chip">{categoryLabels[item.category] ?? item.category}</span>
                    <span className="deadline-chip">{daysLeft(item.end_date)}</span>
                  </div>
                  <h3><a href={`/opportunity/${item.slug}`}>{item.title}</a></h3>
                  <p>{item.organizer ?? "Penyelenggara belum tercatat"}</p>
                  <div className="feed-card-bottom">
                    <span>{item.location ?? "Lokasi fleksibel"}</span>
                    <a href={`/opportunity/${item.slug}`}>Detail</a>
                  </div>
                </article>
              ))}
            </div>
          )}
        </div>

        <aside className="side-column">
          <div className="side-card">
            <h3>Next actions</h3>
            <a href="/profile">Isi profil akademik</a>
            <a href="/explore">Browse semua peluang</a>
            <a href="/saved">Cek saved list</a>
          </div>
          <div className="side-card dark-card">
            <span>Pipeline</span>
            <strong>Web + PDF + image</strong>
            <p>Parser murah dulu. Vision dan LLM hanya jadi fallback.</p>
          </div>
        </aside>
      </section>
    </main>
  );
}
