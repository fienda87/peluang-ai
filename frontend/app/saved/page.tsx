export default function SavedPage() {
  return (
    <main className="page-shell">
      <a className="back-link" href="/">← Beranda</a>
      <h1>Peluang tersimpan</h1>
      <p className="page-sub">
        Semua peluang yang kamu simpan untuk dicek dan dilamar nanti.
      </p>
      <div className="empty-state">
        <h3>Belum ada yang disimpan.</h3>
        <p>
          Simpan peluang dari <a href="/explore" style={{ color: "var(--accent)", fontWeight: 600 }}>halaman jelajah</a> atau
          feed rekomendasi. Fitur simpan aktif setelah login.
        </p>
      </div>
    </main>
  );
}
