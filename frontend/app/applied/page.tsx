export default function AppliedPage() {
  return (
    <main className="page-shell">
      <a className="back-link" href="/">← Beranda</a>
      <h1>Lamaran kamu</h1>
      <p className="page-sub">
        Lacak status setiap peluang yang sudah kamu daftari, dari terkirim sampai hasil.
      </p>
      <div className="empty-state">
        <h3>Belum ada lamaran.</h3>
        <p>Tandai peluang sebagai &ldquo;apply&rdquo; untuk mulai melacak statusnya di sini.</p>
      </div>
    </main>
  );
}
