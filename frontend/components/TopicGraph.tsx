"use client";

import { useState } from "react";
import { topicLabel, type TopicGraph as Graph } from "@/lib/api";

const W = 100;
const H = 108;
const NODE_W = 30;
const NODE_H = 8.4;

/** Roadmap of topics with a mastery bar per node, laid out from the seed coordinates. */
export default function TopicGraph({ graph }: { graph: Graph }) {
  const [active, setActive] = useState<string | null>(null);
  const byId = Object.fromEntries(graph.nodes.map((n) => [n.id, n]));
  const current = active ? byId[active] : null;

  return (
    <div>
      <svg viewBox={`-3 -5 ${W + 8} ${H + 8}`} width="100%" role="img" aria-label="Topic roadmap with mastery per topic">
        {graph.edges.map((e) => {
          const a = byId[e.from];
          const b = byId[e.to];
          const y1 = a.y + NODE_H / 2;
          const y2 = b.y - NODE_H / 2;
          const my = (y1 + y2) / 2;
          return (
            <path
              key={`${e.from}-${e.to}`}
              d={`M${a.x} ${y1} C${a.x} ${my} ${b.x} ${my} ${b.x} ${y2}`}
              fill="none"
              stroke="var(--muted)"
              strokeOpacity={active && active !== e.from && active !== e.to ? 0.15 : 0.45}
              strokeWidth={0.35}
            />
          );
        })}
        {graph.nodes.map((n) => {
          const pct = n.mastery ?? 0;
          const mastered = n.mastery !== null && n.mastery >= 65 && n.attempts >= 3;
          return (
            <g
              key={n.id}
              transform={`translate(${n.x - NODE_W / 2} ${n.y - NODE_H / 2})`}
              onMouseEnter={() => setActive(n.id)}
              onMouseLeave={() => setActive(null)}
              onClick={() => setActive(active === n.id ? null : n.id)}
              style={{ cursor: "pointer" }}
            >
              <rect
                width={NODE_W}
                height={NODE_H}
                rx={1.6}
                fill={mastered ? "var(--good-soft)" : "var(--card-strong)"}
                stroke={active === n.id ? "var(--accent)" : mastered ? "var(--good)" : "var(--line)"}
                strokeWidth={active === n.id ? 0.5 : 0.3}
              />
              <text x={NODE_W / 2} y={4} textAnchor="middle" fontSize={2.8} fontWeight={600} fill="var(--ink)">
                {topicLabel(n.id, n.name)}
              </text>
              <rect x={1.6} y={NODE_H - 2.4} width={NODE_W - 3.2} height={1.1} rx={0.55} fill="var(--track)" />
              <rect x={1.6} y={NODE_H - 2.4} width={((NODE_W - 3.2) * pct) / 100} height={1.1} rx={0.55} fill="var(--good)" />
            </g>
          );
        })}
      </svg>
      <p className="small muted" style={{ minHeight: 20, margin: "6px 0 0" }}>
        {current
          ? `${current.name} · ${current.mastery === null ? "–" : `${current.mastery}%`} · ${current.attempts}/${current.questions}`
          : ""}
      </p>
    </div>
  );
}
