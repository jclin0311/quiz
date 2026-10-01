/**
 * Small, safe SVG templates that illustrate an approach. Keyed by the choice's
 * `visual` field. Deliberately neutral: a visual never hints at correctness.
 */
import type { ReactNode } from "react";

const A = "var(--accent)";
const S = "currentColor";

function Cells({ n = 6, y = 14, w = 9, gap = 2, x0 = 2, hl = [] as number[], hl2 = [] as number[] }) {
  return (
    <>
      {Array.from({ length: n }, (_, i) => (
        <rect
          key={i}
          x={x0 + i * (w + gap)}
          y={y}
          width={w}
          height={w}
          rx={2}
          fill={hl.includes(i) ? A : hl2.includes(i) ? "var(--good)" : "none"}
          fillOpacity={hl.includes(i) || hl2.includes(i) ? 0.85 : 0}
          stroke={S}
          strokeWidth={1.3}
        />
      ))}
    </>
  );
}

const Arrow = ({ x1, y1, x2, y2, c = S }: { x1: number; y1: number; x2: number; y2: number; c?: string }) => {
  const a = Math.atan2(y2 - y1, x2 - x1);
  const h = 3.2;
  return (
    <g stroke={c} strokeWidth={1.4} fill="none" strokeLinecap="round">
      <line x1={x1} y1={y1} x2={x2} y2={y2} />
      <path d={`M${x2 - h * Math.cos(a - 0.5)} ${y2 - h * Math.sin(a - 0.5)} L${x2} ${y2} L${x2 - h * Math.cos(a + 0.5)} ${y2 - h * Math.sin(a + 0.5)}`} />
    </g>
  );
};

const Node = ({ x, y, r = 4, f = false }: { x: number; y: number; r?: number; f?: boolean }) => (
  <circle cx={x} cy={y} r={r} fill={f ? A : "var(--card)"} stroke={f ? A : S} strokeWidth={1.3} />
);

const Tree = ({ hl = [] as number[] }) => {
  const pts = [[34, 6], [20, 20], [48, 20], [12, 34], [28, 34], [40, 34], [56, 34]];
  const edges = [[0, 1], [0, 2], [1, 3], [1, 4], [2, 5], [2, 6]];
  return (
    <>
      {edges.map(([a, b], i) => (
        <line key={i} x1={pts[a][0]} y1={pts[a][1]} x2={pts[b][0]} y2={pts[b][1]} stroke={S} strokeWidth={1.2} />
      ))}
      {pts.map(([x, y], i) => <Node key={i} x={x} y={y} f={hl.includes(i)} />)}
    </>
  );
};

const Graph = ({ hl = [] as number[], weighted = false }) => {
  const pts = [[8, 22], [26, 8], [26, 36], [46, 14], [58, 32]];
  const edges = [[0, 1], [0, 2], [1, 3], [2, 3], [3, 4], [2, 4]];
  return (
    <>
      {edges.map(([a, b], i) => (
        <line key={i} x1={pts[a][0]} y1={pts[a][1]} x2={pts[b][0]} y2={pts[b][1]} stroke={S} strokeWidth={weighted ? (i % 3) + 0.8 : 1.2} />
      ))}
      {pts.map(([x, y], i) => <Node key={i} x={x} y={y} f={hl.includes(i)} />)}
    </>
  );
};

