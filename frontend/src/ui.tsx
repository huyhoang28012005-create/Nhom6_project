import type { ReactNode } from "react";

export const P: Record<string, string> = {
  home: "M3 11l9-8 9 8M5 10v10h14V10",
  cal: "M3 5h18v16H3zM3 10h18M8 3v4M16 3v4",
  search: "M11 19a8 8 0 100-16 8 8 0 000 16zM21 21l-4.3-4.3",
  plus: "M12 5v14M5 12h14",
  user: "M12 12a4 4 0 100-8 4 4 0 000 8zM4 21a8 8 0 0116 0",
  bell: "M6 8a6 6 0 1112 0c0 7 3 9 3 9H3s3-2 3-9M10 21h4",
  pin: "M12 21s7-6 7-12a7 7 0 10-14 0c0 6 7 12 7 12zM12 11a2 2 0 100-4 2 2 0 000 4z",
  users: "M16 20v-2a4 4 0 00-4-4H6a4 4 0 00-4 4v2M9 10a4 4 0 100-8 4 4 0 000 8zM22 20v-2a4 4 0 00-3-3.9",
  proj: "M3 4h18v11H3zM12 15v5M8 20h8",
  snow: "M12 2v20M4 7l16 10M20 7L4 17",
  plug: "M9 2v6M15 2v6M6 8h12v4a6 6 0 01-12 0zM12 18v4",
  wifi: "M2 9a15 15 0 0120 0M5 13a10 10 0 0114 0M8.5 16.5a5 5 0 017 0M12 20h.01",
  hist: "M3 12a9 9 0 109-9 9 9 0 00-7 3L3 8M3 3v5h5M12 7v5l3 2",
  warn: "M12 3l10 18H2zM12 10v5M12 18h.01",
  help: "M12 22a10 10 0 100-20 10 10 0 000 20zM9 9a3 3 0 115 2c-1 .7-2 1-2 3M12 17h.01",
  out: "M9 21H4V3h5M16 17l5-5-5-5M21 12H9",
  down: "M12 3v12M7 10l5 5 5-5M4 21h16",
  check: "M20 6L9 17l-5-5",
  x: "M18 6L6 18M6 6l12 12",
  img: "M3 3h18v18H3zM8.5 10a1.5 1.5 0 100-3 1.5 1.5 0 000 3zM21 15l-5-5L5 21",
  grid: "M3 3h8v8H3zM13 3h8v8h-8zM3 13h8v8H3zM13 13h8v8h-8z",
  list: "M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01",
  lock: "M5 11h14v10H5zM8 11V7a4 4 0 118 0v4",
  clock: "M12 22a10 10 0 100-20 10 10 0 000 20zM12 6v6l4 2",
  grad: "M22 10L12 5 2 10l10 5zM6 12v5c3 2 9 2 12 0v-5",
  bolt: "M13 2L3 14h8l-1 8 10-12h-8l1-8z",
  chart: "M4 20h16M7 16v-5M12 16V6M17 16v-8",
  shield: "M12 2l8 4v6c0 5.5-3.8 9.7-8 10-4.2-.3-8-4.5-8-10V6l8-4z",
  cog: "M12 15a3 3 0 100-6 3 3 0 000 6zM19.4 15a1.7 1.7 0 00.3 1.8l.1.1a2 2 0 11-2.8 2.8l-.1-.1a1.7 1.7 0 00-1.8-.3 1.7 1.7 0 00-1 1.5V21a2 2 0 11-4 0v-.1a1.7 1.7 0 00-1-1.5 1.7 1.7 0 00-1.8.3l-.1.1a2 2 0 11-2.8-2.8l.1-.1a1.7 1.7 0 00.3-1.8 1.7 1.7 0 00-1.5-1H3a2 2 0 110-4h.1a1.7 1.7 0 001.5-1 1.7 1.7 0 00-.3-1.8l-.1-.1a2 2 0 112.8-2.8l.1.1a1.7 1.7 0 001.8.3h.1a1.7 1.7 0 001-1.5V3a2 2 0 114 0v.1a1.7 1.7 0 001 1.5 1.7 1.7 0 001.8-.3l.1-.1a2 2 0 112.8 2.8l-.1.1a1.7 1.7 0 00-.3 1.8v.1a1.7 1.7 0 001.5 1H21a2 2 0 110 4h-.1a1.7 1.7 0 00-1.5 1z",
  swap: "M16 3l4 4-4 4M20 7H4M8 21l-4-4 4-4M4 17h16",
  trash: "M3 6h18M8 6V4h8v2M6 6l1 14h10l1-14",
};

export const I = ({ n, s = 20, c = "" }: { n: string; s?: number; c?: string }) => (
  <svg width={s} height={s} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className={c}>
    <path d={P[n] || P.grid} />
  </svg>
);

