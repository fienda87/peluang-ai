"use client";

import { useEffect, useRef, useState } from "react";

type Ev = { id: number; t: string; level: string; msg: string; ts: string };
type Agent = {
  agent: string;
  runs_24h: number;
  success_rate: number | null;
  last: { status: string | null; steps: number; max_steps: number; llm: number; max_llm: number; started_at: string | null };
};

const FILTERS = ["semua", "crawl", "extract", "opp", "dedup", "error"] as const;

function matchFilter(ev: Ev, f: string) {
  if (f === "semua") return true;
  if (f === "error") return ev.level === "error";
  if (f === "opp") return ev.t.startsWith("opp.");
  if (f === "extract") return ev.t.startsWith("extract");
  return ev.t.startsWith("crawl");
}

function relTime(iso: string) {
  const d = new Date(iso);
  const diff = Math.round((Date.now() - d.getTime()) / 1000);
  if (diff < 60) return `${diff}s lalu`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m lalu`;
  return `${Math.floor(diff / 3600)}j lalu`;
}

function wibClock() {
  return new Date().toLocaleTimeString("id-ID", { timeZone: "Asia/Jakarta", hour12: false });
}

export default function DashboardPage() {
  const [events, setEvents] = useState<Ev[]>([]);
  const [filter, setFilter] = useState<string>("semua");
  const [agents, setAgents] = useState<Agent[]>([]);
  const [sys, setSys] = useState({ api: false });
  const [clock, setClock] = useState("--:--:--");
  const [auto, setAuto] = useState<boolean | null>(null);
  const [running, setRunning] = useState(false);
  const boxRef = useRef<HTMLDivElement>(null);

  // clock WIB
  useEffect(() => {
    const t = setInterval(() => setClock(wibClock()), 1000);
    return () => clearInterval(t);
  }, []);

  // health poll
  useEffect(() => {
    const check = () =>
      fetch("http://localhost:8000/healthz")
        .then((r) => setSys({ api: r.ok }))
        .catch(() => setSys({ api: false }));
    check();
    const t = setInterval(check, 10000);
    return () => clearInterval(t);
  }, []);

  // SSE stream
  useEffect(() => {
    const es = new EventSource("http://localhost:8000/pipeline/stream");
    es.onmessage = (m) => {
      try {
        const ev: Ev = JSON.parse(m.data);
        setEvents((prev) => [...prev.slice(-499), ev]);
      } catch {}
    };
    es.onerror = () => {};
    return () => es.close();
  }, []);

  // agents poll
  useEffect(() => {
    const load = () =>
      fetch("http://localhost:8000/pipeline/agents/status")
        .then((r) => r.json())
        .then((d) => setAgents(d.agents || []))
        .catch(() => {});
    load();
    const t = setInterval(load, 5000);
    return () => clearInterval(t);
  }, []);

  // schedule state
  useEffect(() => {
    fetch("http://localhost:8000/admin/pipeline/schedule")
      .then((r) => r.json())
      .then((d) => setAuto(d.auto_daily))
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (boxRef.current) boxRef.current.scrollTop = boxRef.current.scrollHeight;
  }, [events]);

  async function runNow() {
    setRunning(true);
    try {
      await fetch("http://localhost:8000/admin/pipeline/run-now", { method: "POST" });
    } catch {}
    setTimeout(() => setRunning(false), 4000);
  }

  async function toggleAuto() {
    const next = !(auto ?? false);
    setAuto(next);
    await fetch("http://localhost:8000/admin/pipeline/schedule", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ enable: next }),
    }).catch(() => {});
  }

  const visible = events.filter((e) => matchFilter(e, filter));
  const lastCrawl = [...events].reverse().find((e) => e.t.startsWith("crawl."));
  const isBusyNow =
    lastCrawl && !["run.summary"].includes(lastCrawl.t) && Date.now() - new Date(lastCrawl.ts).getTime() < 120000;
  const nowMsg = isBusyNow ? lastCrawl?.msg : null;

  const storedCount = events.filter((e) => e.t === "crawl.stored").length;
  const oppCount = events.filter((e) => e.t === "opp.created").length;
  const errCount = events.filter((e) => e.level === "error").length;

  return (
    <main className="cc-shell">
      {/* Header */}
      <div className="cc-header">
        <div className="cc-brand">
          <span className="brand-mark">P</span> peluang.ai — command center
        </div>
        <div className="sys-dots">
          <span>
            <i className={`dot ${sys.api ? "up" : ""}`} />api
          </span>
          <b>{clock} WIB</b>
        </div>
      </div>

      <div className="cc-grid">
        {/* Stream */}
        <section className="stream-panel">
          <div className="stream-head">
            <span className="stream-title">▌ pipeline stream</span>
            <div className="chips">
              {FILTERS.map((f) => (
                <button
                  key={f}
                  className={`chip ${filter === f ? "on" : ""}`}
                  onClick={() => setFilter(f)}
                >
                  {f}
                </button>
              ))}
            </div>
          </div>

          {nowMsg && (
            <div className="now-line">
              <span>NOW:</span> {nowMsg}
            </div>
          )}

          <div className="stream-box" ref={boxRef}>
            {visible.length === 0 && (
              <div style={{ color: "#4a5e70" }}>
                menunggu event… tekan ▶ RUN untuk memulai pipeline.
              </div>
            )}
            {visible.map((ev) => {
              const time = new Date(ev.ts).toLocaleTimeString("id-ID", { hour12: false });
              const cls =
                ev.level === "success"
                  ? "s-success"
                  : ev.level === "warn"
                    ? "s-warn"
                    : ev.level === "error"
                      ? "s-error"
                      : "s-info";
              return (
                <div key={ev.id} className={`s-line ${cls}`}>
                  <span className="s-time">{time}</span>
                  {ev.t === "opp.created" ? (
                    <span className="opp-card-inline" style={{ display: "inline-block" }}>
                      {ev.msg}
                    </span>
                  ) : (
                    <span className="s-msg">{ev.msg}</span>
                  )}
                </div>
              );
            })}
          </div>
        </section>

        {/* Agents */}
        <aside className="agent-stack">
          {agents.map((a) => {
            const stepPct = Math.min(100, Math.round(((a.last.steps || 0) / a.last.max_steps) * 100));
            const llmPct = Math.min(100, Math.round(((a.last.llm || 0) / a.last.max_llm) * 100));
            const live = a.last.status === "running";
            return (
              <div key={a.agent} className="agent-card">
                <div className="agent-name">
                  <span>{a.agent}</span>
                  <span className={`agent-dot ${live ? "live" : ""}`} />
                </div>
                <div className="bar-row">
                  <label>steps</label>
                  <div className="bar">
                    <i className={stepPct >= 80 ? "full" : ""} style={{ width: `${stepPct}%` }} />
                  </div>
                  <span>
                    {a.last.steps}/{a.last.max_steps}
                  </span>
                </div>
                <div className="bar-row">
                  <label>llm</label>
                  <div className="bar">
                    <i className={llmPct >= 80 ? "full" : ""} style={{ width: `${llmPct}%` }} />
                  </div>
                  <span>
                    {a.last.llm}/{a.last.max_llm}
                  </span>
                </div>
                <div className="agent-meta">
                  {a.runs_24h} run/24h ·{" "}
                  {a.success_rate !== null ? `${Math.round(a.success_rate * 100)}% ok` : "—"} ·{" "}
                  {a.last.started_at ? `last ${relTime(a.last.started_at)}` : "belum jalan"}
                </div>
              </div>
            );
          })}
          {agents.length === 0 && (
            <div className="agent-card agent-meta">memuat status agen…</div>
          )}
        </aside>
      </div>

      {/* Strip */}
      <div className="cc-strip">
        <div className="cc-counters">
          <span>docs tersimpan <b>{storedCount}</b></span>
          <span>peluang baru <b>{oppCount}</b></span>
          <span>error <b style={{ color: errCount ? "var(--red)" : "var(--accent)" }}>{errCount}</b></span>
        </div>
        <div style={{ display: "flex", gap: 10 }}>
          <button className="secondary-button" onClick={toggleAuto}>
            auto harian: {auto === null ? "…" : auto ? "ON" : "OFF"}
          </button>
          <button className="primary-button" onClick={runNow} disabled={running}>
            {running ? "menjalankan…" : "▶ RUN"}
          </button>
        </div>
      </div>
    </main>
  );
}