const VISUALS: Record<string, ReactNode> = {
  hashmap: (
    <>
      {[0, 1, 2].map((i) => (
        <g key={i}>
          <rect x={4} y={4 + i * 12} width={14} height={9} rx={2} fill="none" stroke={S} strokeWidth={1.3} />
          <Arrow x1={20} y1={8.5 + i * 12} x2={32} y2={8.5 + i * 12} />
          <rect x={35} y={4 + i * 12} width={22} height={9} rx={2} fill={i === 1 ? A : "none"} fillOpacity={0.85} stroke={S} strokeWidth={1.3} />
        </g>
      ))}
    </>
  ),
  set: (
    <>
      <circle cx={32} cy={20} r={16} fill="none" stroke={S} strokeWidth={1.3} strokeDasharray="3 2" />
      <Node x={24} y={15} f /><Node x={38} y={13} /><Node x={30} y={27} /><Node x={41} y={25} />
    </>
  ),
  "two-pointers": (
    <>
      <Cells n={6} y={20} hl={[0, 5]} />
      <Arrow x1={6} y1={6} x2={6} y2={17} c={A} />
      <Arrow x1={62} y1={6} x2={62} y2={17} c={A} />
      <Arrow x1={14} y1={36} x2={26} y2={36} />
      <Arrow x1={54} y1={36} x2={42} y2={36} />
    </>
  ),
  "fast-slow": (
    <>
      <circle cx={40} cy={20} r={13} fill="none" stroke={S} strokeWidth={1.3} />
      <line x1={2} y1={20} x2={27} y2={20} stroke={S} strokeWidth={1.3} />
      <Node x={14} y={20} /><Node x={40} y={7} f /><Node x={52} y={27} f />
      <text x={36} y={24} fontSize={7} fill={S}>×2</text>
    </>
  ),
  "sliding-window": (
    <>
      <Cells n={6} y={16} hl={[1, 2, 3]} />
      <rect x={12} y={12} width={35} height={17} rx={4} fill="none" stroke={A} strokeWidth={1.8} />
      <Arrow x1={30} y1={36} x2={46} y2={36} c={A} />
    </>
  ),
  "binary-search": (
    <>
      <Cells n={6} y={10} hl={[2]} />
      <path d="M2 26 h64" stroke={S} strokeWidth={1.2} />
      <path d="M2 26 v4 M35 26 v4 M66 26 v4" stroke={S} strokeWidth={1.2} />
      <rect x={2} y={32} width={32} height={5} rx={2} fill={A} fillOpacity={0.8} />
    </>
  ),
  sort: (
    <>
      {[10, 16, 22, 28, 34, 40].map((h, i) => (
        <rect key={i} x={4 + i * 10} y={40 - h} width={7} height={h} rx={1.5} fill={i === 5 ? A : "none"} fillOpacity={0.85} stroke={S} strokeWidth={1.2} />
      ))}
    </>
  ),
  brute: (
    <>
      {Array.from({ length: 16 }, (_, i) => (
        <rect key={i} x={14 + (i % 4) * 10} y={2 + Math.floor(i / 4) * 10} width={8} height={8} rx={1.5}
          fill={i % 5 === 0 ? A : "none"} fillOpacity={0.8} stroke={S} strokeWidth={1.1} />
      ))}
    </>
  ),
  prefix: (
    <>
      <Cells n={6} y={6} />
      <Cells n={6} y={24} hl={[0, 1, 2]} />
      {[0, 1, 2, 3, 4].map((i) => <Arrow key={i} x1={6 + i * 11} y1={17} x2={15 + i * 11} y2={23} />)}
    </>
  ),
  "array-copy": (
    <>
      <Cells n={5} y={6} x0={8} />
      <Cells n={5} y={26} x0={8} hl={[0, 1, 2, 3, 4]} />
      <Arrow x1={34} y1={16} x2={34} y2={25} />
    </>
  ),
  counting: (
    <>
      {[["a", 3], ["b", 1], ["c", 2]].map(([k, v], i) => (
        <g key={i}>
          <text x={6} y={11 + i * 12} fontSize={8} fill={S} fontFamily="monospace">{k}</text>
          <rect x={16} y={4 + i * 12} width={(v as number) * 14} height={8} rx={2} fill={A} fillOpacity={0.8} />
        </g>
      ))}
    </>
  ),
  math: (
    <text x={32} y={27} textAnchor="middle" fontSize={17} fontStyle="italic" fill={S} fontFamily="Georgia, serif">f(x)=Σ</text>
  ),
  bits: (
    <>
      {"10110".split("").map((b, i) => (
        <g key={i}>
          <rect x={4 + i * 12} y={10} width={10} height={14} rx={2} fill={b === "1" ? A : "none"} fillOpacity={0.85} stroke={S} strokeWidth={1.2} />
          <text x={9 + i * 12} y={34} textAnchor="middle" fontSize={7} fill={S} fontFamily="monospace">{b}</text>
        </g>
      ))}
    </>
  ),
  stack: (
    <>
      {[0, 1, 2, 3].map((i) => (
        <rect key={i} x={20} y={30 - i * 8} width={24} height={7} rx={2} fill={i === 3 ? A : "none"} fillOpacity={0.85} stroke={S} strokeWidth={1.2} />
      ))}
      <path d="M17 4 v35 h30 V4" fill="none" stroke={S} strokeWidth={1.3} />
      <Arrow x1={56} y1={14} x2={56} y2={4} c={A} />
    </>
  ),
  "monotonic-stack": (
    <>
      {[30, 24, 18, 12].map((h, i) => (
        <rect key={i} x={8 + i * 10} y={38 - h} width={8} height={h} rx={1.5} fill="none" stroke={S} strokeWidth={1.2} />
      ))}
      <rect x={50} y={4} width={8} height={34} rx={1.5} fill={A} fillOpacity={0.85} />
      <Arrow x1={48} y1={10} x2={40} y2={16} c={A} />
    </>
  ),
  queue: (
    <>
      <Cells n={5} y={15} x0={10} hl={[0]} />
      <Arrow x1={8} y1={20} x2={0.5} y2={20} c={A} />
      <Arrow x1={70} y1={20} x2={64} y2={20} />
    </>
  ),
  heap: (
    <>
      <Tree hl={[0]} />
    </>
  ),
  "linked-list": (
    <>
      {[0, 1, 2, 3].map((i) => (
        <g key={i}>
          <rect x={2 + i * 17} y={14} width={10} height={10} rx={2.5} fill={i === 0 ? A : "none"} fillOpacity={0.85} stroke={S} strokeWidth={1.3} />
          {i < 3 && <Arrow x1={13 + i * 17} y1={19} x2={18 + i * 17} y2={19} />}
        </g>
      ))}
    </>
  ),
  recursion: (
    <>
      {[0, 1, 2, 3].map((i) => (
        <rect key={i} x={4 + i * 6} y={4 + i * 6} width={56 - i * 12} height={32 - i * 6} rx={4} fill="none" stroke={i === 3 ? A : S} strokeWidth={1.3} />
      ))}
    </>
  ),
  "tree-dfs": (
    <>
      <Tree hl={[0, 1, 3]} />
    </>
  ),
  "tree-bfs": (
    <>
      <Tree hl={[1, 2]} />
      <line x1={4} y1={20} x2={62} y2={20} stroke={A} strokeWidth={1.2} strokeDasharray="2 2" />
    </>
  ),
  trie: (
    <>
      <Node x={32} y={5} />
      {[[16, "c"], [48, "d"]].map(([x, ch], i) => (
        <g key={i}>
          <line x1={32} y1={5} x2={x as number} y2={19} stroke={S} strokeWidth={1.2} />
          <Node x={x as number} y={19} r={5} f={i === 0} />
          <text x={x as number} y={21.5} textAnchor="middle" fontSize={7} fill={i === 0 ? "#fff" : S}>{ch}</text>
        </g>
      ))}
      {[8, 24].map((x, i) => (
        <g key={i}>
          <line x1={16} y1={19} x2={x} y2={34} stroke={S} strokeWidth={1.2} />
          <Node x={x} y={34} />
        </g>
      ))}
      <line x1={48} y1={19} x2={48} y2={34} stroke={S} strokeWidth={1.2} /><Node x={48} y={34} />
    </>
  ),
  backtrack: (
    <>
      <Tree hl={[0, 2, 5]} />
      <path d="M8 30 l8 8 M16 30 l-8 8" stroke="var(--bad)" strokeWidth={1.4} opacity={0.8} />
    </>
  ),
  "graph-bfs": (
    <>
      <circle cx={8} cy={22} r={12} fill={A} fillOpacity={0.12} />
      <circle cx={8} cy={22} r={22} fill="none" stroke={A} strokeOpacity={0.4} strokeDasharray="2 2" />
      <Graph hl={[0]} />
    </>
  ),
  "graph-dfs": <Graph hl={[0, 1, 3, 4]} />,
  "union-find": (
    <>
      <Node x={16} y={8} f /><Node x={8} y={30} /><Node x={24} y={30} />
      <Arrow x1={9} y1={26} x2={14} y2={12} /><Arrow x1={23} y1={26} x2={18} y2={12} />
      <Node x={48} y={8} f /><Node x={48} y={30} />
      <Arrow x1={48} y1={26} x2={48} y2={13} />
    </>
  ),
  topo: (
    <>
      {[0, 1, 2, 3].map((i) => <Node key={i} x={8 + i * 16} y={i % 2 ? 30 : 12} f={i === 0} />)}
      <Arrow x1={12} y1={14} x2={21} y2={27} /><Arrow x1={28} y1={27} x2={37} y2={15} />
      <Arrow x1={44} y1={15} x2={53} y2={27} /><Arrow x1={12} y1={12} x2={36} y2={12} />
    </>
  ),
  dijkstra: (
    <>
      <Graph hl={[0, 1, 3]} weighted />
    </>
  ),
  "dp-1d": (
    <>
      <Cells n={6} y={18} hl={[5]} hl2={[3, 4]} />
      <path d="M40 16 q6 -10 14 0 M29 16 q12 -18 25 0" fill="none" stroke={S} strokeWidth={1.2} />
    </>
  ),
  "dp-2d": (
    <>
      {Array.from({ length: 12 }, (_, i) => (
        <rect key={i} x={12 + (i % 4) * 11} y={4 + Math.floor(i / 4) * 11} width={9} height={9} rx={1.5}
          fill={i === 10 ? A : i === 6 || i === 9 ? "var(--good)" : "none"} fillOpacity={0.8} stroke={S} strokeWidth={1.1} />
      ))}
    </>
  ),
  greedy: (
    <>
      <path d="M4 36 L18 24 L30 28 L44 12 L60 6" fill="none" stroke={S} strokeWidth={1.4} />
      {[[18, 24], [44, 12], [60, 6]].map(([x, y], i) => <Node key={i} x={x} y={y} r={3} f />)}
    </>
  ),
  intervals: (
    <>
      {[[4, 26, 0], [18, 22, 1], [44, 18, 2]].map(([x, w, r], i) => (
        <rect key={i} x={x} y={6 + r * 11} width={w} height={7} rx={3.5} fill={i < 2 ? A : "none"} fillOpacity={0.8} stroke={S} strokeWidth={1.2} />
      ))}
    </>
  ),
  matrix: (
    <>
      {Array.from({ length: 9 }, (_, i) => (
        <rect key={i} x={18 + (i % 3) * 10} y={4 + Math.floor(i / 3) * 10} width={8} height={8} rx={1.5}
          fill={i % 4 === 0 ? A : "none"} fillOpacity={0.8} stroke={S} strokeWidth={1.1} />
      ))}
      <path d="M52 8 a10 10 0 0 1 0 22" fill="none" stroke={S} strokeWidth={1.3} />
      <Arrow x1={53} y1={29} x2={49} y2={31} />
    </>
  ),
};

export default function ApproachVisual({ kind }: { kind: string }) {
  return (
    <svg viewBox="0 0 68 42" width="100%" height="100%" preserveAspectRatio="xMinYMid meet" aria-hidden="true">
      {VISUALS[kind] ?? VISUALS.math}
    </svg>
  );
}
