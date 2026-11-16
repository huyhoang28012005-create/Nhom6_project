import { useState, type ReactNode } from "react";

const P: Record<string, string> = {
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
};
const I = ({ n, s = 20, c = "" }: { n: string; s?: number; c?: string }) => (
  <svg width={s} height={s} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className={c}><path d={P[n]} /></svg>
);

const U = (id: string) => `https://images.unsplash.com/${id}?auto=format&fit=crop&w=900&q=70`;
const IMG = {
  campus: U("photo-1562774053-701939374585"),
  hall: U("photo-1580582932707-520aed937b7b"),
  room: U("photo-1509062522246-3755977927d7"),
  lab: U("photo-1581092160562-40aa08e78837"),
  group: U("photo-1522202176988-66273c2fd55f"),
  lib: U("photo-1521587760476-6c12a4b040da"),
};
const Photo = ({ src, c = "" }: { src: string; c?: string }) => (
  <img src={src} alt="" loading="lazy" onError={(e) => (e.currentTarget.style.visibility = "hidden")} className={`bg-gradient-to-br from-navy to-brand object-cover ${c}`} />
);

const Btn = ({ v = "p", children, onClick, disabled, loading, className = "" }: { v?: "p" | "s" | "g"; children: ReactNode; onClick?: () => void; disabled?: boolean; loading?: boolean; className?: string }) => (
  <button onClick={onClick} disabled={disabled || loading} className={`inline-flex h-12 items-center justify-center gap-2 rounded-xl px-5 text-sm font-semibold transition focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand disabled:cursor-not-allowed disabled:opacity-50 ${v === "p" ? "bg-navy text-white hover:bg-blue-900 active:scale-[.98]" : v === "s" ? "border border-slate-300 bg-white text-navy hover:bg-slate-50" : "text-navy hover:bg-blue-50"} ${className}`}>
    {loading && <span className="size-4 animate-spin rounded-full border-2 border-white/40 border-t-white" />}{children}
  </button>
);
const Card = ({ children, className = "" }: { children: ReactNode; className?: string }) => <div className={`rounded-2xl bg-white p-6 shadow-[0_4px_20px_rgba(30,58,138,.07)] ${className}`}>{children}</div>;
const tone: Record<string, string> = { g: "bg-green-100 text-green-800", r: "bg-red-100 text-red-800", y: "bg-yellow-100 text-yellow-800", x: "bg-slate-200 text-slate-700", b: "bg-blue-100 text-blue-800" };
const Chip = ({ t, children }: { t: string; children: ReactNode }) => <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-[13px] font-medium ${tone[t]}`}>{children}</span>;
const Field = ({ label, error, children }: { label: string; error?: string; children: ReactNode }) => (
  <label className="block text-sm font-semibold text-ink">{label}<div className="mt-1.5">{children}</div>{error && <p className="mt-1 text-[13px] text-red-600">{error}</p>}</label>
);
const inp = "h-12 w-full rounded-xl border border-slate-200 bg-white px-3 text-base outline-none focus:border-brand focus:ring-2 focus:ring-brand/30";
const Empty = ({ t, d }: { t: string; d: string }) => (
  <div className="flex flex-col items-center py-10 text-center">
    <svg width="120" height="96" viewBox="0 0 120 96" fill="none"><ellipse cx="60" cy="86" rx="40" ry="6" fill="#E2E8F0" /><rect x="20" y="18" width="80" height="58" rx="10" fill="#DBEAFE" /><rect x="32" y="32" width="40" height="6" rx="3" fill="#3B82F6" /><rect x="32" y="46" width="56" height="6" rx="3" fill="#93C5FD" /><circle cx="92" cy="22" r="12" fill="#F59E0B" /><path d="M87 22h10M92 17v10" stroke="#fff" strokeWidth="2.5" strokeLinecap="round" /></svg>
    <h3 className="mt-3 font-semibold">{t}</h3><p className="text-sm text-mute">{d}</p>
  </div>
);

const rooms = [
  { id: 1, n: "Giảng đường A2-305", loc: "Tòa A2 · Tầng 3 · Phòng 305", type: "Giảng đường", cap: 200, img: IMG.hall, ok: true },
  { id: 2, n: "Phòng học B1-204", loc: "Tòa B1 · Tầng 2 · Phòng 204", type: "Phòng học tiêu chuẩn", cap: 60, img: IMG.room, ok: false },
  { id: 3, n: "Phòng máy C3-101", loc: "Tòa C3 · Tầng 1 · Phòng 101", type: "Phòng máy tính", cap: 45, img: IMG.lab, ok: true },
  { id: 4, n: "Phòng học nhóm TV-12", loc: "Thư viện · Tầng 2 · Phòng 12", type: "Phòng học nhóm", cap: 10, img: IMG.group, ok: true },
  { id: 5, n: "Phòng đọc TV-301", loc: "Thư viện · Tầng 3 · Phòng 301", type: "Phòng thư viện", cap: 24, img: IMG.lib, ok: true },
  { id: 6, n: "Phòng học A1-402", loc: "Tòa A1 · Tầng 4 · Phòng 402", type: "Phòng học tiêu chuẩn", cap: 70, img: IMG.room, ok: false },
];
type R = (typeof rooms)[number];
const Equip = () => <div className="flex gap-3 text-mute"><I n="proj" s={16} /><I n="snow" s={16} /><I n="plug" s={16} /><I n="wifi" s={16} /></div>;
const RoomCard = ({ r, go }: { r: R; go: (p: string, r?: R) => void }) => (
  <Card className="overflow-hidden !p-0 transition hover:shadow-lg">
    <div className="relative"><Photo src={r.img} c="aspect-video w-full" /><span className="absolute left-3 top-3"><Chip t={r.ok ? "g" : "r"}>{r.ok ? "Còn trống" : "Đã kín"}</Chip></span></div>
    <div className="space-y-2 p-4">
      <h3 className="font-semibold">{r.n}</h3>
      <p className="flex items-center gap-1.5 text-[13px] text-mute"><I n="pin" s={14} />{r.loc}</p>
      <div className="flex items-center justify-between text-[13px] text-mute"><span className="flex items-center gap-1.5"><I n="users" s={14} />{r.cap} chỗ</span><Equip /></div>
      <div className="flex gap-2 pt-2"><Btn v="s" className="flex-1" onClick={() => go("detail", r)}>Chi tiết</Btn><Btn className="flex-1" disabled={!r.ok} onClick={() => go("book", r)}>Đặt phòng</Btn></div>
    </div>
  </Card>
);

const classes = [
  { t: "07:00 – 09:30", p: "Tiết 1–3", n: "Cơ sở dữ liệu", code: "INT2211 · 02", r: "A2-305", gv: "TS. Nguyễn Văn An", c: "bg-blue-100 border-brand text-navy" },
  { t: "09:45 – 11:30", p: "Tiết 4–6", n: "Giải tích 2", code: "MAT1101 · 05", r: "B1-204", gv: "PGS. Trần Thị Mai", c: "bg-amber-100 border-amber text-amber-900" },
  { t: "13:00 – 15:30", p: "Tiết 7–9", n: "Thực hành mạng máy tính", code: "INT3304 · 01", r: "C3-101", gv: "ThS. Lê Hoàng Nam", c: "bg-green-100 border-green-600 text-green-900" },
];

const inpL = "h-12 w-full rounded-lg border border-slate-200 bg-white px-3 text-base outline-none transition focus:border-[#B08D57] focus:ring-2 focus:ring-[#B08D57]/25";
function Login({ go }: { go: (p: string) => void }) {
  const [role, setRole] = useState("Sinh viên"); const [email, setEmail] = useState(""); const [pw, setPw] = useState(""); const [load, setLoad] = useState(false);
  return (
    <div className="relative grid min-h-screen overflow-hidden lg:grid-cols-[minmax(380px,20%)_minmax(0,1fr)]">
      <Photo src={U("photo-1789073484062-f97bac5211c7")} c="absolute inset-0 size-full object-cover" /><div className="absolute inset-0 bg-gradient-to-t from-[#0B1220]/90 via-[#0B1220]/55 to-[#0B1220]/35" />
      <div className="relative z-10 flex min-w-0 items-center justify-center p-4 sm:p-8 lg:bg-[#FAF7F2] lg:p-6 lg:shadow-2xl">
        <form onSubmit={(e) => { e.preventDefault(); setLoad(true); setTimeout(() => go(role === "Cán bộ Đào tạo" ? "staff" : "home"), 600); }} className="w-full max-w-[420px] rounded-3xl bg-[#FAF7F2] p-6 shadow-[0_10px_40px_rgba(30,58,138,.12)] lg:max-w-none lg:rounded-none lg:p-0 lg:shadow-none">
          <div className="mx-auto grid size-14 place-items-center rounded-full bg-[#0F172A] text-white"><I n="grad" s={26} /></div>
          <h1 className="mt-3 text-center font-serif text-[30px] font-semibold leading-tight">Phòng học ĐHQG</h1>
          <div className="mx-auto mt-3 h-px w-12 bg-[#B08D57]" /><p className="mt-3 text-center text-sm leading-snug text-mute">Đặt phòng học dễ dàng, nhanh chóng</p>
                    <p className="mt-5 text-sm font-semibold leading-none">I am a</p>
          <div className="mt-1.5 grid grid-cols-3 gap-2">{["Sinh viên", "Giảng viên", "Cán bộ Đào tạo"].map((r) => <button type="button" key={r} onClick={() => setRole(r)} className={`min-h-11 rounded-lg border-2 px-1 text-[13px] leading-tight font-semibold transition ${role === r ? "border-[#1D4ED8] bg-[#1D4ED8] text-white" : "border-slate-200 bg-[#F1F5F9] text-[#475569] hover:bg-slate-200"}`}>{r}</button>)}</div>
          <div className="mt-3 space-y-3"><Field label="Email"><input type="email" className={inpL} value={email} onChange={(e) => setEmail(e.target.value)} placeholder="ban@truong.edu.vn" /></Field>
            <Field label="Password"><input type="password" className={inpL} value={pw} onChange={(e) => setPw(e.target.value)} placeholder="••••••••" /></Field></div>
          <Btn className="mt-6 w-full" loading={load} onClick={() => {}}><I n="out" s={18} />Đăng nhập · Log in</Btn>
          <p className="mt-3 text-center text-[13px] leading-snug text-mute">Tài khoản demo: nhập bất kỳ email và mật khẩu nào</p>
        </form>
      </div>
      <div className="relative z-10 hidden items-end p-12 lg:flex"><p className="max-w-md font-serif text-3xl font-medium leading-snug text-white">Tìm phòng, đặt phòng và theo dõi lịch học ở một nơi.</p></div>
    </div>
  );
}

function Home({ go }: { go: (p: string, r?: R) => void }) {
  return (
    <div className="space-y-6">
      <div className="relative overflow-hidden rounded-xl"><Photo src={IMG.campus} c="absolute inset-0 size-full" /><div className="absolute inset-0 bg-gradient-to-r from-navy via-navy/85 to-brand/60" />
        <div className="relative p-6 text-white md:p-10"><p className="text-sm text-blue-100">Học kỳ 2 · Năm học 2024–2025</p><h1 className="mt-1 text-[32px] font-bold">Xin chào, Nguyễn Minh Anh</h1><p className="mt-1 text-blue-100">Hôm nay bạn có 3 tiết học và 1 lịch đặt phòng sắp tới.</p>
          <div className="mt-5 flex flex-wrap gap-2"><Btn className="!bg-amber !text-ink hover:!bg-amber/90" onClick={() => go("search")}><I n="search" s={18} />Tìm phòng trống</Btn><Btn v="g" className="!text-white hover:!bg-white/10" onClick={() => go("schedule")}>Xem thời khóa biểu</Btn></div></div></div>
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">{[["search", "Tìm phòng", "search"], ["plus", "Đặt phòng", "book"], ["warn", "Báo sự cố", "issue"], ["hist", "Lịch sử", "history"]].map(([i, l, p]) => (
        <button key={p} onClick={() => go(p)} className="flex items-center gap-3 rounded-2xl bg-white p-4 text-left font-semibold shadow-[0_4px_20px_rgba(30,58,138,.07)] transition hover:-translate-y-0.5 hover:shadow-md"><span className="grid size-10 place-items-center rounded-lg bg-blue-50 text-navy"><I n={i} /></span>{l}</button>))}</div>
      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2"><h2 className="mb-4 text-2xl font-semibold">Lịch học hôm nay</h2>
          <div className="space-y-3">{classes.map((c) => (<div key={c.n} className="flex gap-4"><div className="w-24 shrink-0 text-sm"><b>{c.t.split(" – ")[0]}</b><br /><span className="text-[13px] text-mute">{c.p}</span></div><div className={`flex-1 rounded-xl border-l-4 p-3 ${c.c}`}><b>{c.n}</b><p className="text-[13px]">{c.code} · {c.gv}</p><p className="mt-1 flex items-center gap-1 text-[13px]"><I n="pin" s={14} />Giảng đường {c.r}</p></div></div>))}</div></Card>
        <div className="space-y-6">
          <Card><h2 className="mb-3 text-lg font-semibold">Tìm nhanh phòng trống</h2><div className="space-y-3"><input type="date" className={inp} /><select className={inp}><option>Ca 1 (Tiết 1–3)</option><option>Ca 2 (Tiết 4–6)</option></select><Btn className="w-full" onClick={() => go("search")}>Tìm phòng</Btn></div></Card>
          <Card><h2 className="mb-3 text-lg font-semibold">Đặt phòng sắp tới</h2><b>Phòng học nhóm TV-12</b><p className="text-[13px] text-mute">Thứ Sáu, 16:00 – 18:00 · 6 người</p><div className="mt-2"><Chip t="y">Chờ duyệt</Chip></div></Card>
        </div>
      </div>
      <Card><div className="mb-3 flex justify-between"><h2 className="text-2xl font-semibold">Thông báo mới nhất</h2><Btn v="g" onClick={() => go("notif")}>Xem tất cả</Btn></div>{notifs.slice(0, 2).map((n) => <NRow key={n.t} n={n} />)}</Card>
    </div>
  );
}

const days = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7"];
function Schedule() {
  const [v, setV] = useState("Tuần");
  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3"><h1 className="text-[32px] font-bold">Thời khóa biểu</h1><div className="flex gap-2"><div className="flex rounded-xl bg-white p-1 shadow-sm">{["Tuần", "Tháng", "Danh sách"].map((x) => <button key={x} onClick={() => setV(x)} className={`rounded-lg px-3 py-1.5 text-sm font-medium ${v === x ? "bg-navy text-white" : "text-mute"}`}>{x}</button>)}</div><Btn v="s"><I n="down" s={18} />Xuất lịch</Btn></div></div>
      {v === "Tuần" ? (
        <Card className="overflow-x-auto"><div className="grid min-w-[760px] grid-cols-6 gap-3">{days.map((d, i) => (<div key={d} className="space-y-2"><div className="rounded-lg bg-soft py-2 text-center text-sm font-semibold">{d}</div>{classes.filter((_, j) => (i + j) % 2 === 0 || i === 1).map((c) => (<div key={c.n} className={`rounded-lg border-l-4 p-2 text-[13px] ${c.c}`}><b className="block">{c.n}</b>{c.p} · {c.r}<br />{c.gv}</div>))}</div>))}</div></Card>
      ) : v === "Tháng" ? (
        <Card><div className="grid grid-cols-7 gap-1 text-center text-sm">{["T2", "T3", "T4", "T5", "T6", "T7", "CN"].map((d) => <b key={d} className="py-2 text-mute">{d}</b>)}{Array.from({ length: 35 }, (_, i) => <div key={i} className={`h-16 rounded-lg p-1.5 text-left ${i === 9 ? "bg-navy text-white" : "bg-soft"}`}>{i + 1 <= 30 && i + 1}{i % 3 === 0 && i < 30 && <span className="mt-1 block h-1.5 rounded bg-brand" />}</div>)}</div></Card>
      ) : (
        <Card className="space-y-3">{classes.map((c) => <div key={c.n} className={`rounded-xl border-l-4 p-3 ${c.c}`}><b>{c.n}</b> · {c.code}<p className="text-[13px]">{c.p} ({c.t}) · Giảng đường {c.r} · {c.gv}</p></div>)}</Card>
      )}
    </div>
  );
}

function Search({ go }: { go: (p: string, r?: R) => void }) {
  const [view, setView] = useState("grid"); const [q, setQ] = useState(""); const [load] = useState(false);
  const list = rooms.filter((r) => r.n.toLowerCase().includes(q.toLowerCase()));
  return (
    <div className="space-y-5"><h1 className="text-[32px] font-bold">Tìm phòng trống</h1>
      <div className="grid gap-6 lg:grid-cols-[280px_1fr]">
        <Card className="space-y-4 self-start"><h2 className="font-semibold">Bộ lọc</h2>
          <Field label="Tòa nhà"><select className={inp}><option>Tất cả</option><option>A2</option><option>B1</option><option>C3</option></select></Field>
          <Field label="Ngày"><input type="date" className={inp} /></Field>
          <Field label="Ca/Tiết"><select className={inp}><option>Ca 1 (Tiết 1–3)</option><option>Ca 2 (Tiết 4–6)</option></select></Field>
          <Field label="Sức chứa tối thiểu"><input type="number" defaultValue={10} className={inp} /></Field>
          <Field label="Loại phòng"><select className={inp}><option>Tất cả</option><option>Giảng đường</option><option>Phòng máy</option><option>Phòng học nhóm</option></select></Field>
          <div className="space-y-2 text-sm">{["Máy chiếu", "Điều hòa", "Ổ cắm"].map((e) => <label key={e} className="flex items-center gap-2"><input type="checkbox" className="size-4 accent-navy" />{e}</label>)}</div>
        </Card>
        <div className="space-y-4">
          <div className="flex gap-2"><input className={inp} placeholder="Tìm theo tên phòng…" value={q} onChange={(e) => setQ(e.target.value)} />
            <div className="flex rounded-xl bg-white p-1 shadow-sm">{[["grid", "grid"], ["list", "list"]].map(([k, i]) => <button key={k} aria-label={k} onClick={() => setView(k)} className={`rounded-lg px-3 ${view === k ? "bg-navy text-white" : "text-mute"}`}><I n={i} s={18} /></button>)}</div></div>
          {load ? null : list.length === 0 ? <Card><Empty t="Không tìm thấy phòng phù hợp" d="Hãy thử thay đổi bộ lọc hoặc chọn ca khác." /></Card> :
            <div className={view === "grid" ? "grid gap-4 sm:grid-cols-2 xl:grid-cols-3" : "space-y-4"}>{list.map((r) => <RoomCard key={r.id} r={r} go={go} />)}</div>}
        </div>
      </div></div>
  );
}

function Detail({ r, go }: { r: R; go: (p: string, r?: R) => void }) {
  const busy = [1, 2, 6, 7];
  return (
    <div className="space-y-5"><Btn v="g" onClick={() => go("search")}>← Quay lại</Btn>
      <div className="grid gap-6 lg:grid-cols-3">
        <div className="space-y-3 lg:col-span-2"><Photo src={r.img} c="aspect-video w-full rounded-xl" /><div className="grid grid-cols-4 gap-3">{[IMG.hall, IMG.room, IMG.lab, IMG.group].map((s) => <Photo key={s} src={s} c="aspect-video w-full rounded-lg" />)}</div></div>
        <Card className="space-y-3 self-start"><Chip t={r.ok ? "g" : "r"}>{r.ok ? "Còn trống" : "Đã kín"}</Chip><h1 className="text-2xl font-semibold">{r.n}</h1><p className="flex items-center gap-1.5 text-mute"><I n="pin" s={16} />{r.loc}</p><p className="flex items-center gap-1.5 text-mute"><I n="users" s={16} />Sức chứa {r.cap} · {r.type}</p>
          <div className="flex flex-wrap gap-2">{["Máy chiếu", "Điều hòa", "Ổ cắm", "Wi-Fi"].map((e) => <Chip key={e} t="b">{e}</Chip>)}</div><Btn className="w-full" disabled={!r.ok} onClick={() => go("book", r)}>Đặt phòng</Btn></Card>
      </div>
      <Card><h2 className="mb-3 text-2xl font-semibold">Lịch trong ngày</h2><div className="grid grid-cols-6 gap-2 sm:grid-cols-12">{Array.from({ length: 12 }, (_, i) => <div key={i} className={`rounded-lg py-3 text-center text-[13px] font-medium ${busy.includes(i) ? "bg-red-100 text-red-800" : "bg-green-100 text-green-800"}`}>T{i + 1}</div>)}</div>
        <div className="mt-3 flex gap-4 text-[13px] text-mute"><span><i className="mr-1 inline-block size-3 rounded bg-green-500" />Trống</span><span><i className="mr-1 inline-block size-3 rounded bg-red-500" />Đã có lớp</span></div></Card></div>
  );
}

function Book({ r, go, toast }: { r: R; go: (p: string) => void; toast: (m: string) => void }) {
  const steps = ["Chọn ngày", "Chọn ca", "Số người", "Mục đích", "Xác nhận"];
  const [s, setS] = useState(0); const [d, setD] = useState(""); const [ca, setCa] = useState(""); const [n, setN] = useState(""); const [m, setM] = useState(""); const [try_, setTry] = useState(false);
  const errs = [!d && "Vui lòng chọn ngày", !ca && "Vui lòng chọn ca", (!n || +n < 1 ? "Nhập số người hợp lệ" : +n > r.cap ? `Vượt sức chứa (${r.cap})` : ""), m.length < 10 && "Mô tả ít nhất 10 ký tự", ""];
  const next = () => { setTry(true); if (errs[s]) return; setTry(false); if (s === 4) { toast("Đã gửi yêu cầu đặt phòng, chờ duyệt"); go("history"); } else setS(s + 1); };
  const e = try_ ? (errs[s] as string) : "";
  return (
    <div className="space-y-5"><h1 className="text-[32px] font-bold">Đặt phòng</h1>
      <div className="flex gap-1 overflow-x-auto">{steps.map((x, i) => <div key={x} className="flex flex-1 min-w-24 flex-col gap-1"><i className={`h-1.5 rounded ${i <= s ? "bg-navy" : "bg-slate-300"}`} /><span className={`text-[13px] ${i === s ? "font-semibold text-navy" : "text-mute"}`}>{i + 1}. {x}</span></div>)}</div>
      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="space-y-4 lg:col-span-2"><h2 className="text-2xl font-semibold">{steps[s]}</h2>
          {s === 0 && <Field label="Ngày sử dụng" error={e}><input type="date" className={inp} value={d} onChange={(x) => setD(x.target.value)} /></Field>}
          {s === 1 && <div><div className="grid grid-cols-2 gap-2 sm:grid-cols-4">{["Ca 1 · 07:00", "Ca 2 · 09:45", "Ca 3 · 13:00", "Ca 4 · 15:45"].map((c, i) => <button key={c} disabled={i === 1} onClick={() => setCa(c)} className={`rounded-xl border-2 p-3 text-sm font-semibold disabled:cursor-not-allowed disabled:bg-red-50 disabled:text-red-700 ${ca === c ? "border-navy bg-blue-50 text-navy" : "border-slate-200 hover:border-brand"}`}>{c}{i === 1 && <span className="block text-[13px]">Đã kín</span>}</button>)}</div>{e && <p className="mt-1 text-[13px] text-red-600">{e}</p>}</div>}
          {s === 2 && <Field label={`Số người (tối đa ${r.cap})`} error={e}><input type="number" className={`${inp} ${e ? "!border-red-500" : ""}`} value={n} onChange={(x) => setN(x.target.value)} /></Field>}
          {s === 3 && <Field label="Mục đích sử dụng" error={e}><textarea rows={4} className={`${inp} h-auto py-2 ${e ? "!border-red-500" : ""}`} value={m} onChange={(x) => setM(x.target.value)} placeholder="VD: Họp nhóm đồ án môn Cơ sở dữ liệu" /></Field>}
          {s === 4 && <p className="text-mute">Kiểm tra lại thông tin ở thẻ tóm tắt rồi nhấn “Gửi yêu cầu”.</p>}
          <div className="flex justify-between pt-2"><Btn v="s" disabled={s === 0} onClick={() => setS(s - 1)}>Quay lại</Btn><Btn onClick={next}>{s === 4 ? "Gửi yêu cầu" : "Tiếp tục"}</Btn></div></Card>
        <Card className="space-y-2 self-start"><Photo src={r.img} c="aspect-video w-full rounded-lg" /><h3 className="font-semibold">{r.n}</h3><p className="flex items-center gap-1.5 text-[13px] text-mute"><I n="pin" s={14} />{r.loc}</p>
          <dl className="space-y-1 text-sm">{[["Ngày", d || "—"], ["Ca", ca || "—"], ["Số người", n || "—"]].map(([a, b]) => <div key={a} className="flex justify-between"><dt className="text-mute">{a}</dt><dd className="font-medium">{b}</dd></div>)}</dl></Card>
      </div></div>
  );
}

const hist = [
  { r: "Phòng học nhóm TV-12", d: "16/05/2025 · 16:00–18:00", s: "Chờ duyệt", t: "y" }, { r: "Giảng đường A2-305", d: "10/05/2025 · 13:00–15:30", s: "Đã duyệt", t: "g" },
  { r: "Phòng máy C3-101", d: "02/05/2025 · 09:45–11:30", s: "Từ chối", t: "r" }, { r: "Phòng đọc TV-301", d: "28/04/2025 · 07:00–09:30", s: "Đã hủy", t: "x" },
];
function History({ toast }: { toast: (m: string) => void }) {
  const [tab, setTab] = useState("Tất cả"); const [q, setQ] = useState(""); const [modal, setModal] = useState(false);
  const l = hist.filter((h) => (tab === "Tất cả" || h.s === tab) && h.r.toLowerCase().includes(q.toLowerCase()));
  return (
    <div className="space-y-5"><h1 className="text-[32px] font-bold">Lịch sử đặt phòng</h1>
      <div className="flex flex-wrap gap-3"><div className="flex flex-wrap gap-1 rounded-xl bg-white p-1 shadow-sm">{["Tất cả", "Chờ duyệt", "Đã duyệt", "Từ chối", "Đã hủy"].map((x) => <button key={x} onClick={() => setTab(x)} className={`rounded-lg px-3 py-1.5 text-sm font-medium ${tab === x ? "bg-navy text-white" : "text-mute"}`}>{x}</button>)}</div><input className={`${inp} max-w-xs`} placeholder="Tìm phòng…" value={q} onChange={(e) => setQ(e.target.value)} /></div>
      <Card className="!p-0">{l.length === 0 ? <Empty t="Chưa có lượt đặt phòng" d="Các yêu cầu của bạn sẽ hiển thị tại đây." /> : l.map((h) => (
        <div key={h.r} className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 p-4 last:border-0"><div><b>{h.r}</b><p className="text-[13px] text-mute">{h.d}</p></div><div className="flex items-center gap-2"><Chip t={h.t}>{h.s}</Chip>{(h.s === "Chờ duyệt" || h.s === "Đã duyệt") && <><Btn v="s" className="!h-9">Đổi lịch</Btn><Btn v="g" className="!h-9 !text-red-600" onClick={() => setModal(true)}>Hủy</Btn></>}</div></div>))}</Card>
      {modal && <div className="fixed inset-0 z-50 grid place-items-center bg-ink/50 p-4"><Card className="w-full max-w-sm space-y-4"><h2 className="text-xl font-semibold">Hủy đặt phòng?</h2><p className="text-mute">Thao tác này không thể hoàn tác.</p><div className="flex justify-end gap-2"><Btn v="s" onClick={() => setModal(false)}>Giữ lại</Btn><Btn className="!bg-red-600" onClick={() => { setModal(false); toast("Đã hủy đặt phòng"); }}>Xác nhận hủy</Btn></div></Card></div>}
    </div>
  );
}

const notifs = [
  { g: "Hôm nay", t: "Đổi phòng", m: "Cơ sở dữ liệu chuyển từ A2-305 sang B1-204.", c: "b", u: true }, { g: "Hôm nay", t: "Kết quả duyệt", m: "Yêu cầu đặt Phòng TV-12 đã được duyệt.", c: "g", u: true },
  { g: "Hôm qua", t: "Nghỉ học", m: "Giải tích 2 nghỉ buổi thứ Năm do giảng viên bận.", c: "r", u: false }, { g: "Hôm qua", t: "Học bù", m: "Học bù Giải tích 2, Chủ nhật 07:00, B1-204.", c: "y", u: false },
];
const NRow = ({ n }: { n: (typeof notifs)[number] }) => <div className={`flex gap-3 rounded-xl p-3 ${n.u ? "bg-blue-50" : ""}`}><span className="mt-2 size-2 shrink-0 rounded-full" style={{ background: n.u ? "#3B82F6" : "transparent" }} /><div><Chip t={n.c}>{n.t}</Chip><p className="mt-1 text-sm">{n.m}</p></div></div>;
const Notif = () => (
  <div className="space-y-5"><h1 className="text-[32px] font-bold">Thông báo</h1>
    {["Hôm nay", "Hôm qua"].map((g) => <Card key={g}><h2 className="mb-2 font-semibold text-mute">{g}</h2>{notifs.filter((n) => n.g === g).map((n) => <NRow key={n.m} n={n} />)}</Card>)}</div>
);

function Issue({ toast }: { toast: (m: string) => void }) {
  const [d, setD] = useState("");
  return (
    <div className="space-y-5"><h1 className="text-[32px] font-bold">Báo cáo sự cố</h1>
      <div className="grid gap-6 lg:grid-cols-2">
        <Card className="space-y-4"><Field label="Phòng"><select className={inp}>{rooms.map((r) => <option key={r.id}>{r.n}</option>)}</select></Field><Field label="Loại sự cố"><select className={inp}><option>Thiết bị (máy chiếu, micro)</option><option>Điều hòa / điện</option><option>Vệ sinh</option><option>Khác</option></select></Field>
          <Field label="Mô tả" error={d.length > 0 && d.length < 10 ? "Mô tả ít nhất 10 ký tự" : ""}><textarea rows={4} className={`${inp} h-auto py-2`} value={d} onChange={(e) => setD(e.target.value)} /></Field>
          <div className="grid place-items-center gap-1 rounded-xl border-2 border-dashed border-slate-300 py-6 text-sm text-mute"><I n="img" s={28} />Kéo thả hoặc chọn ảnh minh họa</div>
          <Btn className="w-full" disabled={d.length < 10} onClick={() => { toast("Đã gửi báo cáo sự cố"); setD(""); }}>Gửi báo cáo</Btn></Card>
        <Card><h2 className="mb-3 text-2xl font-semibold">Báo cáo đã gửi</h2>{[["Máy chiếu A2-305 không lên hình", "Đang xử lý", "y"], ["Điều hòa B1-204 kêu to", "Đã xử lý", "g"], ["Ổ cắm C3-101 hỏng", "Đã tiếp nhận", "b"]].map(([a, b, c]) => <div key={a} className="flex items-center justify-between gap-2 border-b border-slate-100 py-3 last:border-0"><span className="text-sm">{a}</span><Chip t={c}>{b}</Chip></div>)}</Card>
      </div></div>
  );
}

function Profile({ go }: { go: (p: string) => void }) {
  const [on, setOn] = useState([true, true, false]);
  return (
    <div className="space-y-5"><h1 className="text-[32px] font-bold">Hồ sơ & Cài đặt</h1>
      <div className="grid gap-6 lg:grid-cols-2">
        <Card className="space-y-3"><div className="flex items-center gap-4"><div className="grid size-16 place-items-center rounded-full bg-navy text-xl font-bold text-white">MA</div><div><b className="text-lg">Nguyễn Minh Anh</b><p className="text-sm text-mute">MSSV 21021234</p></div></div>
          {[["Khoa", "Công nghệ thông tin"], ["Lớp", "K66-CNTT2"], ["Khóa", "K66"]].map(([a, b]) => <div key={a} className="flex justify-between border-t border-slate-100 pt-3 text-sm"><span className="text-mute">{a}</span><b>{b}</b></div>)}</Card>
        <Card className="space-y-3"><h2 className="font-semibold">Cài đặt thông báo</h2>{["Đổi phòng / nghỉ học", "Kết quả duyệt đặt phòng", "Nhắc lịch học"].map((l, i) => <div key={l} className="flex items-center justify-between text-sm">{l}<button role="switch" aria-checked={on[i]} onClick={() => setOn(on.map((v, j) => (j === i ? !v : v)))} className={`h-6 w-11 rounded-full p-0.5 transition ${on[i] ? "bg-navy" : "bg-slate-300"}`}><i className={`block size-5 rounded-full bg-white transition ${on[i] ? "translate-x-5" : ""}`} /></button></div>)}
          <Field label="Ngôn ngữ"><select className={inp}><option>Tiếng Việt</option><option>English</option></select></Field><Btn v="s" className="w-full !text-red-600" onClick={() => go("login")}><I n="out" s={18} />Đăng xuất</Btn></Card>
      </div>
      <Card><h2 className="mb-2 text-2xl font-semibold">Trợ giúp / Câu hỏi thường gặp</h2>{[["Làm sao để đặt phòng?", "Vào Tìm phòng, chọn phòng còn trống rồi làm theo 5 bước."], ["Bao lâu thì yêu cầu được duyệt?", "Thông thường trong vòng 24 giờ làm việc."], ["Tôi có thể hủy không?", "Có, trước giờ sử dụng ít nhất 2 giờ."]].map(([q, a]) => <details key={q} className="border-t border-slate-100 py-3"><summary className="cursor-pointer font-medium">{q}</summary><p className="mt-1 text-sm text-mute">{a}</p></details>)}</Card></div>
  );
}


/* ===== Cán bộ Đào tạo ===== */
const Toast = ({ t, m }: { t: "r" | "a" | "g"; m: string }) => (
  <div role="status" className={`flex items-center gap-2 rounded-xl px-4 py-3 text-sm font-medium text-white shadow-lg ${t === "r" ? "bg-red-600" : t === "a" ? "bg-amber text-ink !text-ink" : "bg-green-600"}`}><I n={t === "g" ? "check" : "warn"} s={16} />{m}</div>
);
const Spin = () => <span className="size-4 animate-spin rounded-full border-2 border-current/30 border-t-current" />;
const sRooms = [
  { n: "A2-305", b: "Tòa A2", c: 200, busy: [1] }, { n: "B1-204", b: "Tòa B1", c: 60, busy: [2] }, { n: "C3-101", b: "Tòa C3", c: 45, busy: [] },
  { n: "A1-402", b: "Tòa A1", c: 70, busy: [1, 2, 3] }, { n: "B2-110", b: "Tòa B2", c: 120, busy: [1, 2, 3] },
];
const sClasses = [
  { code: "INT2211-02", m: "Cơ sở dữ liệu", gv: "TS. Nguyễn Văn An", n: 60, slot: 1 }, { code: "MAT1101-05", m: "Giải tích 2", gv: "PGS. Trần Thị Mai", n: 90, slot: 2 },
  { code: "INT3304-01", m: "Mạng máy tính", gv: "ThS. Lê Hoàng Nam", n: 40, slot: 3 }, { code: "ENG1001-03", m: "Tiếng Anh 1", gv: "ThS. Phạm Thu Hà", n: 35, slot: 3 },
];
const caName = (n: number) => `Ca ${n} · Tiết ${n * 3 - 2}–${n * 3}`;
const sNav = [["import", "Import TKB", "down"], ["assign", "Xếp phòng", "grid"], ["approve", "Duyệt đổi phòng", "check"], ["export", "Xuất Excel", "list"]];

function ImportTKB() {
  const [closed, setClosed] = useState(false); const [busy, setBusy] = useState(false);
  const rows = [["INT2211-02", "Cơ sở dữ liệu", "A2-305", "Ca 1", ""], ["MAT1101-05", "Giải tích 2", "B1-204", "Ca 2", ""], ["INT3304-01", "Mạng máy tính", "C3-101", "Ca 9", "Ca học không hợp lệ (1–6)"], ["ENG1001-03", "", "B2-110", "Ca 3", "Thiếu tên môn học"], ["PHY1100-01", "Vật lý đại cương", "A2-999", "Ca 4", "Phòng không tồn tại"]];
  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3"><h1 className="text-[32px] font-bold">Import thời khóa biểu</h1>
        <div className="flex rounded-xl bg-white p-1 shadow-sm" aria-label="Xem trước hai phiên bản">{[["Trước hạn nạp", false], ["Sau hạn nạp", true]].map(([l, v]) => <button key={String(l)} onClick={() => setClosed(v as boolean)} className={`rounded-lg px-3 py-1.5 text-sm font-medium ${closed === v ? "bg-navy text-white" : "text-mute"}`}>{l as string}</button>)}</div></div>
      <div className={`flex items-center gap-3 rounded-xl p-4 text-sm ${closed ? "bg-slate-200 text-slate-700" : "bg-blue-50 text-navy"}`}><I n="clock" />Hạn chót nạp thời khóa biểu (First Closure Date): <b>30/06/2025</b> — {closed ? "đã hết hạn" : "còn 12 ngày"}</div>
      <Card className={`space-y-4 ${closed ? "opacity-60" : ""}`}>
        <div className={`grid place-items-center rounded-2xl border-2 border-dashed px-4 py-10 text-center ${closed ? "border-slate-300 bg-slate-100" : "border-brand/50 bg-blue-50/50"}`}>
          <span className={`grid size-14 place-items-center rounded-full ${closed ? "bg-slate-300 text-slate-600" : "bg-navy text-white"}`}><I n="down" s={26} c="rotate-180" /></span>
          <p className="mt-3 font-semibold">Kéo thả file Excel (.xlsx) vào đây</p><p className="text-sm text-mute">hoặc</p>
          <label className={`mt-1 ${closed ? "pointer-events-none" : ""}`}><input type="file" accept=".xlsx" disabled={closed} className="hidden" /><span className={`inline-flex h-11 items-center rounded-xl border px-4 text-sm font-semibold ${closed ? "border-slate-300 text-slate-400" : "cursor-pointer border-slate-300 bg-white text-navy hover:bg-slate-50"}`}>Chọn tệp từ máy</span></label>
        </div>
        <div className="flex flex-wrap items-center justify-between gap-3"><a href="#" className="flex items-center gap-2 text-sm font-semibold text-brand"><I n="down" s={16} />Tải file mẫu TKB.xlsx</a>
          <div className="group relative"><Btn disabled={closed} loading={busy} className={closed ? "!bg-slate-300 !text-slate-600 !opacity-100" : "!bg-brand hover:!bg-blue-600"} onClick={() => { setBusy(true); setTimeout(() => setBusy(false), 1500); }}><I n="down" s={18} c="rotate-180" />Tải lên TKB</Btn>
            {closed && <span className="pointer-events-none absolute bottom-full right-0 mb-2 whitespace-nowrap rounded-lg bg-ink px-3 py-2 text-[13px] text-white opacity-0 shadow-lg transition group-hover:opacity-100">Đã hết hạn nạp thời khóa biểu</span>}</div></div>
      </Card>
      <Card className={closed ? "opacity-60" : ""}><div className="mb-3 flex items-center justify-between"><h2 className="text-2xl font-semibold">Xem trước dữ liệu</h2><span className="flex gap-2"><Chip t="g">2 dòng hợp lệ</Chip><Chip t="r">3 dòng lỗi</Chip></span></div>
        <div className="overflow-x-auto"><table className="w-full min-w-[640px] text-left text-sm"><thead className="text-[13px] text-mute"><tr>{["#", "Mã lớp", "Môn", "Phòng", "Ca", "Lỗi"].map((h) => <th key={h} className="px-3 py-2 font-semibold">{h}</th>)}</tr></thead>
          <tbody>{rows.map((r, i) => <tr key={i} className={r[4] ? "bg-red-50" : ""}><td className="px-3 py-2.5">{i + 1}</td>{r.slice(0, 4).map((c, j) => <td key={j} className={`px-3 py-2.5 ${r[4].includes(["", "môn", "Phòng", "Ca"][j]) && r[4] && (j === 1 && !c || j === 2 && r[4].startsWith("Phòng") || j === 3 && r[4].startsWith("Ca")) ? "font-semibold text-red-700 underline decoration-red-400 decoration-wavy" : ""}`}>{c || "(trống)"}</td>)}<td className="px-3 py-2.5 text-red-700">{r[4] || <Chip t="g">Hợp lệ</Chip>}</td></tr>)}</tbody></table></div></Card>
      <Card className="!p-0"><h2 className="p-6 pb-3 text-2xl font-semibold">Lịch sử tải lên</h2>{[["TKB_HK2_2425_v2.xlsx", "20/05/2025 09:12", "412 lớp", "Thành công", "g"], ["TKB_HK2_2425_v1.xlsx", "15/05/2025 14:40", "398 lớp", "Có 6 lỗi", "y"], ["TKB_HK1_2425.xlsx", "10/12/2024 08:05", "405 lớp", "Thành công", "g"]].map((h) => <div key={h[0]} className="flex flex-wrap items-center justify-between gap-2 border-t border-slate-100 px-6 py-3 text-sm"><b>{h[0]}</b><span className="text-mute">{h[1]} · {h[2]}</span><Chip t={h[4]}>{h[3]}</Chip></div>)}</Card>
    </div>
  );
}

function Dd({ cls, value, onPick }: { cls: (typeof sClasses)[number]; value: string; onPick: (r: string) => void }) {
  const [open, setOpen] = useState(false);
  const free = sRooms.filter((r) => !r.busy.includes(cls.slot));
  return (
    <div className="relative">
      <button onClick={() => setOpen(!open)} className="flex h-11 w-52 items-center justify-between rounded-xl border border-slate-200 bg-white px-3 text-sm hover:border-brand">{value || <span className="text-mute">Chọn phòng…</span>}<span className="text-mute">▾</span></button>
      {open && <div className="absolute right-0 z-20 mt-1 w-72 rounded-xl bg-white p-1 shadow-xl ring-1 ring-slate-200">
        {free.length === 0 ? <div className="p-3 text-center"><Empty t="Không có phòng trống trong ca này" d="Thử chọn ca học khác." /></div> : free.map((r) => (
          <button key={r.n} onClick={() => { onPick(r.n); setOpen(false); }} className="flex w-full items-center justify-between rounded-lg px-3 py-2 text-left text-sm hover:bg-blue-50"><span><b>{r.n}</b><br /><span className="text-[13px] text-mute">{r.b}</span></span><span className={`flex items-center gap-1 text-[13px] ${r.c < cls.n ? "text-amber-700" : "text-mute"}`}><I n="users" s={14} />{r.c} chỗ</span></button>))}
      </div>}
    </div>
  );
}

function Assign() {
  const [tab, setTab] = useState("Lưới lịch"); const [pick, setPick] = useState<Record<string, string>>({}); const [saving, setSaving] = useState(false); const [toast, setToast] = useState<{ t: "r" | "a" | "g"; m: string } | null>(null);
  const flash = (t: "r" | "a" | "g", m: string) => { setToast({ t, m }); setTimeout(() => setToast(null), 3000); };
  const choose = (c: (typeof sClasses)[number], r: string) => { const room = sRooms.find((x) => x.n === r)!; if (room.c < c.n) { flash("a", `Phòng không đủ chỗ (Sĩ số: ${c.n} > Sức chứa: ${room.c})`); return; } setPick({ ...pick, [c.code]: r }); };
  const save = () => { if (saving) return; setSaving(true); setTimeout(() => { setSaving(false); flash("g", "Đã lưu phân phòng"); }, 1500); };
  const grid: Record<string, Record<number, { t: string; c?: boolean }>> = { "A2-305": { 1: { t: "INT2211-02" } }, "B1-204": { 2: { t: "MAT1101-05" } }, "C3-101": { 3: { t: "INT3304-01", c: true } }, "A1-402": { 1: { t: "PHY1100-01" }, 2: { t: "CHE1001-02" }, 3: { t: "ENG1001-03" } }, "B2-110": { 3: { t: "INT3304-01", c: true } } };
  return (
    <div className="space-y-5"><div className="flex flex-wrap items-center justify-between gap-3"><h1 className="text-[32px] font-bold">Xếp phòng</h1>
      <Btn disabled={saving} onClick={save} className={saving ? "!opacity-70" : ""} loading={saving}>{saving ? "Đang lưu…" : "Lưu phân phòng"}</Btn></div>
      <div className="flex w-fit rounded-xl bg-white p-1 shadow-sm">{["Lưới lịch", "Dropdown"].map((x) => <button key={x} onClick={() => setTab(x)} className={`rounded-lg px-4 py-1.5 text-sm font-medium ${tab === x ? "bg-navy text-white" : "text-mute"}`}>{x}</button>)}</div>
      {tab === "Lưới lịch" ? (
        <Card className="overflow-x-auto"><div className="mb-3 flex items-center justify-between text-sm"><b>Thứ Hai, 26/05/2025</b><span className="flex items-center gap-1 text-red-700"><I n="warn" s={16} />2 xung đột</span></div>
          <div className="grid min-w-[720px] grid-cols-[110px_repeat(6,1fr)] gap-2 text-[13px]"><div />{[1, 2, 3, 4, 5, 6].map((c) => <div key={c} className="rounded-lg bg-soft py-2 text-center font-semibold">Ca {c}<br /><span className="font-normal text-mute">Tiết {c * 3 - 2}–{c * 3}</span></div>)}
            {Object.entries(grid).map(([room, cells]) => [<div key={room} className="flex items-center font-semibold">{room}</div>, ...[1, 2, 3, 4, 5, 6].map((c) => { const x = cells[c]; return <div key={room + c} className={`min-h-14 rounded-lg p-2 ${x ? (x.c ? "bg-red-100 text-red-800 ring-2 ring-red-500" : "bg-blue-100 text-navy") : "border border-dashed border-slate-200"}`}>{x && <><b>{x.t}</b>{x.c && <span className="block">Trùng phòng</span>}</>}</div>; })])}
          </div></Card>
      ) : (
        <Card className="overflow-x-auto !pb-40"><table className="w-full min-w-[820px] text-left text-sm"><thead className="text-[13px] text-mute"><tr>{["Mã lớp", "Môn", "Giảng viên", "Sĩ số", "Ca học", "Phòng"].map((h) => <th key={h} className="px-3 py-2 font-semibold">{h}</th>)}</tr></thead>
          <tbody>{sClasses.map((c) => <tr key={c.code} className="border-t border-slate-100"><td className="px-3 py-3 font-semibold">{c.code}</td><td className="px-3">{c.m}</td><td className="px-3">{c.gv}</td><td className="px-3">{c.n}</td><td className="px-3">{caName(c.slot)}</td><td className="px-3"><Dd cls={c} value={pick[c.code]} onPick={(r) => choose(c, r)} /></td></tr>)}</tbody></table>
          <p className="mt-3 text-[13px] text-mute">Gợi ý: chỉ hiển thị phòng còn trống trong ca của lớp. Ca 3 hiện không còn phòng trống nào ngoài các phòng đã liệt kê.</p></Card>
      )}
      <Card className="space-y-2"><h2 className="font-semibold">Ví dụ phản hồi</h2><div className="flex flex-wrap gap-3"><Toast t="r" m="Phòng đã có lớp học" /><Toast t="a" m="Phòng không đủ chỗ (Sĩ số: 60 > Sức chứa: 45)" /></div></Card>
      {toast && <div className="fixed bottom-24 left-1/2 z-50 -translate-x-1/2 lg:bottom-8"><Toast {...toast} /></div>}
    </div>
  );
}

const reqs = [
  { id: 1, gv: "TS. Nguyễn Văn An", l: "INT2211-02", o: "A2-305", n: "B2-110", why: "Máy chiếu A2-305 hỏng, cần phòng có thiết bị.", d: "21/05/2025", s: "Chờ duyệt" },
  { id: 2, gv: "PGS. Trần Thị Mai", l: "MAT1101-05", o: "B1-204", n: "A2-305", why: "Sĩ số tăng lên 90 sinh viên.", d: "20/05/2025", s: "Chờ duyệt" },
  { id: 3, gv: "ThS. Lê Hoàng Nam", l: "INT3304-01", o: "C3-101", n: "C3-102", why: "Cần thêm máy tính thực hành.", d: "18/05/2025", s: "Đã duyệt" },
  { id: 4, gv: "ThS. Phạm Thu Hà", l: "ENG1001-03", o: "A1-402", n: "A2-305", why: "Điều hòa phòng cũ không hoạt động.", d: "15/05/2025", s: "Từ chối" },
];
function Approve() {
  const [list, setList] = useState(reqs); const [tab, setTab] = useState("Tất cả"); const [busy, setBusy] = useState<string>(""); const [open, setOpen] = useState<(typeof reqs)[number] | null>(null);
  const act = (id: number, a: "ok" | "no") => { if (busy) return; setBusy(id + a); setTimeout(() => { setList((l) => l.map((r) => (r.id === id ? { ...r, s: a === "ok" ? "Đã duyệt" : "Từ chối" } : r))); setBusy(""); setOpen(null); }, 1200); };
  const tone2: Record<string, string> = { "Chờ duyệt": "y", "Đã duyệt": "g", "Từ chối": "r" };
  const rows = list.filter((r) => tab === "Tất cả" || r.s === tab);
  const Actions = ({ r }: { r: (typeof reqs)[number] }) => r.s !== "Chờ duyệt" ? null : (<div className="flex gap-2">
    <button disabled={!!busy} onClick={(e) => { e.stopPropagation(); act(r.id, "ok"); }} className="inline-flex h-9 items-center gap-1.5 rounded-lg bg-green-600 px-3 text-sm font-semibold text-white hover:bg-green-700 disabled:opacity-60">{busy === r.id + "ok" ? <Spin /> : <I n="check" s={16} />}Duyệt</button>
    <button disabled={!!busy} onClick={(e) => { e.stopPropagation(); act(r.id, "no"); }} className="inline-flex h-9 items-center gap-1.5 rounded-lg border border-red-300 px-3 text-sm font-semibold text-red-700 hover:bg-red-50 disabled:opacity-60">{busy === r.id + "no" ? <Spin /> : <I n="x" s={16} />}Từ chối</button></div>);
  return (
    <div className="space-y-5"><h1 className="text-[32px] font-bold">Duyệt đổi phòng</h1>
      <div className="flex w-fit flex-wrap gap-1 rounded-xl bg-white p-1 shadow-sm">{["Tất cả", "Chờ duyệt", "Đã duyệt", "Từ chối"].map((x) => <button key={x} onClick={() => setTab(x)} className={`rounded-lg px-3 py-1.5 text-sm font-medium ${tab === x ? "bg-navy text-white" : "text-mute"}`}>{x}</button>)}</div>
      <Card className="overflow-x-auto !p-2">{rows.length === 0 ? <Empty t="Không có yêu cầu nào" d="Các yêu cầu đổi phòng sẽ hiển thị tại đây." /> : <table className="w-full min-w-[980px] text-left text-sm"><thead className="text-[13px] text-mute"><tr>{["Giảng viên", "Lớp", "Phòng cũ", "Phòng đề nghị", "Lý do", "Ngày gửi", "Trạng thái", ""].map((h) => <th key={h} className="px-3 py-2 font-semibold">{h}</th>)}</tr></thead>
        <tbody>{rows.map((r) => <tr key={r.id} onClick={() => setOpen(r)} className="cursor-pointer border-t border-slate-100 hover:bg-blue-50/50"><td className="px-3 py-3 font-semibold">{r.gv}</td><td className="px-3">{r.l}</td><td className="px-3">{r.o}</td><td className="px-3 font-semibold text-navy">{r.n}</td><td className="max-w-[220px] truncate px-3 text-mute">{r.why}</td><td className="px-3">{r.d}</td><td className="px-3"><Chip t={tone2[r.s]}>{r.s}</Chip></td><td className="px-3"><Actions r={r} /></td></tr>)}</tbody></table>}</Card>
      {open && <div className="fixed inset-0 z-50 flex justify-end bg-ink/40" onClick={() => setOpen(null)}><aside onClick={(e) => e.stopPropagation()} className="h-full w-full max-w-md space-y-4 overflow-y-auto bg-white p-6 shadow-2xl">
        <div className="flex items-center justify-between"><h2 className="text-2xl font-semibold">Chi tiết yêu cầu</h2><button aria-label="Đóng" onClick={() => setOpen(null)} className="grid size-10 place-items-center rounded-xl hover:bg-soft"><I n="x" /></button></div>
        <Chip t={tone2[open.s]}>{open.s}</Chip>
        <dl className="space-y-3 text-sm">{[["Giảng viên", open.gv], ["Lớp học phần", open.l], ["Phòng cũ", open.o], ["Phòng đề nghị", open.n], ["Ngày gửi", open.d]].map(([a, b]) => <div key={a} className="flex justify-between border-b border-slate-100 pb-2"><dt className="text-mute">{a}</dt><dd className="font-semibold">{b}</dd></div>)}</dl>
        <div><p className="text-sm font-semibold">Lý do</p><p className="mt-1 rounded-xl bg-soft p-3 text-sm text-mute">{open.why}</p></div>
        <Actions r={open} /></aside></div>}
    </div>
  );
}

function Export() {
  const [busy, setBusy] = useState(false); const [done, setDone] = useState(false); const [fmt, setFmt] = useState(".xlsx");
  return (
    <div className="space-y-5"><h1 className="text-[32px] font-bold">Xuất Excel</h1>
      <Card className="grid gap-4 md:grid-cols-3"><Field label="Học kỳ"><select className={inp}><option>Học kỳ 2 · 2024–2025</option><option>Học kỳ 1 · 2024–2025</option></select></Field><Field label="Tòa nhà"><select className={inp}><option>Tất cả</option><option>Tòa A2</option><option>Tòa B1</option></select></Field><Field label="Khoa"><select className={inp}><option>Tất cả</option><option>Công nghệ thông tin</option><option>Toán – Cơ – Tin học</option></select></Field>
        <div className="md:col-span-3"><p className="mb-2 text-sm font-semibold">Định dạng</p><div className="flex gap-3">{[".xlsx", ".csv"].map((f) => <button key={f} onClick={() => setFmt(f)} className={`h-12 rounded-xl border-2 px-6 text-sm font-semibold ${fmt === f ? "border-navy bg-blue-50 text-navy" : "border-slate-200"}`}>{f === ".xlsx" ? "Excel (.xlsx)" : "CSV (.csv)"}</button>)}</div></div>
        <div className="flex items-center gap-3 md:col-span-3"><Btn loading={busy} onClick={() => { setBusy(true); setDone(false); setTimeout(() => { setBusy(false); setDone(true); }, 1500); }}><I n="down" s={18} />{busy ? "Đang xuất…" : "Xuất Excel"}</Btn>{done && <Chip t="g"><I n="check" s={14} />Đã xuất xong</Chip>}</div></Card>
      <Card className="!p-0"><h2 className="p-6 pb-3 text-2xl font-semibold">Lịch sử xuất file</h2>{[["TKB_HK2_2425_TatCa.xlsx", "22/05/2025 10:30", "Học kỳ 2 · Tất cả tòa"], ["TKB_HK2_2425_CNTT.xlsx", "18/05/2025 15:12", "Khoa CNTT"], ["PhongHoc_HK1_2425.csv", "05/12/2024 09:00", "Học kỳ 1 · Tòa A2"]].map((h) => <div key={h[0]} className="flex flex-wrap items-center justify-between gap-2 border-t border-slate-100 px-6 py-3 text-sm"><b>{h[0]}</b><span className="text-mute">{h[1]} · {h[2]}</span><Btn v="g" className="!h-9"><I n="down" s={16} />Tải lại</Btn></div>)}</Card></div>
  );
}

function Staff({ go }: { go: (p: string) => void }) {
  const [p, setP] = useState("import");
  const body = p === "import" ? <ImportTKB /> : p === "assign" ? <Assign /> : p === "approve" ? <Approve /> : <Export />;
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50/60 to-slate-100 lg:pl-64">
      <aside className="fixed inset-y-0 left-0 hidden w-64 flex-col bg-white p-4 shadow-sm lg:flex">
        <div className="mb-3 flex items-center gap-3 px-2"><div className="grid size-10 place-items-center rounded-xl bg-navy text-white"><I n="grad" /></div><b className="text-navy">UniRoom</b></div>
        <span className="mx-2 mb-6 w-fit rounded-full bg-amber/20 px-3 py-1 text-[13px] font-semibold text-amber-900">Cán bộ Đào tạo</span>
        <nav className="flex-1 space-y-1">{sNav.map(([k, l, i]) => <button key={k} onClick={() => setP(k)} className={`flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition ${p === k ? "bg-navy text-white" : "text-mute hover:bg-soft"}`}><I n={i} s={18} /><span className="text-left leading-tight">{l}<span className={`block text-xs font-normal ${p === k ? "text-blue-100" : "text-slate-600"}`}>{EN[l]}</span></span></button>)}</nav>
        <div className="flex items-center gap-3 rounded-xl p-2"><span className="grid size-10 place-items-center rounded-full bg-amber font-bold">LT</span><span className="flex-1 text-sm"><b className="block">Lê Thu Trang</b><span className="text-[13px] text-mute">Phòng Đào tạo</span></span><button aria-label="Đăng xuất" onClick={() => go("login")} className="text-mute hover:text-red-600"><I n="out" s={18} /></button></div>
      </aside>
      <header className="sticky top-0 z-20 flex items-center justify-between bg-white/90 px-4 py-3 backdrop-blur lg:px-8"><span className="rounded-full bg-amber/20 px-3 py-1 text-[13px] font-semibold text-amber-900">Cán bộ Đào tạo</span><button onClick={() => go("login")} className="text-sm font-medium text-mute lg:hidden">Đăng xuất</button></header>
      <main className="mx-auto max-w-[1180px] p-4 pb-28 lg:p-8">{body}</main>
      <nav className="fixed inset-x-0 bottom-0 z-30 grid grid-cols-4 border-t border-slate-200 bg-white lg:hidden">{sNav.map(([k, l, i]) => <button key={k} onClick={() => setP(k)} className={`flex flex-col items-center gap-0.5 py-2 text-xs font-medium ${p === k ? "text-navy" : "text-mute"}`}><I n={i} s={22} />{l}</button>)}</nav>
    </div>
  );
}

const EN: Record<string, string> = {"Trang chủ": "Home", "Lịch học": "Schedule", "Tìm phòng": "Find rooms", "Đặt phòng": "Booking", "Lịch sử": "History", "Thông báo": "Notifications", "Báo sự cố": "Report issue", "Cá nhân": "Profile", "Import TKB": "Import timetable", "Xếp phòng": "Room assignment", "Duyệt đổi phòng": "Approve changes", "Xuất Excel": "Export"};
const nav = [["home", "Trang chủ", "home"], ["schedule", "Lịch học", "cal"], ["search", "Tìm phòng", "search"], ["book", "Đặt phòng", "plus"], ["history", "Lịch sử", "hist"], ["notif", "Thông báo", "bell"], ["issue", "Báo sự cố", "warn"], ["profile", "Cá nhân", "user"]];
const tabs = ["home", "schedule", "search", "book", "profile"];

export default function App() {
  const [page, setPage] = useState("login"); const [room, setRoom] = useState<R>(rooms[0]); const [toast, setToast] = useState("");
  const go = (p: string, r?: R) => { if (r) setRoom(r); setPage(p); window.scrollTo(0, 0); };
  const show = (m: string) => { setToast(m); setTimeout(() => setToast(""), 2500); };
  if (page === "login") return <Login go={go} />;
  if (page === "staff") return <Staff go={go} />;
  const active = page === "detail" ? "search" : page;
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50/60 to-slate-100 lg:pl-64">
      <aside className="fixed inset-y-0 left-0 hidden w-64 flex-col bg-white p-4 shadow-sm lg:flex">
        <div className="mb-6 flex items-center gap-3 px-2"><div className="grid size-10 place-items-center rounded-xl bg-navy text-white"><I n="grad" /></div><b className="text-navy">UniRoom</b></div>
        <nav className="flex-1 space-y-1">{nav.map(([k, l, i]) => <button key={k} onClick={() => go(k)} className={`flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition ${active === k ? "bg-navy text-white" : "text-mute hover:bg-soft"}`}><I n={i} s={18} /><span className="text-left leading-tight">{l}<span className={`block text-xs font-normal ${active === k ? "text-blue-100" : "text-slate-600"}`}>{EN[l]}</span></span></button>)}</nav>
        <button onClick={() => go("profile")} className="flex items-center gap-3 rounded-xl p-2 text-left hover:bg-soft"><span className="grid size-10 place-items-center rounded-full bg-amber font-bold text-ink">MA</span><span className="text-sm"><b className="block">Minh Anh</b><span className="text-[13px] text-mute">21021234</span></span></button>
      </aside>
      <header className="sticky top-0 z-20 flex items-center gap-3 bg-white/90 px-4 py-3 backdrop-blur lg:px-8">
        <div className="relative max-w-md flex-1"><span className="absolute left-3 top-3 text-mute"><I n="search" s={18} /></span><input className={`${inp} pl-10`} placeholder="Tìm phòng, lớp học phần…" /></div>
        <button aria-label="Thông báo" onClick={() => go("notif")} className="relative ml-auto grid size-11 place-items-center rounded-xl hover:bg-soft"><I n="bell" /><i className="absolute right-2.5 top-2.5 size-2.5 rounded-full bg-red-500" /></button>
        <span className="grid size-10 place-items-center rounded-full bg-amber font-bold">MA</span>
      </header>
      <main className="mx-auto max-w-[1180px] p-4 pb-28 lg:p-8">
        {page === "home" && <Home go={go} />}{page === "schedule" && <Schedule />}{page === "search" && <Search go={go} />}{page === "detail" && <Detail r={room} go={go} />}
        {page === "book" && <Book r={room} go={go} toast={show} />}{page === "history" && <History toast={show} />}{page === "notif" && <Notif />}{page === "issue" && <Issue toast={show} />}{page === "profile" && <Profile go={go} />}
      </main>
      <nav className="fixed inset-x-0 bottom-0 z-30 grid grid-cols-5 border-t border-slate-200 bg-white lg:hidden">{tabs.map((k) => { const [, l, i] = nav.find((n) => n[0] === k)!; return <button key={k} onClick={() => go(k)} className={`flex flex-col items-center gap-0.5 py-2 text-xs font-medium ${active === k ? "text-navy" : "text-mute"}`}><I n={i} s={22} />{l}</button>; })}</nav>
      {toast && <div role="status" className="fixed bottom-24 left-1/2 z-50 flex -translate-x-1/2 items-center gap-2 rounded-xl bg-ink px-4 py-3 text-sm text-white shadow-lg lg:bottom-8"><I n="check" s={16} c="text-green-400" />{toast}</div>}
    </div>
  );
}
