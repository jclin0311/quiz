"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Bar, BarChart, CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import BottomNav from "@/components/BottomNav";
import Dolphin from "@/components/Dolphin";
import TopicGraph from "@/components/TopicGraph";
import { api, DashboardStats, TopicGraph as Graph } from "@/lib/api";

const axis = { fontSize: 11, fill: "var(--muted)" };
const tooltipStyle = {
  contentStyle: {
    background: "var(--card-strong)", border: "none", borderRadius: 12, boxShadow: "0 6px 24px rgba(0,0,0,.12)",
    fontSize: 13, color: "var(--ink)",
  },
  labelStyle: { color: "var(--muted)", marginBottom: 2 },
  itemStyle: { color: "var(--ink)" },
  cursor: { fill: "var(--chart-grid)" },
};

const shortDate = (iso: string) => {
  const [, m, d] = iso.split("-");
  return `${Number(m)}/${Number(d)}`;
};

function TableView({ headers, rows }: { headers: string[]; rows: (string | number)[][] }) {
  return (
    <details className="small" style={{ marginTop: 8 }}>
      <summary className="muted" style={{ cursor: "pointer" }}>Table</summary>
      <table style={{ width: "100%", borderCollapse: "collapse", marginTop: 6 }}>
        <thead><tr>{headers.map((h) => <th key={h} style={{ textAlign: "left", padding: "4px 6px", color: "var(--muted)" }}>{h}</th>)}</tr></thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i} style={{ borderTop: "1px solid var(--line)" }}>
              {r.map((c, j) => <td key={j} style={{ padding: "4px 6px" }}>{c}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </details>
  );
}

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [graph, setGraph] = useState<Graph | null>(null);
  const [analysis, setAnalysis] = useState<{ text: string; source: string } | null>(null);
  const [analysisError, setAnalysisError] = useState(false);
  const [topic, setTopic] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api<DashboardStats>("/dashboard").then(setStats).catch((e) => setError(e.message));
    api<Graph>("/topics/graph").then(setGraph).catch(() => {});
    // The narrative refreshes whenever the underlying stats change (cached server-side by stats hash).
    api<{ text: string; source: string }>("/dashboard/analysis").then(setAnalysis).catch(() => setAnalysisError(true));
  }, []);

  const weeklyTopics = useMemo(() => (stats ? Object.keys(stats.weekly_topic_accuracy) : []), [stats]);
  // Default to the weakest topic with data.
  useEffect(() => {
    if (!stats || topic) return;
    const weakest = [...stats.topic_accuracy].sort((a, b) => a.accuracy - b.accuracy)[0];
    if (weakest) setTopic(weakest.topic);
  }, [stats, topic]);

  if (error) return <main className="shell wide"><p className="error">{error}</p><BottomNav /></main>;
  if (!stats) return <main className="shell wide"><p className="muted">Loading…</p><BottomNav /></main>;

  const t = stats.totals;
  const names = Object.fromEntries(stats.topic_accuracy.map((x) => [x.topic, x.name]));
  const weekly = topic ? (stats.weekly_topic_accuracy[topic] ?? []).map((w) => ({ ...w, label: shortDate(w.week) })) : [];
  const perDay = stats.per_day.map((d) => ({ ...d, label: shortDate(d.date) }));
  const weekDelta =
    t.this_week_accuracy !== null && t.last_week_accuracy !== null ? Math.round(t.this_week_accuracy - t.last_week_accuracy) : null;

  return (
    <main className="shell wide">
      <h1 className="h1" style={{ margin: "6px 0 28px" }}>Progress</h1>

      <div className="stats plain" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(130px, 1fr))", gap: "18px 0", marginBottom: 28 }}>
        <div className="card stat"><div className="v">{t.answered}</div><div className="l">answered</div></div>
        <div className="card stat"><div className="v">{t.accuracy ?? "–"}{t.accuracy !== null && "%"}</div><div className="l">accuracy</div></div>
        <div className="card stat"><div className="v">{t.streak}</div><div className="l">streak</div></div>
        <div className="card stat">
          <div className="v">{t.this_week_answered}</div>
          <div className="l">
            this week
            {weekDelta !== null && (
              <span style={{ color: weekDelta >= 0 ? "var(--good)" : "var(--bad)", fontWeight: 700 }}>
                {" "}{weekDelta >= 0 ? "▲" : "▼"} {Math.abs(weekDelta)} pts
              </span>
            )}
          </div>
        </div>
      </div>

      <div className="card" style={{ marginBottom: 14 }}>
        <div className="row" style={{ alignItems: "flex-start" }}>
          <Dolphin size={56} mood={analysis ? "happy" : "think"} />
          <div style={{ flex: 1 }}>
                        <p style={{ margin: 0, lineHeight: 1.55, fontSize: 15 }}>
              {analysis?.text ?? (analysisError ? "Unavailable" : "…")}
            </p>
            {analysis?.source === "llm" && (
              <p className="small muted" style={{ margin: "8px 0 0" }}>
                {analysis.source === "llm" ? "AI" : ""}
              </p>
            )}
          </div>
        </div>
      </div>

      {t.answered === 0 ? (
        <div className="card muted">No data yet</div>
      ) : (
        <div className="stack">
          <section className="card">
            <h2 className="h2">By topic</h2>
            <div style={{ width: "100%", height: Math.max(120, stats.topic_accuracy.length * 30 + 30) }}>
              <ResponsiveContainer>
                <BarChart data={stats.topic_accuracy} layout="vertical" margin={{ left: 0, right: 16, top: 4, bottom: 4 }}>
                  <CartesianGrid horizontal={false} stroke="var(--chart-grid)" />
                  <XAxis type="number" domain={[0, 100]} tickFormatter={(v) => `${v}%`} tick={axis} axisLine={false} tickLine={false} />
                  <YAxis type="category" dataKey="name" width={138} tick={{ ...axis, fill: "var(--ink-2)" }} axisLine={false} tickLine={false} />
                  <Tooltip {...tooltipStyle} formatter={(v, _n, p) => [`${v}% (${p.payload.correct}/${p.payload.attempts})`, ""]} />
                  <Bar dataKey="accuracy" fill="var(--chart)" barSize={14} radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
            <TableView headers={["Topic", "Answered", "Correct", "Accuracy"]}
              rows={stats.topic_accuracy.map((x) => [x.name, x.attempts, x.correct, `${x.accuracy}%`])} />
          </section>

          <section className="card">
            <h2 className="h2">Last 30 days</h2>
            <div className="chart-wrap" style={{ height: 220 }}>
              <ResponsiveContainer>
                <LineChart data={perDay} margin={{ left: -18, right: 12, top: 8, bottom: 0 }}>
                  <CartesianGrid vertical={false} stroke="var(--chart-grid)" />
                  <XAxis dataKey="label" tick={axis} axisLine={false} tickLine={false} interval="preserveStartEnd" minTickGap={24} />
                  <YAxis allowDecimals={false} tick={axis} axisLine={false} tickLine={false} />
                  <Tooltip {...tooltipStyle} cursor={{ stroke: "var(--muted)", strokeDasharray: "3 3" }}
                    formatter={(v, _n, p) => [`${v} · ${p.payload.correct} correct`, ""]} separator="" />
                  <Line type="monotone" dataKey="answered" stroke="var(--chart)" strokeWidth={2} dot={false} activeDot={{ r: 4, strokeWidth: 2, stroke: "var(--card)" }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
            <TableView headers={["Date", "Answered", "Correct"]}
              rows={stats.per_day.filter((d) => d.answered).map((d) => [d.date, d.answered, d.correct])} />
          </section>

          <section className="card">
            <div className="row" style={{ justifyContent: "space-between", flexWrap: "wrap", marginBottom: 10 }}>
              <h2 className="h2" style={{ margin: 0 }}>Weekly</h2>
              <select value={topic ?? ""} onChange={(e) => setTopic(e.target.value)} aria-label="Topic"
                style={{ font: "inherit", fontSize: 14, padding: "6px 10px", borderRadius: 10, border: "1px solid var(--line)", background: "var(--card-strong)", color: "var(--ink)" }}>
                {weeklyTopics.map((id) => <option key={id} value={id}>{names[id] ?? id}</option>)}
              </select>
            </div>
            <div className="chart-wrap" style={{ height: 220 }}>
              <ResponsiveContainer>
                <BarChart data={weekly} margin={{ left: -18, right: 12, top: 8, bottom: 0 }}>
                  <CartesianGrid vertical={false} stroke="var(--chart-grid)" />
                  <XAxis dataKey="label" tick={axis} axisLine={false} tickLine={false} />
                  <YAxis domain={[0, 100]} tickFormatter={(v) => `${v}%`} tick={axis} axisLine={false} tickLine={false} />
                  <Tooltip {...tooltipStyle}
                    labelFormatter={(l) => l}
                    formatter={(v, _n, p) => [v === null ? "–" : `${v}% of ${p.payload.attempts}`, ""]} />
                  <Bar dataKey="accuracy" fill="var(--chart)" barSize={22} radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
            <TableView headers={["Week of", "Answered", "Accuracy"]}
              rows={weekly.filter((w) => w.attempts).map((w) => [w.week, w.attempts, `${w.accuracy}%`])} />
          </section>
        </div>
      )}

      {graph && (
        <section className="card" style={{ marginTop: 14 }}>
          <h2 className="h2">Roadmap</h2>
          <TopicGraph graph={graph} />
        </section>
      )}

      <BottomNav />
    </main>
  );
}
