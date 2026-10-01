type Mood = "happy" | "cheer" | "think";

export default function Dolphin({ size = 72, mood = "happy" }: { size?: number; mood?: Mood }) {
  return (
    <svg width={size} height={size} viewBox="0 0 120 120" role="img" aria-label="Dolphin mascot">
      {/* water splash */}
      <path d="M14 100 q12 -8 24 0 t24 0 t24 0 t24 0" fill="none" stroke="var(--dolphin)" strokeOpacity=".3" strokeWidth="2" strokeLinecap="round" />
      {/* tail */}
      <path d="M22 70 C10 62 8 50 12 44 C18 52 24 56 32 58 Z" fill="var(--dolphin)" />
      <path d="M22 70 C14 80 14 90 18 94 C22 84 28 78 36 74 Z" fill="var(--dolphin)" />
      {/* body */}
      <path
        d="M28 66 C34 42 58 28 80 30 C94 31 104 40 108 50 C110 55 112 58 116 60 C112 63 106 64 100 64 C92 76 72 86 52 84 C40 83 30 78 28 66 Z"
        fill="var(--dolphin)"
      />
      {/* belly */}
      <path d="M48 80 C62 84 82 78 96 66 C86 70 66 74 50 72 Z" fill="var(--dolphin-belly)" />
      {/* dorsal fin */}
      <path d="M62 33 C62 22 68 14 76 12 C74 20 74 26 78 31 Z" fill="var(--dolphin)" />
      {/* flipper */}
      <path d="M64 74 C62 84 56 90 50 92 C54 86 56 80 56 74 Z" fill="var(--dolphin)" opacity=".9" />
      {/* eye */}
      {mood === "cheer" ? (
        <path d="M86 45 q3 -4 6 0" stroke="var(--dolphin-belly)" strokeWidth="2.4" fill="none" strokeLinecap="round" />
      ) : (
        <>
          <circle cx="89" cy="46" r="3.2" fill="var(--dolphin-belly)" />
        </>
      )}
      {/* smile */}
      <path
        d={mood === "think" ? "M100 58 q-5 1 -9 0" : "M102 57 q-6 5 -12 2"}
        stroke="var(--dolphin-belly)"
        strokeWidth="2"
        fill="none"
        strokeLinecap="round"
      />

      {mood === "think" && (
        <g fill="var(--dolphin)" opacity=".5">
          <circle cx="104" cy="28" r="3" />
          <circle cx="110" cy="18" r="4.5" />
        </g>
      )}
    </svg>
  );
}
