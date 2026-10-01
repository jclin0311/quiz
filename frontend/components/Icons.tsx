type P = { size?: number };
const base = (size: number) => ({
  width: size,
  height: size,
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 1.4,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
  "aria-hidden": true,
});

export const ChevronLeft = ({ size = 26 }: P) => (
  <svg {...base(size)}><path d="M15 5l-7 7 7 7" /></svg>
);
export const More = ({ size = 24 }: P) => (
  <svg {...base(size)} strokeWidth={0} fill="currentColor"><circle cx="5" cy="12" r="2" /><circle cx="12" cy="12" r="2" /><circle cx="19" cy="12" r="2" /></svg>
);
export const ImageIcon = ({ size = 26 }: P) => (
  <svg {...base(size)}><rect x="3" y="3" width="18" height="18" rx="5" /><circle cx="9" cy="9" r="1.8" /><path d="M3.5 17l5-5 4 4 3-3 5 5" /></svg>
);
export const Bulb = ({ size = 26 }: P) => (
  <svg {...base(size)}><path d="M9 18h6M10 21h4" /><path d="M12 3a6 6 0 0 0-3.5 10.9c.6.5 1 1.2 1 2V16h5v-.1c0-.8.4-1.5 1-2A6 6 0 0 0 12 3z" /></svg>
);
export const Speaker = ({ size = 26 }: P) => (
  <svg {...base(size)}><path d="M4 9.5v5h3.5L13 19V5L7.5 9.5z" /><path d="M16.5 9a4 4 0 0 1 0 6M19 6.5a7.5 7.5 0 0 1 0 11" /></svg>
);
export const HomeIcon = ({ size = 24 }: P) => (
  <svg {...base(size)}><path d="M4 11l8-7 8 7v8a2 2 0 0 1-2 2h-3v-6h-6v6H6a2 2 0 0 1-2-2z" /></svg>
);
export const ChartIcon = ({ size = 24 }: P) => (
  <svg {...base(size)}><path d="M4 20V10M10 20V4M16 20v-7M22 20H2" /></svg>
);
export const UserIcon = ({ size = 24 }: P) => (
  <svg {...base(size)}><circle cx="12" cy="8" r="4" /><path d="M4 21c1.5-4 4.5-6 8-6s6.5 2 8 6" /></svg>
);
export const Check = ({ size = 16 }: P) => (
  <svg {...base(size)} strokeWidth={2.6}><path d="M5 12.5l4.5 4.5L19 7.5" /></svg>
);
export const Cross = ({ size = 16 }: P) => (
  <svg {...base(size)} strokeWidth={2.6}><path d="M6 6l12 12M18 6L6 18" /></svg>
);