export const U = (id: string) => `https://images.unsplash.com/${id}?auto=format&fit=crop&w=900&q=70`;
export const IMG = {
  campus: U("photo-1562774053-701939374585"),
  hall: U("photo-1580582932707-520aed937b7b"),
  room: U("photo-1509062522246-3755977927d7"),
  lab: U("photo-1581092160562-40aa08e78837"),
  group: U("photo-1522202176988-66273c2fd55f"),
  lib: U("photo-1521587760476-6c12a4b040da"),
};

export function roomImageByType(roomType?: string | null): string {
  if (roomType === "hall") return IMG.hall;
  if (roomType === "lab") return IMG.lab;
  if (roomType === "group") return IMG.group;
  return IMG.room;
}

export function roomTypeLabel(roomType?: string | null): string {
  if (roomType === "hall") return "Giảng đường";
  if (roomType === "lab") return "Phòng Lab máy tính";
  if (roomType === "group") return "Phòng học nhóm";
  return "Phòng học tiêu chuẩn";
}

export const Photo = ({ src, c = "" }: { src: string; c?: string }) => (
  <img
    src={src}
    alt=""
    loading="lazy"
    onError={(e) => (e.currentTarget.style.visibility = "hidden")}
    className={`bg-gradient-to-br from-navy to-brand object-cover ${c}`}
  />
);

export const Btn = ({
  v = "p",
  children,
  onClick,
  disabled,
  loading,
  type = "button",
  className = "",
}: {
  v?: "p" | "s" | "g";
  children: ReactNode;
  onClick?: () => void;
  disabled?: boolean;
  loading?: boolean;
  type?: "button" | "submit";
  className?: string;
}) => (
  <button
    type={type}
    onClick={onClick}
    disabled={disabled || loading}
    className={`inline-flex h-11 items-center justify-center gap-2 rounded-xl px-4 text-sm font-semibold transition focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand disabled:cursor-not-allowed disabled:opacity-50 ${
      v === "p"
        ? "bg-navy text-white hover:bg-blue-900 active:scale-[.98]"
        : v === "s"
          ? "border border-slate-300 bg-white text-navy hover:bg-slate-50"
          : "text-navy hover:bg-blue-50"
    } ${className}`}
  >
    {loading && <span className="size-4 animate-spin rounded-full border-2 border-current/35 border-t-current" />}
    {children}
  </button>
);

export const Card = ({ children, className = "" }: { children: ReactNode; className?: string }) => (
  <div className={`rounded-2xl bg-white p-6 shadow-[0_4px_20px_rgba(30,58,138,.07)] ${className}`}>{children}</div>
);

const toneMap: Record<string, string> = {
  g: "bg-green-100 text-green-800",
  r: "bg-red-100 text-red-800",
  y: "bg-yellow-100 text-yellow-800",
  x: "bg-slate-200 text-slate-700",
  b: "bg-blue-100 text-blue-800",
};

export const Chip = ({ t, children }: { t: string; children: ReactNode }) => (
  <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-[12.5px] font-medium ${toneMap[t] || toneMap.x}`}>
    {children}
  </span>
);

export const Field = ({ label, error, children }: { label: string; error?: string; children: ReactNode }) => (
  <label className="block text-sm font-semibold text-ink">
    {label}
    <div className="mt-1.5">{children}</div>
    {error && <p className="mt-1 text-[13px] font-normal text-red-600">{error}</p>}
  </label>
);

export const inp =
  "h-11 w-full rounded-xl border border-slate-200 bg-white px-3 text-sm outline-none focus:border-brand focus:ring-2 focus:ring-brand/30";

export const Empty = ({ t, d }: { t: string; d: string }) => (
  <div className="flex flex-col items-center py-10 text-center">
    <svg width="120" height="96" viewBox="0 0 120 96" fill="none">
      <ellipse cx="60" cy="86" rx="40" ry="6" fill="#E2E8F0" />
      <rect x="20" y="18" width="80" height="58" rx="10" fill="#DBEAFE" />
      <rect x="32" y="32" width="40" height="6" rx="3" fill="#3B82F6" />
      <rect x="32" y="46" width="56" height="6" rx="3" fill="#93C5FD" />
      <circle cx="92" cy="22" r="12" fill="#F59E0B" />
      <path d="M87 22h10M92 17v10" stroke="#fff" strokeWidth="2.5" strokeLinecap="round" />
    </svg>
    <h3 className="mt-3 font-semibold">{t}</h3>
    <p className="text-sm text-mute">{d}</p>
  </div>
);

export const ToastBanner = ({ t, m }: { t: "r" | "a" | "g"; m: string }) => (
  <div
    role="status"
    className={`flex items-center gap-2 rounded-xl px-4 py-3 text-sm font-medium shadow-lg ${
      t === "r" ? "bg-red-600 text-white" : t === "a" ? "bg-amber text-ink" : "bg-green-600 text-white"
    }`}
  >
    <I n={t === "g" ? "check" : "warn"} s={16} />
    {m}
  </div>
);
