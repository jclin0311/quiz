/** Brush-stroke circle (ensō) that fills with progress. Always left slightly open. */
export default function Enso({ value, total, size = 180, children }: { value: number; total: number; size?: number; children?: React.ReactNode }) {
  const r = 42;
  const c = 2 * Math.PI * r;
  const frac = total ? Math.min(1, value / total) : 0;
  // A completed circle still leaves a small gap, as an ensō does.
  const drawn = frac * 0.94 * c;
  return (
    <div style={{ position: "relative", width: size, height: size, margin: "0 auto" }}>
      <svg viewBox="0 0 100 100" width={size} height={size} aria-hidden="true">
        <defs>
          <filter id="brush" x="-10%" y="-10%" width="120%" height="120%">
            <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed="3" />
            <feDisplacementMap in="SourceGraphic" scale="1.6" />
          </filter>
        </defs>
        <circle cx="50" cy="50" r={r} fill="none" stroke="var(--track)" strokeWidth="1" />
        {drawn > 0 && <g transform="rotate(-80 50 50)" filter="url(#brush)">
          <circle cx="50" cy="50" r={r} fill="none" stroke="var(--ink)" strokeWidth="4.2" strokeLinecap="round"
            strokeDasharray={`${drawn} ${c}`} style={{ transition: "stroke-dasharray 1.2s ease" }} />
          <circle cx="50" cy="50" r={r - 1.6} fill="none" stroke="var(--ink)" strokeOpacity=".35" strokeWidth="1.2" strokeLinecap="round"
            strokeDasharray={`${drawn * 0.9} ${c}`} />
        </g>}
      </svg>
      <div style={{ position: "absolute", inset: 0, display: "grid", placeItems: "center", textAlign: "center" }}>{children}</div>
    </div>
  );
}
